# backend/users/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib import messages
# Import các model từ đúng ứng dụng của chúng
from tournaments.models import Team, Player, Tournament, Player, TeamAchievement, VoteRecord, TournamentStaff, PlayerTransfer, ScoutingList 
from .forms import CustomUserChangeForm, AvatarUpdateForm, NotificationPreferencesForm, ProfileSetupForm, ProfileUpdateForm, ProfileUpdateForm
from .models import Profile, Role
from django.contrib.auth.models import User
# Thêm import đánh giá công việc
from organizations.models import ProfessionalReview
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
        form = ProfileSetupForm(instance=profile, user=request.user)

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
    profile_user = get_object_or_404(User.objects.select_related('profile'), username=username)
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

    context = {
        'profile_user': profile_user,
        'profile': profile,
        'achievements': achievements,
        'commentator_gigs': commentator_gigs,
        'media_gigs': media_gigs,
        'reviews': reviews,                     # Gửi reviews ra template
        'average_rating': average_rating,       # Gửi rating trung bình
        'reviews_count': reviews.count(),       # Gửi tổng số reviews
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


@login_required
def coach_profile_detail(request, pk):
    """Chi tiết hồ sơ HLV"""
    from .models import CoachProfile
    from tournaments.models import CoachRecruitment
    
    coach_profile = get_object_or_404(CoachProfile.objects.select_related('user', 'team'), pk=pk)
    
    # Kiểm tra quyền chỉnh sửa
    can_edit = request.user == coach_profile.user
    
    # Lấy lịch sử chiêu mộ nếu là chính user đó
    recruitment_history = None
    if can_edit:
        recruitment_history = CoachRecruitment.objects.filter(
            coach=coach_profile
        ).select_related('team', 'team__captain').order_by('-created_at')[:5]
    
    context = {
        'coach_profile': coach_profile,
        'can_edit': can_edit,
        'recruitment_history': recruitment_history,
    }
    
    return render(request, 'users/coach_profile_detail.html', context)


# ===== VIEWS CHO SÂN BÓNG =====

@login_required
def create_stadium_profile(request):
    """Tạo hoặc cập nhật hồ sơ Sân bóng"""
    from .models import StadiumProfile
    from .forms import StadiumProfileForm
    
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
def stadium_dashboard(request):
    """Dashboard cho Sân bóng"""
    from .models import StadiumProfile
    from organizations.models import JobPosting, JobApplication
    
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