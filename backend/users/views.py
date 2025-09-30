# backend/users/views.py

from django.shortcuts import render, redirect
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib import messages
from tournaments.models import Team, Tournament
from .forms import CustomUserChangeForm, AvatarUpdateForm, NotificationPreferencesForm
from .models import Profile
from .models import Role

@login_required
def dashboard(request):
    # Lấy hoặc tạo mới profile cho user
    profile, created = Profile.objects.get_or_create(user=request.user)
    # Khởi tạo cờ báo lỗi cho form avatar
    avatar_form_has_errors = False

    # Khởi tạo các form
    user_form = CustomUserChangeForm(instance=request.user)
    password_form = PasswordChangeForm(request.user)
    avatar_form = AvatarUpdateForm(instance=profile)
    preferences_form = NotificationPreferencesForm(instance=profile)

    if request.method == 'POST':
        # Xử lý khi người dùng cập nhật thông tin cá nhân
        if 'update_profile' in request.POST:
            user_form = CustomUserChangeForm(request.POST, instance=request.user)
            if user_form.is_valid():
                user_form.save()
                messages.success(request, 'Thông tin của bạn đã được cập nhật thành công!')
                return redirect('dashboard')
            else:
                messages.error(request, 'Cập nhật thông tin thất bại. Vui lòng kiểm tra lại.')

        # Xử lý khi người dùng đổi mật khẩu
        elif 'change_password' in request.POST:
            password_form = PasswordChangeForm(request.user, request.POST)
            if password_form.is_valid():
                user = password_form.save()
                update_session_auth_hash(request, user)
                messages.success(request, 'Mật khẩu của bạn đã được thay đổi thành công!')
                return redirect('dashboard')
        
        # Xử lý khi người dùng cập nhật ảnh đại diện
        elif 'update_avatar' in request.POST:
            avatar_form = AvatarUpdateForm(request.POST, request.FILES, instance=profile)
            if avatar_form.is_valid():
                avatar_form.save()
                messages.success(request, 'Ảnh đại diện đã được cập nhật!')
                return redirect('dashboard')
            else:
                # Đặt cờ báo lỗi để template có thể mở lại popup
                avatar_form_has_errors = True
                messages.error(request, 'Cập nhật ảnh đại diện thất bại. Vui lòng xem chi tiết trong popup.')

        # === THÊM MỚI: Xử lý khi người dùng cập nhật cài đặt thông báo ===
        if 'update_preferences' in request.POST:
            preferences_form = NotificationPreferencesForm(request.POST, instance=profile)
            if preferences_form.is_valid():
                preferences_form.save()
                messages.success(request, 'Đã cập nhật cài đặt thông báo của bạn!')
                return redirect('dashboard') # Sau này có thể chuyển hướng về đúng tab

    # Lấy dữ liệu cho các tab khác
    managed_teams = Team.objects.filter(captain=request.user).select_related('tournament')
    followed_tournaments = request.user.followed_tournaments.all().exclude(status='FINISHED').order_by('start_date')
    player_profile = getattr(request.user, 'player_profile', None)

    context = {
        'user_form': user_form,
        'password_form': password_form,
        'avatar_form': avatar_form,
        'preferences_form': preferences_form,
        'managed_teams': managed_teams,
        'followed_tournaments': followed_tournaments,
        'player_profile': player_profile,
        'avatar_form_has_errors': avatar_form_has_errors,
    }
    return render(request, 'users/dashboard.html', context)

# === THÊM VIEW MỚI VÀO CUỐI FILE ===
@login_required
def select_roles_view(request):
    # Lấy profile của người dùng
    profile = request.user.profile
    
    # Nếu người dùng đã chọn vai trò rồi thì chuyển hướng họ về trang dashboard
    if profile.has_selected_roles:
        return redirect('dashboard')

    if request.method == 'POST':
        # Lấy danh sách ID của các vai trò được chọn từ form
        selected_role_ids = request.POST.getlist('roles')

        # Kiểm tra giới hạn (tối đa 2 vai trò)
        if len(selected_role_ids) == 0:
            messages.error(request, "Bạn phải chọn ít nhất một vai trò.")
        elif len(selected_role_ids) > 2:
            messages.error(request, "Bạn chỉ được chọn tối đa 2 vai trò.")
        else:
            # Xóa các vai trò cũ (nếu có) và thêm các vai trò mới
            profile.roles.clear()
            for role_id in selected_role_ids:
                try:
                    role = Role.objects.get(pk=role_id)
                    profile.roles.add(role)
                except Role.DoesNotExist:
                    messages.error(request, f"Vai trò không hợp lệ: {role_id}")
                    # Quay lại trang chọn vai trò nếu có lỗi
                    return render(request, 'users/select_roles.html', {'roles': Role.objects.all()})
            
            # Đánh dấu là đã hoàn tất chọn vai trò và lưu lại
            profile.has_selected_roles = True
            profile.save()
            
            messages.success(request, "Cảm ơn bạn! Vai trò đã được cập nhật.")
            return redirect('home') # Chuyển hướng về trang chủ

    # Nếu là GET request, chỉ hiển thị trang
    roles = Role.objects.all()
    return render(request, 'users/select_roles.html', {'roles': roles})    