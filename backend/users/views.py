# backend/users/views.py

# === THÊM get_object_or_404 VÀO DÒNG NÀY ===
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib import messages
from tournaments.models import Team, Tournament, Player, TeamAchievement
from .forms import CustomUserChangeForm, AvatarUpdateForm, NotificationPreferencesForm, ProfileSetupForm, ProfileUpdateForm
from .models import Profile, Role
from django.contrib.auth.models import User


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
            
            messages.success(request, "Đã lưu vai trò! Vui lòng hoàn tất hồ sơ của bạn.")
            return redirect('profile_setup') 

    roles = Role.objects.all()
    return render(request, 'users/select_roles.html', {'roles': roles})    

@login_required
def profile_setup_view(request):
    profile = request.user.profile
    
    if profile.is_profile_complete:
        return redirect('home')

    if request.method == 'POST':
        form = ProfileSetupForm(request.POST, instance=profile, user=request.user)
        if form.is_valid():
            form.save()
            profile.is_profile_complete = True
            profile.save()
            messages.success(request, "Cảm ơn bạn đã cập nhật hồ sơ!")
            return redirect('home')
    else:
        form = ProfileSetupForm(instance=profile, user=request.user)

    return render(request, 'users/profile_setup.html', {'form': form})

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