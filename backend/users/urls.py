# backend/users/urls.py

from django.urls import path, include
from . import views

urlpatterns = [
    # Giữ lại các URL quan trọng của bạn
    path('dashboard/', views.dashboard, name='dashboard'),
    path('select-roles/', views.select_roles_view, name='select_roles'),
    path('profile-setup/', views.profile_setup_view, name='profile_setup'),
    path('profile/<str:username>/', views.public_profile_view, name='public_profile'),
    # Để allauth xử lý mọi thứ liên quan đến tài khoản
    # URL của allauth đã bao gồm login, logout, register, password reset...
    path('', include('allauth.urls')),
]