# backend/users/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib import messages
# Import các model từ đúng ứng dụng của chúng
from tournaments.models import Team, Player, Tournament, Player, TeamAchievement, VoteRecord, TournamentStaff, PlayerTransfer, ScoutingList 
from .forms import CustomUserChangeForm, AvatarUpdateForm, NotificationPreferencesForm, ProfileSetupForm, ProfileUpdateForm, UnifiedProfessionalForm
from .models import Profile, Role, CoachProfile, StadiumProfile, CoachReview, StadiumReview
from sponsors.models import SponsorProfile
from django.contrib.auth.models import User
# Thêm import đánh giá công việc
from organizations.models import ProfessionalReview, JobApplication, JobPosting
from django.db.models import Avg, Count
# Thêm các import cần thiết ở đầu file
from django.db import transaction
from tournaments.forms import PlayerCreationForm
from tournaments.models import Player

@login_required
def dashboard(request):
    profile, created = Profile.objects.get_or_create(user=request.user)
    avatar_form_has_errors = False

    user_form = CustomUserChangeForm(instance=request.user)
    password_form = PasswordChangeForm(request.user)
    avatar_form = AvatarUpdateForm(instance=profile)
    preferences_form = NotificationPreferencesForm(instance=profile)
    profile_form = ProfileUpdateForm(instance=profile)

    # === BẮT ĐẦU LOGIC MỚI CHO HỒ SƠ CẦU THỦ ===
    player_profile = None
    player_profile_form = None
    can_edit_player_profile = False
    remaining_edits = 0

    try:
        player_profile = request.user.player_profile
    except Player.DoesNotExist:
        pass

    if player_profile:
        # Sửa lại logic: khóa khi có 3 phiếu bầu hoặc 3 lần sửa
        can_edit_player_profile = player_profile.votes < 3 and player_profile.edit_count < 3
        remaining_edits = 3 - player_profile.edit_count
    # === KẾT THÚC LOGIC MỚI ===

    if request.method == 'POST':
        if 'update_profile' in request.POST:
            user_form = CustomUserChangeForm(request.POST, instance=request.user)
            if user_form.is_valid():
                user_form.save()
                messages.success(request, 'Thông tin của bạn đã được cập nhật thành công!')
                return redirect('dashboard')
            else:
                messages.error(request, 'Cập nhật thông tin thất bại. Vui lòng kiểm tra lại.')

        elif 'change_password' in request.POST:
            password_form = PasswordChangeForm(request.user, request.POST)
            if password_form.is_valid():
                user = password_form.save()
                update_session_auth_hash(request, user)
                messages.success(request, 'Mật khẩu của bạn đã được thay đổi thành công!')
                return redirect('dashboard')

        elif 'update_avatar' in request.POST:
            avatar_form = AvatarUpdateForm(request.POST, request.FILES, instance=profile)
            if avatar_form.is_valid():
                avatar_form.save()
                messages.success(request, 'Ảnh đại diện đã được cập nhật!')
                return redirect('dashboard')
            else:
                avatar_form_has_errors = True
                messages.error(request, 'Cập nhật ảnh đại diện thất bại. Vui lòng xem chi tiết trong popup.')

        elif 'update_preferences' in request.POST:
            preferences_form = NotificationPreferencesForm(request.POST, instance=profile)
            if preferences_form.is_valid():
                preferences_form.save()
                messages.success(request, 'Đã cập nhật cài đặt thông báo của bạn!')
                return redirect(request.path_info + '?tab=notifications')

        elif 'update_public_profile' in request.POST:
            # Sửa lại dòng này để có request.FILES
            profile_form = ProfileUpdateForm(request.POST, request.FILES, instance=profile)
            if profile_form.is_valid():
                # === THÊM LOGIC ĐẾM VÀO ĐÂY TRƯỚC KHI LƯU ===
                if 'roles' in profile_form.changed_data:
                    # Form đã valid, nghĩa là người dùng còn lượt đổi
                    # nên ta chỉ cần tăng biến đếm
                    if profile.role_change_count < 3:
                        profile.role_change_count += 1
                        # Không cần save ở đây, form.save() bên dưới sẽ lưu cả thay đổi này
                
                profile_form.save()
                messages.success(request, 'Đã cập nhật hồ sơ công khai của bạn!')
                return redirect(request.path_info + '?tab=public-profile')

        # === BẮT ĐẦU KHỐI XỬ LÝ LƯU HỒ SƠ CẦU THỦ ===
        elif 'update_player_profile' in request.POST and player_profile and can_edit_player_profile:
            # Dùng lại PlayerCreationForm để chỉnh sửa
            player_profile_form = PlayerCreationForm(request.POST, request.FILES, instance=player_profile)
            if player_profile_form.is_valid():
                player_to_save = player_profile_form.save(commit=False)
                player_to_save.edit_count += 1 # Tăng số lần chỉnh sửa
                player_to_save.save()

                messages.success(request, f'Đã cập nhật hồ sơ cầu thủ. Bạn còn {3 - player_to_save.edit_count} lần sửa đổi.')
                return redirect(request.path_info + '?tab=player-profile')
            else:
                messages.error(request, 'Cập nhật hồ sơ cầu thủ thất bại. Vui lòng kiểm tra lại các trường thông tin.')
        # === KẾT THÚC KHỐI XỬ LÝ ===

    # Khởi tạo form cho GET request
    if player_profile and not player_profile_form:
        player_profile_form = PlayerCreationForm(instance=player_profile)

    managed_teams = Team.objects.filter(captain=request.user)
    # === THÊM TRUY VẤN NÀY VÀO ===
    scouting_list = ScoutingList.objects.filter(
        team__in=managed_teams
    ).select_related('player', 'player__team').order_by('team__name', '-added_at')

    followed_tournaments = request.user.followed_tournaments.all().exclude(status='FINISHED').order_by('start_date')
    managed_tournaments = Tournament.objects.filter(staff__user=request.user, staff__role__id='TOURNAMENT_MANAGER').distinct().order_by('-start_date')
    media_tournaments = Tournament.objects.filter(staff__user=request.user, staff__role__id__in=['MEDIA', 'PHOTOGRAPHER']).distinct().order_by('-start_date')

    # === BẮT ĐẦU THÊM MỚI TẠI ĐÂY ===
    # 2. Lấy danh sách lời mời
    incoming_transfers = PlayerTransfer.objects.filter(
        current_team__in=managed_teams, status='PENDING'
    ).select_related('inviting_team', 'player')

    outgoing_transfers = PlayerTransfer.objects.filter(
        inviting_team__in=managed_teams
    ).select_related('current_team', 'player').order_by('-created_at')

    user_role_ids = set(profile.roles.values_list('id', flat=True))

    # === BẮT ĐẦU LOGIC MỚI: TÍNH SỐ LẦN ĐỔI VAI TRÒ CÒN LẠI ===
    remaining_role_changes = 3 - profile.role_change_count
    if remaining_role_changes < 0:
        remaining_role_changes = 0
    
    # === TÍNH SỐ LƯỢNG PENDING CHO DASHBOARD LINKS ===
    pending_recruitments_count = 0
    pending_applications_count = 0
    
    # Đếm pending recruitments cho HLV
    if hasattr(request.user, 'coach_profile'):
        from tournaments.models import CoachRecruitment
        pending_recruitments_count = CoachRecruitment.objects.filter(
            coach=request.user.coach_profile,
            status=CoachRecruitment.Status.PENDING
        ).count()
    
    # Đếm pending applications cho Sân bóng
    if hasattr(request.user, 'stadium_profile'):
        pending_applications_count = JobApplication.objects.filter(
            job__stadium=request.user.stadium_profile,
            status=JobApplication.Status.PENDING
        ).count()

    context = {
        'user_form': user_form,
        'password_form': password_form,
        'avatar_form': avatar_form,
        'preferences_form': preferences_form,
        'profile_form': profile_form,
        'managed_teams': managed_teams,
        'followed_tournaments': followed_tournaments,
        'avatar_form_has_errors': avatar_form_has_errors,
        'managed_tournaments': managed_tournaments,
        'media_tournaments': media_tournaments,
        'player_profile': player_profile,
        # === GỬI CÁC BIẾN MỚI RA TEMPLATE ===
        'player_profile_form': player_profile_form,
        'can_edit_player_profile': can_edit_player_profile,
        'remaining_edits': remaining_edits,
        # 3. Thêm vào context để gửi ra template
        'incoming_transfers': incoming_transfers,
        'outgoing_transfers': outgoing_transfers,
        'scouting_list': scouting_list,
        'user_role_ids': user_role_ids,
        'remaining_role_changes': remaining_role_changes,
        # Thêm thông tin cho dashboard links
        'pending_recruitments_count': pending_recruitments_count,
        'pending_applications_count': pending_applications_count,
    }
    return render(request, 'users/dashboard.html', context)

