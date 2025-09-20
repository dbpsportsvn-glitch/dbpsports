# backend/users/views.py

from django.shortcuts import render, redirect
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib import messages
from tournaments.models import Team
from .forms import CustomUserChangeForm

@login_required
def dashboard(request):
    # Lấy tất cả các đội mà người dùng hiện tại là đội trưởng
    managed_teams = Team.objects.filter(captain=request.user).select_related('tournament')

    # --- BẮT ĐẦU NÂNG CẤP ---
    # Kiểm tra xem người dùng có hồ sơ cầu thủ nào được liên kết không
    player_profile = None
    if hasattr(request.user, 'player_profile'):
        player_profile = request.user.player_profile
    # --- KẾT THÚC NÂNG CẤP ---

    context = {
        'managed_teams': managed_teams,
        'player_profile': player_profile, # Gửi hồ sơ cầu thủ ra template
    }
    return render(request, 'users/dashboard.html', context)

@login_required
def profile_view(request):
    if request.method == 'POST':
        if 'update_profile' in request.POST:
            user_form = CustomUserChangeForm(request.POST, instance=request.user)
            if user_form.is_valid():
                user_form.save()
                messages.success(request, 'Thông tin của bạn đã được cập nhật thành công!')
                return redirect('profile')

        if 'change_password' in request.POST:
            password_form = PasswordChangeForm(request.user, request.POST)
            if password_form.is_valid():
                user = password_form.save()
                update_session_auth_hash(request, user)
                messages.success(request, 'Mật khẩu của bạn đã được thay đổi thành công!')
                return redirect('profile')
    else:
        user_form = CustomUserChangeForm(instance=request.user)
        password_form = PasswordChangeForm(request.user)

    context = {
        'user_form': user_form,
        'password_form': password_form
    }
    return render(request, 'users/profile.html', context)