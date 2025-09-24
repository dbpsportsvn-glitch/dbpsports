# backend/users/views.py

from django.shortcuts import render, redirect
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib import messages
# --- SỬA LẠI IMPORT ---
from tournaments.models import Team, Tournament
from .forms import CustomUserChangeForm

# --- THAY THẾ TOÀN BỘ VIEW `dashboard` BẰNG VIEW MỚI NÀY ---
@login_required
def dashboard(request):
    # Lấy các form
    user_form = CustomUserChangeForm(instance=request.user)
    password_form = PasswordChangeForm(request.user)

    if request.method == 'POST':
        # Xử lý khi người dùng cập nhật thông tin
        if 'update_profile' in request.POST:
            user_form = CustomUserChangeForm(request.POST, instance=request.user)
            if user_form.is_valid():
                user_form.save()
                messages.success(request, 'Thông tin của bạn đã được cập nhật thành công!')
                return redirect('dashboard') # Tải lại trang dashboard

        # Xử lý khi người dùng đổi mật khẩu
        if 'change_password' in request.POST:
            password_form = PasswordChangeForm(request.user, request.POST)
            if password_form.is_valid():
                user = password_form.save()
                update_session_auth_hash(request, user)
                messages.success(request, 'Mật khẩu của bạn đã được thay đổi thành công!')
                return redirect('dashboard') # Tải lại trang dashboard

    # Lấy dữ liệu cho các tab khác
    managed_teams = Team.objects.filter(captain=request.user).select_related('tournament')
    followed_tournaments = request.user.followed_tournaments.exclude(status='FINISHED').order_by('start_date')
    player_profile = getattr(request.user, 'player_profile', None)

    context = {
        'user_form': user_form,
        'password_form': password_form,
        'managed_teams': managed_teams,
        'followed_tournaments': followed_tournaments,
        'player_profile': player_profile,
    }
    return render(request, 'users/dashboard.html', context)