@login_required
def select_roles_view(request):
    profile = request.user.profile
    
    if profile.has_selected_roles:
        return redirect('dashboard')

    if request.method == 'POST':
        selected_role_ids = request.POST.getlist('roles')

        if len(selected_role_ids) == 0:
            messages.error(request, "Bạn phải chọn ít nhất một vai trò.")
        elif len(selected_role_ids) > 2:
            messages.error(request, "Bạn chỉ được chọn tối đa 2 vai trò.")
        else:
            # Bắt đầu một transaction để đảm bảo tất cả các thao tác cùng thành công hoặc thất bại
            with transaction.atomic():
                profile.roles.clear()
                for role_id in selected_role_ids:
                    try:
                        role = Role.objects.get(pk=role_id)
                        profile.roles.add(role)
                    except Role.DoesNotExist:
                        messages.error(request, f"Vai trò không hợp lệ: {role_id}")
                        return render(request, 'users/select_roles.html', {'roles': Role.objects.all()})
                
                profile.has_selected_roles = True
                profile.save()

                # === LOGIC MỚI: TỰ ĐỘNG TẠO HỒ SƠ CẦU THỦ & THƯỞNG PHIẾU (PHIÊN BẢN 2.0) ===
                if 'PLAYER' in selected_role_ids:
                    # Tạo hồ sơ cầu thủ tự do (team=None) và cộng thưởng 1 phiếu bầu
                    Player.objects.get_or_create(
                        user=request.user,
                        defaults={
                            'team': None, # Cầu thủ tự do, không thuộc đội nào
                            'full_name': request.user.get_full_name() or request.user.username,
                            'jersey_number': 99,
                            'position': 'MF',
                            'votes': 1  # Cộng thưởng trực tiếp
                        }
                    )
                    messages.success(request, "Chào mừng bạn! Một hồ sơ cầu thủ tự do đã được tạo và bạn được tặng 1 phiếu bầu.")

            # === Logic chuyển hướng sau khi xử lý ===
            if 'ORGANIZER' in selected_role_ids:
                messages.info(request, "Để bắt đầu, vui lòng hoàn tất thông tin đăng ký Ban tổ chức của bạn.")
                return redirect('organizations:create')
            
            messages.success(request, "Đã lưu vai trò! Vui lòng hoàn tất hồ sơ của bạn để mọi người có thể tìm thấy bạn.")
            return redirect('profile_setup') 

    roles = Role.objects.all().order_by('order')
    return render(request, 'users/select_roles.html', {'roles': roles})    

