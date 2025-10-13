# backend/users/urls.py

from django.urls import path, include
from . import views

urlpatterns = [
    # Giữ lại các URL quan trọng của bạn
    path('dashboard/', views.dashboard, name='dashboard'),
    path('select-roles/', views.select_roles_view, name='select_roles'),
    path('profile-setup/', views.profile_setup_view, name='profile_setup'),
    path('profile/<str:username>/', views.public_profile_view, name='public_profile'),
    
    # URLs cho Huấn luyện viên
    path('coach/create/', views.create_coach_profile, name='create_coach_profile'),
    path('coach/<int:pk>/', views.coach_profile_detail, name='coach_profile_detail'),
    
    # URLs cho Sân bóng
    path('stadium/create/', views.create_stadium_profile, name='create_stadium_profile'),
    path('stadium/dashboard/', views.stadium_dashboard, name='stadium_dashboard'),
    path('stadium/job/create/', views.create_stadium_job_posting, name='create_stadium_job_posting'),
    
    # Để allauth xử lý mọi thứ liên quan đến tài khoản
    # URL của allauth đã bao gồm login, logout, register, password reset...
    path('', include('allauth.urls')),
]