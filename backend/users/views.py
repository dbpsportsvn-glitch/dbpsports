# backend/users/views.py

from django.shortcuts import render, redirect
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib import messages
from tournaments.models import Team, Tournament
from .forms import CustomUserChangeForm, AvatarUpdateForm
from .models import Profile

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

    # Lấy dữ liệu cho các tab khác
    managed_teams = Team.objects.filter(captain=request.user).select_related('tournament')
    followed_tournaments = request.user.followed_tournaments.exclude(status='FINISHED').order_by('start_date')
    player_profile = getattr(request.user, 'player_profile', None)

    context = {
        'user_form': user_form,
        'password_form': password_form,
        'avatar_form': avatar_form,
        'managed_teams': managed_teams,
        'followed_tournaments': followed_tournaments,
        'player_profile': player_profile,
        'avatar_form_has_errors': avatar_form_has_errors,
    }
    return render(request, 'users/dashboard.html', context)