@login_required
def profile_setup_view(request):
    profile = request.user.profile
    
    if profile.is_profile_complete:
        return redirect('home')

    action = request.GET.get('action')
    if action == 'skip':
        profile.is_profile_complete = True
        profile.save()
        messages.info(request, "Bạn có thể cập nhật hồ sơ của mình sau tại Khu vực cá nhân.")
        return redirect('home')
    elif action == 'create_team':
        profile.is_profile_complete = True
        profile.save()
        messages.info(request, "Hồ sơ đã được đánh dấu hoàn tất! Bây giờ hãy tạo đội bóng đầu tiên của bạn.")
        return redirect('create_standalone_team')

    if request.method == 'POST':
        form = ProfileSetupForm(request.POST, instance=profile, user=request.user)
        if form.is_valid():
            form.save()
            profile.is_profile_complete = True
            profile.save()
            
            if profile.roles.filter(id='PLAYER').exists():
                 messages.success(request, "Cảm ơn bạn đã cập nhật hồ sơ! Hãy bắt đầu bằng việc tạo đội bóng của bạn.")
                 return redirect('create_standalone_team')
            
            messages.success(request, "Cảm ơn bạn đã cập nhật hồ sơ!")
            return redirect('home')
    else:
        form = ProfileSetupForm(instance=profile)

    is_player = profile.roles.filter(id='PLAYER').exists()
    user_role_ids = set(profile.roles.values_list('id', flat=True)) # Lấy danh sách ID vai trò

    context = {
        'form': form,
        'is_player': is_player,
        'user_role_ids': user_role_ids, # Gửi danh sách này ra template
    }
    return render(request, 'users/profile_setup.html', context)
    

# === Backen hs ca nhan cong viec ===
def public_profile_view(request, username):
    try:
        profile_user = User.objects.select_related('profile').get(username=username)
    except User.DoesNotExist:
        # Thử tìm bằng email nếu username không tìm thấy
        try:
            profile_user = User.objects.select_related('profile').get(email=username)
        except User.DoesNotExist:
            # Hiển thị trang 404 tùy chỉnh
            return render(request, 'users/user_not_found.html', {
                'username': username
            }, status=404)
    profile = profile_user.profile

    # Lấy thành tích (giữ nguyên)
    player_profiles = Player.objects.filter(user=profile_user)
    team_ids = player_profiles.values_list('team_id', flat=True)
    achievements = TeamAchievement.objects.filter(team_id__in=team_ids).select_related('tournament', 'team').order_by('-achieved_at')

    # === BẮT ĐẦU NÂNG CẤP: LẤY DỮ LIỆU PORTFOLIO ===
    
    # Lấy tất cả các vai trò chuyên môn của người dùng trong các giải đấu
    staff_assignments = TournamentStaff.objects.filter(
        user=profile_user
    ).select_related('tournament', 'role').order_by('-tournament__start_date')

    # Phân loại các công việc đã làm vào từng danh sách riêng
    commentator_gigs = []
    media_gigs = []

    for assignment in staff_assignments:
        # Nếu là Bình luận viên, tìm các trận đấu họ đã bình luận trong giải đó
        if assignment.role.id == 'COMMENTATOR':
            matches_commentated = Match.objects.filter(
                tournament=assignment.tournament, 
                commentator__icontains=profile_user.get_full_name() or profile_user.username
            ).exclude(livestream_url__isnull=True).exclude(livestream_url__exact='')
            
            if matches_commentated.exists():
                commentator_gigs.append({
                    'tournament': assignment.tournament,
                    'matches': matches_commentated
                })

        # Nếu là Media hoặc Nhiếp ảnh gia
        elif assignment.role.id in ['MEDIA', 'PHOTOGRAPHER']:
            media_gigs.append({
                'tournament': assignment.tournament,
                'role_name': assignment.role.name
            })

    # === BẮT ĐẦU NÂNG CẤP: LẤY DỮ LIỆU ĐÁNH GIÁ ===
    reviews = ProfessionalReview.objects.filter(reviewee=profile_user).select_related('reviewer', 'job_application__job')
    
    # Tính toán rating trung bình
    average_rating = reviews.aggregate(avg=Avg('rating'))['avg']
    if average_rating:
        average_rating = round(average_rating, 1) # Làm tròn 1 chữ số thập phân    

    # === THÊM: LẤY THÔNG TIN COACH ===
    coach_profile = None
    coach_reviews = []
    coach_avg_rating = 0
    try:
        coach_profile = profile_user.coach_profile
        coach_reviews = CoachReview.objects.filter(
            coach_profile=coach_profile,
            is_approved=True
        ).select_related('reviewer', 'team', 'tournament').order_by('-created_at')
        coach_avg = coach_reviews.aggregate(avg=Avg('rating'))['avg']
        if coach_avg:
            coach_avg_rating = round(coach_avg, 1)
    except CoachProfile.DoesNotExist:
        pass

    # === THÊM: LẤY THÔNG TIN STADIUM ===
    stadium_profile = None
    stadium_reviews = []
    stadium_avg_rating = 0
    try:
        stadium_profile = profile_user.stadium_profile
        stadium_reviews = StadiumReview.objects.filter(
            stadium_profile=stadium_profile,
            is_approved=True
        ).select_related('reviewer', 'team', 'tournament').order_by('-created_at')
        stadium_avg = stadium_reviews.aggregate(avg=Avg('rating'))['avg']
        if stadium_avg:
            stadium_avg_rating = round(stadium_avg, 1)
    except StadiumProfile.DoesNotExist:
        pass

    # === THÊM: LẤY LỊCH SỬ CÔNG VIỆC ===
    job_applications = JobApplication.objects.filter(
        applicant=profile_user,
        status='APPROVED'
    ).select_related('job', 'job__tournament', 'job__stadium').order_by('-applied_at')[:10]

    # === THÊM: TÍNH AVAILABILITY ===
    is_available = True
    hourly_rate = None
    user_roles_queryset = profile.roles.all()
    
    # Tạo dictionary để template dễ check
    user_roles = {
        'COACH': user_roles_queryset.filter(id='COACH').exists(),
        'STADIUM': user_roles_queryset.filter(id='STADIUM').exists(),
        'SPONSOR': user_roles_queryset.filter(id='SPONSOR').exists(),
        'COMMENTATOR': user_roles_queryset.filter(id='COMMENTATOR').exists(),
        'MEDIA': user_roles_queryset.filter(id='MEDIA').exists(),
        'PHOTOGRAPHER': user_roles_queryset.filter(id='PHOTOGRAPHER').exists(),
        'REFEREE': user_roles_queryset.filter(id='REFEREE').exists(),
    }
    
    if user_roles['COACH'] and coach_profile:
        is_available = coach_profile.is_available
        hourly_rate = getattr(coach_profile, 'hourly_rate', None)
    elif user_roles['STADIUM']:
        is_available = True
    else:
        hourly_rate = getattr(profile, 'hourly_rate', None)

    # === THÊM: LẤY THÔNG TIN NHÀ TÀI TRỢ ===
    sponsor_profile = None
    sponsor_testimonials = []
    sponsor_sponsorships = []
    sponsor_avg_rating = 0
    try:
        from sponsors.models import SponsorProfile, Testimonial
        sponsor_profile = profile_user.sponsor_profile
        
        # Lấy testimonials
        sponsor_testimonials = Testimonial.objects.filter(
            sponsor_profile=sponsor_profile,
            is_approved=True
        ).select_related('author', 'tournament').order_by('-created_at')
        sponsor_avg = sponsor_testimonials.aggregate(avg=Avg('rating'))['avg']
        if sponsor_avg:
            sponsor_avg_rating = round(sponsor_avg, 1)
        
        # Lấy danh sách giải đấu đã tài trợ
        sponsor_sponsorships = profile_user.sponsorships.filter(is_active=True).select_related('tournament').order_by('-tournament__start_date')
    except:
        pass

    context = {
        'profile_user': profile_user,
        'profile': profile,
        'achievements': achievements,
        'commentator_gigs': commentator_gigs,
        'media_gigs': media_gigs,
        'reviews': reviews,
        'average_rating': average_rating,
        'reviews_count': reviews.count(),
        # Coach data
        'coach_profile': coach_profile,
        'coach_reviews': coach_reviews,
        'coach_avg_rating': coach_avg_rating,
        # Stadium data
        'stadium_profile': stadium_profile,
        'stadium_reviews': stadium_reviews,
        'stadium_avg_rating': stadium_avg_rating,
        # Sponsor data
        'sponsor_profile': sponsor_profile,
        'sponsor_testimonials': sponsor_testimonials,
        'sponsor_sponsorships': sponsor_sponsorships,
        'sponsor_avg_rating': sponsor_avg_rating,
        # Professional data
        'job_applications': job_applications,
        'is_available': is_available,
        'hourly_rate': hourly_rate,
        'user_roles': user_roles,
    }
    return render(request, 'users/public_profile.html', context)


