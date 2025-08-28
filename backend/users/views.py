# users/views.py

from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required # Đảm bảo đã import
from tournaments.models import Team # Import Team model
from .forms import RegisterForm


def register(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('home') # Chuyển hướng về trang chủ sau khi đăng ký thành công
    else:
        form = RegisterForm()

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