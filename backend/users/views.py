# backend/users/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib import messages
# Import các model từ đúng ứng dụng của chúng
from tournaments.models import Team, Tournament, Player, TeamAchievement, VoteRecord, TournamentStaff 
from .forms import CustomUserChangeForm, AvatarUpdateForm, NotificationPreferencesForm, ProfileSetupForm, ProfileUpdateForm
from .models import Profile, Role
from django.contrib.auth.models import User
# === KẾT THÚC THAY THẾ ===

@login_required
def dashboard(request):
    profile, created = Profile.objects.get_or_create(user=request.user)
    avatar_form_has_errors = False

    user_form = CustomUserChangeForm(instance=request.user)
    password_form = PasswordChangeForm(request.user)
    avatar_form = AvatarUpdateForm(instance=profile)
    preferences_form = NotificationPreferencesForm(instance=profile)
    profile_form = ProfileUpdateForm(instance=profile)

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

        if 'update_preferences' in request.POST:
            preferences_form = NotificationPreferencesForm(request.POST, instance=profile)
            if preferences_form.is_valid():
                preferences_form.save()
                messages.success(request, 'Đã cập nhật cài đặt thông báo của bạn!')
                return redirect(request.path_info + '?tab=notifications')

        # === ĐẢM BẢO KHỐI NÀY ĐÚNG ===
        if 'update_public_profile' in request.POST:
            profile_form = ProfileUpdateForm(request.POST, instance=profile)
            if profile_form.is_valid():
                profile_form.save()
                messages.success(request, 'Đã cập nhật hồ sơ công khai của bạn!')
                return redirect(request.path_info + '?tab=public-profile')

    managed_teams = Team.objects.filter(captain=request.user).select_related('tournament')
    followed_tournaments = request.user.followed_tournaments.all().exclude(status='FINISHED').order_by('start_date')
    player_profile = getattr(request.user, 'player_profile', None)

    # Lấy danh sách các giải đấu mà người dùng được gán vai trò 'Quản lý Giải đấu'
    managed_tournaments = Tournament.objects.filter(
        staff__user=request.user,
        staff__role__id='TOURNAMENT_MANAGER'
    ).distinct().order_by('-start_date')

    # === THÊM TRUY VẤN MỚI TẠI ĐÂY ===
    media_tournaments = Tournament.objects.filter(
        staff__user=request.user,
        staff__role__id__in=['MEDIA', 'PHOTOGRAPHER']
    ).distinct().order_by('-start_date')

    context = {
        'user_form': user_form,
        'password_form': password_form,
        'avatar_form': avatar_form,
        'preferences_form': preferences_form,
        'profile_form': profile_form,
        'managed_teams': managed_teams,
        'followed_tournaments': followed_tournaments,
        'player_profile': player_profile,
        'avatar_form_has_errors': avatar_form_has_errors,
        'managed_tournaments': managed_tournaments,
        'media_tournaments': media_tournaments,
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
            
            # === LOGIC PHÂN QUYỀN MỚI ===

            # 1. Tặng phiếu bầu cho vai trò Cầu thủ
            if len(selected_role_ids) == 1 and selected_role_ids[0] == 'PLAYER':
                # Tạo một bản ghi vote "ảo" để làm quà tặng
                # Lưu ý: Đây là một phiếu bầu tượng trưng, không gắn với giải đấu nào
                VoteRecord.objects.create(
                    voter=request.user,
                    weight=1 
                )
                messages.success(request, "Chúc mừng bạn đã gia nhập cộng đồng cầu thủ! Bạn được tặng 1 phiếu bầu làm quà khởi đầu.")

            # 2. Điều hướng cho Ban tổ chức
            if 'ORGANIZER' in selected_role_ids:
                messages.info(request, "Để bắt đầu, vui lòng hoàn tất thông tin đăng ký Ban tổ chức của bạn.")
                return redirect('organizations:create')
            
            # 3. Điều hướng mặc định cho các vai trò khác
            messages.success(request, "Đã lưu vai trò! Vui lòng hoàn tất hồ sơ của bạn để mọi người có thể tìm thấy bạn.")
            return redirect('profile_setup') 

    roles = Role.objects.all()
    return render(request, 'users/select_roles.html', {'roles': roles})    

@login_required
def profile_setup_view(request):
    profile = request.user.profile
    
    # Nếu đã hoàn tất hồ sơ trước đó, chuyển về trang chủ
    if profile.is_profile_complete:
        return redirect('home')

    # Xử lý các action "bỏ qua" hoặc "tạo đội ngay" từ link GET
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
        # Chuyển hướng đến trang tạo đội độc lập
        return redirect('create_standalone_team')

    # Xử lý khi người dùng nhấn nút "Lưu và Tiếp tục" (POST)
    if request.method == 'POST':
        form = ProfileSetupForm(request.POST, instance=profile, user=request.user)
        if form.is_valid():
            form.save()
            profile.is_profile_complete = True
            profile.save()
            
            # Sau khi lưu, nếu là cầu thủ, chuyển đến trang tạo đội
            if profile.roles.filter(id='PLAYER').exists():
                 messages.success(request, "Cảm ơn bạn đã cập nhật hồ sơ! Hãy bắt đầu bằng việc tạo đội bóng của bạn.")
                 # Chuyển hướng đến trang tạo đội độc lập
                 return redirect('create_standalone_team')
            
            # Nếu không phải cầu thủ, về trang chủ
            messages.success(request, "Cảm ơn bạn đã cập nhật hồ sơ!")
            return redirect('home')
    else:
        form = ProfileSetupForm(instance=profile, user=request.user)

    # Kiểm tra xem người dùng có vai trò là "Cầu thủ" hay không để hiển thị nút phù hợp
    is_player = profile.roles.filter(id='PLAYER').exists()

    context = {
        'form': form,
        'is_player': is_player # Gửi biến này ra template
    }
    return render(request, 'users/profile_setup.html', context)

# === VIEW GÂY LỖI TRƯỚC ĐÂY ===
def public_profile_view(request, username):
    profile_user = get_object_or_404(User.objects.select_related('profile'), username=username)
    profile = profile_user.profile

    player_profiles = Player.objects.filter(user=profile_user)
    team_ids = player_profiles.values_list('team_id', flat=True)
    achievements = TeamAchievement.objects.filter(team_id__in=team_ids).select_related('tournament', 'team').order_by('-achieved_at')

    context = {
        'profile_user': profile_user,
        'profile': profile,
        'achievements': achievements,
    }
    return render(request, 'users/public_profile.html', context)