# ===== VIEWS CHO HLV =====

@login_required
def create_coach_profile(request):
    """Tạo hoặc cập nhật hồ sơ HLV"""
    from .models import CoachProfile
    from tournaments.forms import CoachProfileForm
    
    # Kiểm tra user đã có CoachProfile chưa
    try:
        coach_profile = request.user.coach_profile
        is_new = False
    except CoachProfile.DoesNotExist:
        coach_profile = None
        is_new = True
    
    if request.method == 'POST':
        form = CoachProfileForm(request.POST, request.FILES, instance=coach_profile)
        if form.is_valid():
            coach = form.save(commit=False)
            coach.user = request.user
            coach.save()
            
            # Thêm role COACH nếu chưa có
            coach_role = Role.objects.get(id='COACH')
            if coach_role not in request.user.profile.roles.all():
                request.user.profile.roles.add(coach_role)
            
            if is_new:
                messages.success(request, "Đã tạo hồ sơ Huấn luyện viên thành công!")
            else:
                messages.success(request, "Đã cập nhật hồ sơ Huấn luyện viên!")
            
            return redirect('coach_profile_detail', pk=coach.pk)
    else:
        form = CoachProfileForm(instance=coach_profile)
    
    context = {
        'form': form,
        'is_new': is_new,
        'coach_profile': coach_profile
    }
    
    return render(request, 'users/coach_profile_form.html', context)


def coach_profile_detail(request, pk):
    """Redirect to unified public profile"""
    from .models import CoachProfile
    coach_profile = get_object_or_404(CoachProfile, pk=pk)
    return redirect('public_profile', username=coach_profile.user.username)


# ===== VIEWS CHO SÂN BÓNG =====

@login_required
def create_stadium_profile(request):
    """Tạo hoặc cập nhật hồ sơ Sân bóng"""
    from .models import StadiumProfile
    from .forms import StadiumProfileForm
    
    # Kiểm tra user có vai trò STADIUM không
    if not request.user.profile.roles.filter(id='STADIUM').exists():
        messages.error(request, "Bạn cần có vai trò Sân bóng để truy cập trang này.")
        return redirect('dashboard')
    
    # Kiểm tra user đã có StadiumProfile chưa
    try:
        stadium_profile = request.user.stadium_profile
        is_new = False
    except StadiumProfile.DoesNotExist:
        stadium_profile = None
        is_new = True
    
    if request.method == 'POST':
        form = StadiumProfileForm(request.POST, request.FILES, instance=stadium_profile)
        if form.is_valid():
            stadium = form.save(commit=False)
            stadium.user = request.user
            stadium.save()
            
            # Thêm role STADIUM nếu chưa có
            stadium_role = Role.objects.get(id='STADIUM')
            if stadium_role not in request.user.profile.roles.all():
                request.user.profile.roles.add(stadium_role)
            
            if is_new:
                messages.success(request, "Đã tạo hồ sơ Sân bóng thành công!")
            else:
                messages.success(request, "Đã cập nhật hồ sơ Sân bóng!")
            
            return redirect('stadium_dashboard')
    else:
        form = StadiumProfileForm(instance=stadium_profile)
    
    context = {
        'form': form,
        'is_new': is_new,
        'stadium_profile': stadium_profile
    }
    
    return render(request, 'users/stadium_profile_form.html', context)


@login_required
def stadium_profile_detail(request, pk):
    """Redirect to unified public profile"""
    stadium_profile = get_object_or_404(StadiumProfile, pk=pk)
    return redirect('public_profile', username=stadium_profile.user.username)


