# users/views.py

from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm, AuthenticationForm
from django.contrib import messages
from tournaments.models import Team
# Import các form tùy chỉnh mới
from .forms import CustomUserCreationForm, CustomUserChangeForm

def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST) # <-- Sửa ở đây
        if form.is_valid():
            form.save()
            return redirect('login')
    else:
        form = CustomUserCreationForm() # <-- Và ở đây
        
    return render(request, 'users/register.html', {'form': form})

    return render(request, 'users/register.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('home') # Chuyển về trang chủ sau khi đăng nhập
    else:
        form = AuthenticationForm()
    return render(request, 'users/login.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('home') # Chuyển về trang chủ sau khi đăng xuất

@login_required
def dashboard(request):
    # Lấy tất cả các đội mà người dùng hiện tại là đội trưởng
    managed_teams = Team.objects.filter(captain=request.user)

    context = {
        'managed_teams': managed_teams
    }
    return render(request, 'users/dashboard.html', context)    

@login_required
def profile_view(request):
    if request.method == 'POST':
        if 'update_profile' in request.POST:
            user_form = CustomUserChangeForm(request.POST, instance=request.user) # <-- Sửa ở đây
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
        user_form = CustomUserChangeForm(instance=request.user) # <-- Và ở đây
        password_form = PasswordChangeForm(request.user)

    context = {
        'user_form': user_form,
        'password_form': password_form
    }
    return render(request, 'users/profile.html', context)