@login_required
def stadium_dashboard(request):
    """Dashboard cho Sân bóng"""
    from .models import StadiumProfile
    from organizations.models import JobPosting, JobApplication
    
    # Kiểm tra user có vai trò STADIUM không
    if not request.user.profile.roles.filter(id='STADIUM').exists():
        messages.error(request, "Bạn cần có vai trò Sân bóng để truy cập trang này.")
        return redirect('dashboard')
    
    # Kiểm tra user có StadiumProfile không
    if not hasattr(request.user, 'stadium_profile'):
        messages.warning(request, "Bạn cần tạo hồ sơ Sân bóng trước.")
        return redirect('create_stadium_profile')
    
    stadium_profile = request.user.stadium_profile
    
    # Lấy các tin tuyển dụng của sân
    job_postings = JobPosting.objects.filter(
        stadium=stadium_profile
    ).annotate(
        application_count=Count('applications')
    ).order_by('-created_at')
    
    # Lấy các ứng viên mới
    recent_applications = JobApplication.objects.filter(
        job__stadium=stadium_profile,
        status=JobApplication.Status.PENDING
    ).select_related('job', 'applicant', 'applicant__profile').order_by('-applied_at')[:10]
    
    context = {
        'stadium_profile': stadium_profile,
        'job_postings': job_postings,
        'recent_applications': recent_applications,
    }
    
    return render(request, 'users/stadium_dashboard.html', context)


@login_required
def create_stadium_job_posting(request):
    """Sân bóng đăng tin tuyển dụng"""
    from .models import StadiumProfile
    from organizations.models import JobPosting
    from organizations.forms import JobPostingForm
    
    # Kiểm tra user có vai trò STADIUM không
    if not request.user.profile.roles.filter(id='STADIUM').exists():
        messages.error(request, "Bạn cần có vai trò Sân bóng để truy cập trang này.")
        return redirect('dashboard')
    
    # Kiểm tra user có StadiumProfile
    if not hasattr(request.user, 'stadium_profile'):
        messages.error(request, "Bạn cần tạo hồ sơ Sân bóng trước.")
        return redirect('create_stadium_profile')
    
    stadium = request.user.stadium_profile
    
    if request.method == 'POST':
        # Tạo JobPosting với posted_by=STADIUM
        job = JobPosting.objects.create(
            posted_by=JobPosting.PostedBy.STADIUM,
            stadium=stadium,
            role_required_id=request.POST['role_required'],
            title=request.POST['title'],
            description=request.POST['description'],
            budget=request.POST.get('budget', ''),
            location_detail=request.POST.get('location_detail', stadium.location_detail)
        )
        
        messages.success(request, "Đã đăng tin tuyển dụng thành công!")
        return redirect('stadium_dashboard')
    
    # Lấy danh sách roles
    roles = Role.objects.all().order_by('order')
    
    context = {
        'stadium': stadium,
        'roles': roles,
    }
    
    return render(request, 'users/stadium_job_posting_form.html', context)


@login_required
def stadium_job_applications(request):
    """Stadium owner xem và quản lý job applications"""
    # Kiểm tra user có vai trò STADIUM không
    if not request.user.profile.roles.filter(id='STADIUM').exists():
        messages.error(request, "Bạn cần có vai trò Sân bóng để truy cập trang này.")
        return redirect('dashboard')
    
    # Kiểm tra user có stadium profile không
    if not hasattr(request.user, 'stadium_profile'):
        messages.warning(request, "Bạn cần tạo hồ sơ Sân bóng trước.")
        return redirect('create_stadium_profile')
    
    stadium = request.user.stadium_profile
    
    # Lấy tất cả job postings của stadium này
    job_postings = stadium.job_postings.all()
    
    # Lấy tất cả applications cho các job của stadium
    applications = JobApplication.objects.filter(
        job__stadium=stadium
    ).select_related('applicant', 'job').order_by('-applied_at')
    
    # Thống kê
    total_applications = applications.count()
    pending_applications = applications.filter(status=JobApplication.Status.PENDING).count()
    accepted_applications = applications.filter(status=JobApplication.Status.APPROVED).count()
    rejected_applications = applications.filter(status=JobApplication.Status.REJECTED).count()
    
    context = {
        'stadium': stadium,
        'job_postings': job_postings,
        'applications': applications,
        'total_applications': total_applications,
        'pending_applications': pending_applications,
        'accepted_applications': accepted_applications,
        'rejected_applications': rejected_applications,
    }
    
    return render(request, 'users/stadium_job_applications.html', context)


@login_required
def stadium_job_application_detail(request, application_pk):
    """Stadium owner xem chi tiết một job application"""
    # Kiểm tra user có vai trò STADIUM không
    if not request.user.profile.roles.filter(id='STADIUM').exists():
        messages.error(request, "Bạn cần có vai trò Sân bóng để truy cập trang này.")
        return redirect('dashboard')
    
    # Kiểm tra user có stadium profile không
    if not hasattr(request.user, 'stadium_profile'):
        messages.warning(request, "Bạn cần tạo hồ sơ Sân bóng trước.")
        return redirect('create_stadium_profile')
    
    stadium = request.user.stadium_profile
    application = get_object_or_404(JobApplication, pk=application_pk, job__stadium=stadium)
    
    # Xử lý POST request (accept/reject application)
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'accept':
            application.status = JobApplication.Status.APPROVED
            application.save()
            
            # Tự động đóng job posting khi đã chấp nhận ứng viên
            job = application.job
            job.status = JobPosting.Status.CLOSED
            job.save()
            
            # Gửi thông báo cho applicant
            from tournaments.models import Notification
            Notification.objects.create(
                user=application.applicant,
                title=f"Đơn ứng tuyển được chấp nhận",
                message=f"Đơn ứng tuyển của bạn cho vị trí '{job.title}' tại {stadium.stadium_name} đã được chấp nhận!",
                notification_type=Notification.NotificationType.GENERIC,
                related_url=f"/users/profile/{application.applicant.pk}/"
            )
            
            messages.success(request, f"Đã chấp nhận đơn ứng tuyển của {application.applicant.get_full_name() or application.applicant.username}. Tin tuyển dụng '{job.title}' đã được đóng.")
            
        elif action == 'reject':
            application.status = JobApplication.Status.REJECTED
            application.save()
            
            # Gửi thông báo cho applicant
            from tournaments.models import Notification
            Notification.objects.create(
                user=application.applicant,
                title=f"Đơn ứng tuyển bị từ chối",
                message=f"Đơn ứng tuyển của bạn cho vị trí '{application.job.title}' tại {stadium.stadium_name} đã bị từ chối.",
                notification_type=Notification.NotificationType.GENERIC,
                related_url=f"/users/profile/{application.applicant.pk}/"
            )
            
            messages.info(request, f"Đã từ chối đơn ứng tuyển của {application.applicant.get_full_name() or application.applicant.username}")
        
        return redirect('stadium_dashboard')
    
    context = {
        'stadium': stadium,
        'application': application,
    }
    
    return render(request, 'users/stadium_job_application_detail.html', context)


@login_required
def edit_stadium_job_posting(request, job_pk):
    """Stadium owner chỉnh sửa job posting của mình"""
    # Kiểm tra user có vai trò STADIUM không
    if not request.user.profile.roles.filter(id='STADIUM').exists():
        messages.error(request, "Bạn cần có vai trò Sân bóng để truy cập trang này.")
        return redirect('dashboard')
    
    # Kiểm tra user có stadium profile không
    if not hasattr(request.user, 'stadium_profile'):
        messages.warning(request, "Bạn cần tạo hồ sơ Sân bóng trước.")
        return redirect('create_stadium_profile')
    
    stadium = request.user.stadium_profile
    job = get_object_or_404(JobPosting, pk=job_pk, stadium=stadium)
    
    if request.method == 'POST':
        from organizations.forms import JobPostingForm
        form = JobPostingForm(request.POST, instance=job)
        if form.is_valid():
            job_posting = form.save(commit=False)
            job_posting.stadium = stadium
            job_posting.posted_by = 'STADIUM'
            job_posting.save()
            
            messages.success(request, f"Đã cập nhật tin tuyển dụng '{job_posting.title}' thành công!")
            return redirect('stadium_dashboard')
    else:
        from organizations.forms import JobPostingForm
        form = JobPostingForm(instance=job)
    
    # Lấy danh sách roles
    from .models import Role
    roles = Role.objects.all().order_by('order')
    
    context = {
        'form': form,
        'job': job,
        'stadium': stadium,
        'roles': roles,
        'is_edit': True,
    }
    
    return render(request, 'users/stadium_job_posting_form.html', context)


@login_required
def create_coach_review(request, coach_pk):
    """Tạo đánh giá cho Huấn luyện viên."""
    coach_profile = get_object_or_404(CoachProfile, pk=coach_pk)
    
    # Kiểm tra xem user đã đánh giá HLV này chưa
    existing_review = CoachReview.objects.filter(
        coach_profile=coach_profile,
        reviewer=request.user
    ).first()
    
    if existing_review:
        messages.warning(request, "Bạn đã đánh giá HLV này rồi!")
        return redirect('coach_profile_detail', pk=coach_pk)
    
    if request.method == 'POST':
        from .forms import CoachReviewForm
        form = CoachReviewForm(request.POST, user=request.user)
        if form.is_valid():
            review = form.save(commit=False)
            review.coach_profile = coach_profile
            review.reviewer = request.user
            review.save()
            
            messages.success(request, f"Đã đánh giá HLV {coach_profile.full_name} thành công!")
            return redirect('coach_profile_detail', pk=coach_pk)
    else:
        from .forms import CoachReviewForm
        form = CoachReviewForm(user=request.user)
    
    context = {
        'form': form,
        'coach_profile': coach_profile,
    }
    
    return render(request, 'users/create_coach_review.html', context)


@login_required
def create_stadium_review(request, stadium_pk):
    """Tạo đánh giá cho Sân bóng."""
    stadium_profile = get_object_or_404(StadiumProfile, pk=stadium_pk)
    
    # Kiểm tra xem user đã đánh giá sân này chưa
    existing_review = StadiumReview.objects.filter(
        stadium_profile=stadium_profile,
        reviewer=request.user
    ).first()
    
    if existing_review:
        messages.warning(request, "Bạn đã đánh giá sân bóng này rồi!")
        return redirect('stadium_profile_detail', pk=stadium_pk)
    
    if request.method == 'POST':
        from .forms import StadiumReviewForm
        form = StadiumReviewForm(request.POST, user=request.user)
        if form.is_valid():
            review = form.save(commit=False)
            review.stadium_profile = stadium_profile
            review.reviewer = request.user
            review.save()
            
            messages.success(request, f"Đã đánh giá sân bóng {stadium_profile.stadium_name} thành công!")
            return redirect('stadium_profile_detail', pk=stadium_pk)
    else:
        from .forms import StadiumReviewForm
        form = StadiumReviewForm(user=request.user)
    
    context = {
        'form': form,
        'stadium_profile': stadium_profile,
    }
    
    return render(request, 'users/create_stadium_review.html', context)




@login_required
def upload_profile_banner(request):
    """Upload profile banner image"""
    if request.method == 'POST':
        banner_image = request.FILES.get('banner_image')
        if banner_image:
            # Validate file size (max 5MB)
            if banner_image.size > 5 * 1024 * 1024:
                messages.error(request, "Kích thước ảnh không được vượt quá 5MB.")
                return redirect('public_profile', username=request.user.username)
            
            # Validate file type
            allowed_types = ['image/jpeg', 'image/jpg', 'image/png', 'image/webp']
            if banner_image.content_type not in allowed_types:
                messages.error(request, "Chỉ chấp nhận file ảnh (JPG, PNG, WebP).")
                return redirect('public_profile', username=request.user.username)
            
            # Save to profile
            profile = request.user.profile
            profile.banner_image = banner_image
            profile.save()
            
            messages.success(request, "Đã cập nhật ảnh bìa hồ sơ thành công!")
    return redirect('public_profile', username=request.user.username)


# === VIEW CHO FORM THỐNG NHẤT ===
@login_required
def unified_professional_form_view(request):
    """View xử lý form thống nhất cho tất cả vai trò chuyên môn"""
    profile = request.user.profile
    
    if request.method == 'POST':
        form = UnifiedProfessionalForm(request.POST, request.FILES, instance=profile, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Đã cập nhật thông tin chuyên môn thành công!')
            return redirect('public_profile', username=request.user.username)
        else:
            messages.error(request, 'Có lỗi xảy ra. Vui lòng kiểm tra lại thông tin.')
    else:
        form = UnifiedProfessionalForm(instance=profile, user=request.user)
    
    # Get user roles for context
    user_roles = profile.roles.all()
    role_ids = [role.id for role in user_roles]
    
    context = {
        'form': form,
        'user_roles': role_ids,
        'profile': profile,
    }
    return render(request, 'users/unified_professional_form.html', context)


@login_required
def review_user_view(request, username):
    """Trang tổng hợp đánh giá cho tất cả vai trò của user"""
    profile_user = get_object_or_404(User, username=username)
    
    # Không cho phép tự đánh giá
    if request.user == profile_user:
        messages.error(request, "Bạn không thể đánh giá chính mình.")
        return redirect('public_profile', username=username)
    
    # Lấy thông tin các profile
    coach_profile = None
    stadium_profile = None
    sponsor_profile = None
    
    try:
        coach_profile = profile_user.coach_profile
    except CoachProfile.DoesNotExist:
        pass
    
    try:
        stadium_profile = profile_user.stadium_profile
    except StadiumProfile.DoesNotExist:
        pass
    
    try:
        sponsor_profile = profile_user.sponsor_profile
    except SponsorProfile.DoesNotExist:
        pass
    
    # Kiểm tra đánh giá đã tồn tại
    existing_reviews = {
        'coach': None,
        'stadium': None,
        'sponsor': None,
    }
    
    if coach_profile:
        existing_reviews['coach'] = CoachReview.objects.filter(
            coach_profile=coach_profile,
            reviewer=request.user
        ).first()
    
    if stadium_profile:
        existing_reviews['stadium'] = StadiumReview.objects.filter(
            stadium_profile=stadium_profile,
            reviewer=request.user
        ).first()
    
    if sponsor_profile:
        from sponsors.models import Testimonial
        existing_reviews['sponsor'] = Testimonial.objects.filter(
            sponsor_profile=sponsor_profile,
            author=request.user
        ).first()
    
    # Kiểm tra vai trò chuyên gia
    professional_roles = profile_user.profile.roles.filter(
        id__in=['COMMENTATOR', 'MEDIA', 'PHOTOGRAPHER', 'REFEREE']
    )
    has_professional_roles = professional_roles.exists()
    
    context = {
        'profile_user': profile_user,
        'coach_profile': coach_profile,
        'stadium_profile': stadium_profile,
        'sponsor_profile': sponsor_profile,
        'existing_reviews': existing_reviews,
        'has_professional_roles': has_professional_roles,
        'professional_roles': professional_roles,
    }
    
    return render(request, 'users/review_user.html', context)


# ===== VIEWS CHO CHUYÊN GIA (PROFESSIONAL) =====

@login_required
def professional_dashboard(request):
    """Dashboard cho Chuyên gia (COACH, COMMENTATOR, MEDIA, PHOTOGRAPHER, REFEREE)"""
    
    # Kiểm tra user có vai trò chuyên gia không
    professional_role_ids = ['COACH', 'COMMENTATOR', 'MEDIA', 'PHOTOGRAPHER', 'REFEREE']
    user_roles = request.user.profile.roles.filter(id__in=professional_role_ids)
    
    if not user_roles.exists():
        messages.error(request, "Bạn cần có vai trò chuyên gia để truy cập trang này.")
        return redirect('dashboard')
    
    # Lấy các tin đã đăng của chuyên gia này
    job_postings = JobPosting.objects.filter(
        professional_user=request.user,
        posted_by=JobPosting.PostedBy.PROFESSIONAL
    ).annotate(
        application_count=Count('applications')
    ).order_by('-created_at')
    
    # Lấy các ứng tuyển/lời mời cho tin của mình
    recent_applications = JobApplication.objects.filter(
        job__professional_user=request.user,
        status=JobApplication.Status.PENDING
    ).select_related('job', 'applicant', 'applicant__profile').order_by('-applied_at')[:10]
    
    context = {
        'user_roles': user_roles,
        'job_postings': job_postings,
        'recent_applications': recent_applications,
    }
    
    return render(request, 'users/professional_dashboard.html', context)


@login_required
def create_professional_job_posting(request):
    """Chuyên gia đăng tin tìm việc"""
    
    # Kiểm tra user có vai trò chuyên gia không
    professional_role_ids = ['COACH', 'COMMENTATOR', 'MEDIA', 'PHOTOGRAPHER', 'REFEREE']
    user_roles = request.user.profile.roles.filter(id__in=professional_role_ids)
    
    if not user_roles.exists():
        messages.error(request, "Bạn cần có vai trò chuyên gia (COACH, COMMENTATOR, MEDIA, PHOTOGRAPHER, REFEREE) để đăng tin tìm việc.")
        return redirect('dashboard')
    
    if request.method == 'POST':
        from .forms import ProfessionalJobSeekingForm
        
        # Tạo form với instance để có thể set các field trước khi validation
        form = ProfessionalJobSeekingForm(request.POST, user=request.user)
        
        if form.is_valid():
            job = form.save(commit=False)
            job.posted_by = JobPosting.PostedBy.PROFESSIONAL
            job.professional_user = request.user
            
            # Debug: in ra giá trị các field
            print(f"Posted by: {job.posted_by}")
            print(f"Professional user: {job.professional_user}")
            print(f"Tournament: {job.tournament}")
            print(f"Stadium: {job.stadium}")
            print(f"Role required: {job.role_required}")
            
            # Gọi full_clean() để trigger model validation
            try:
                job.full_clean()
                job.save()
                messages.success(request, "Đã đăng tin tìm việc thành công!")
                return redirect('professional_dashboard')
            except Exception as e:
                print(f"Model validation error: {e}")
                messages.error(request, f"Lỗi validation: {e}")
        else:
            # Debug: hiển thị lỗi form
            print("Form errors:", form.errors)
            print("Form data:", request.POST)
            print("Form non-field errors:", form.non_field_errors())
            for field, errors in form.errors.items():
                print(f"Field {field} errors: {errors}")
            
            # Hiển thị lỗi cụ thể cho user
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
            if form.non_field_errors():
                for error in form.non_field_errors():
                    messages.error(request, error)
    else:
        from .forms import ProfessionalJobSeekingForm
        form = ProfessionalJobSeekingForm(user=request.user)
    
    context = {
        'form': form,
        'user_roles': user_roles,
    }
    
    return render(request, 'users/professional_job_posting_form.html', context)


@login_required
def edit_professional_job_posting(request, job_pk):
    """Chuyên gia chỉnh sửa tin đã đăng"""
    
    job = get_object_or_404(
        JobPosting, 
        pk=job_pk, 
        professional_user=request.user,
        posted_by=JobPosting.PostedBy.PROFESSIONAL
    )
    
    if request.method == 'POST':
        from .forms import ProfessionalJobSeekingForm
        form = ProfessionalJobSeekingForm(request.POST, instance=job, user=request.user)
        
        if form.is_valid():
            job_posting = form.save(commit=False)
            job_posting.posted_by = JobPosting.PostedBy.PROFESSIONAL
            job_posting.professional_user = request.user
            job_posting.save()
            
            messages.success(request, f"Đã cập nhật tin '{job_posting.title}' thành công!")
            return redirect('professional_dashboard')
    else:
        from .forms import ProfessionalJobSeekingForm
        form = ProfessionalJobSeekingForm(instance=job, user=request.user)
    
    context = {
        'form': form,
        'job': job,
        'is_edit': True,
    }
    
    return render(request, 'users/professional_job_posting_form.html', context)


@login_required
def delete_professional_job_posting(request, job_pk):
    """Xóa tin đăng của chuyên gia"""
    
    job = get_object_or_404(
        JobPosting, 
        pk=job_pk, 
        professional_user=request.user,
        posted_by=JobPosting.PostedBy.PROFESSIONAL
    )
    
    if request.method == 'POST':
        job_title = job.title
        job.delete()
        messages.success(request, f"Đã xóa tin '{job_title}' thành công!")
        return redirect('professional_dashboard')
    
    context = {
        'job': job,
    }
    
    return render(request, 'users/confirm_delete_job.html', context)


@login_required
def professional_job_applications(request):
    """Xem các ứng tuyển cho tin tìm việc của chuyên gia"""
    
    # Kiểm tra user có vai trò chuyên gia không
    professional_role_ids = ['COACH', 'COMMENTATOR', 'MEDIA', 'PHOTOGRAPHER', 'REFEREE']
    if not request.user.profile.roles.filter(id__in=professional_role_ids).exists():
        messages.error(request, "Bạn cần có vai trò chuyên gia để truy cập trang này.")
        return redirect('dashboard')
    
    # Lấy tất cả tin đã đăng của chuyên gia
    job_postings = JobPosting.objects.filter(
        professional_user=request.user,
        posted_by=JobPosting.PostedBy.PROFESSIONAL
    )
    
    # Lấy tất cả applications cho các tin của chuyên gia
    applications = JobApplication.objects.filter(
        job__professional_user=request.user,
        job__posted_by=JobPosting.PostedBy.PROFESSIONAL
    ).select_related('applicant', 'job', 'applicant__profile').order_by('-applied_at')
    
    # Thống kê
    total_applications = applications.count()
    pending_applications = applications.filter(status=JobApplication.Status.PENDING).count()
    accepted_applications = applications.filter(status=JobApplication.Status.APPROVED).count()
    rejected_applications = applications.filter(status=JobApplication.Status.REJECTED).count()
    
    context = {
        'job_postings': job_postings,
        'applications': applications,
        'total_applications': total_applications,
        'pending_applications': pending_applications,
        'accepted_applications': accepted_applications,
        'rejected_applications': rejected_applications,
    }
    
    return render(request, 'users/professional_job_applications.html', context)


@login_required
def professional_job_application_detail(request, application_pk):
    """Xem chi tiết một ứng tuyển và xử lý (accept/reject)"""
    
    # Kiểm tra user có vai trò chuyên gia không
    professional_role_ids = ['COACH', 'COMMENTATOR', 'MEDIA', 'PHOTOGRAPHER', 'REFEREE']
    if not request.user.profile.roles.filter(id__in=professional_role_ids).exists():
        messages.error(request, "Bạn cần có vai trò chuyên gia để truy cập trang này.")
        return redirect('dashboard')
    
    application = get_object_or_404(
        JobApplication, 
        pk=application_pk, 
        job__professional_user=request.user,
        job__posted_by=JobPosting.PostedBy.PROFESSIONAL
    )
    
    # Xử lý POST request (accept/reject)
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'accept':
            application.status = JobApplication.Status.APPROVED
            application.save()
            
            # Tự động đóng tin đăng khi đã chấp nhận
            job = application.job
            job.status = JobPosting.Status.CLOSED
            job.save()
            
            # Gửi thông báo cho applicant
            from tournaments.models import Notification
            Notification.objects.create(
                user=application.applicant,
                title=f"Ứng tuyển được chấp nhận",
                message=f"Chuyên gia {request.user.get_full_name() or request.user.username} đã chấp nhận đơn ứng tuyển của bạn cho '{job.title}'!",
                notification_type=Notification.NotificationType.GENERIC,
                related_url=f"/users/profile/{request.user.username}/"
            )
            
            messages.success(request, f"Đã chấp nhận đơn ứng tuyển của {application.applicant.get_full_name() or application.applicant.username}.")
            
        elif action == 'reject':
            application.status = JobApplication.Status.REJECTED
            application.save()
            
            # Gửi thông báo
            from tournaments.models import Notification
            Notification.objects.create(
                user=application.applicant,
                title=f"Ứng tuyển bị từ chối",
                message=f"Chuyên gia {request.user.get_full_name() or request.user.username} đã từ chối đơn ứng tuyển của bạn cho '{application.job.title}'.",
                notification_type=Notification.NotificationType.GENERIC,
                related_url=f"/users/profile/{request.user.username}/"
            )
            
            messages.info(request, f"Đã từ chối đơn ứng tuyển của {application.applicant.get_full_name() or application.applicant.username}")
        
        return redirect('professional_dashboard')
    
    context = {
        'application': application,
    }
    
    return render(request, 'users/professional_job_application_detail.html', context)