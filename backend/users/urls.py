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
    path('stadium/job/<int:job_pk>/edit/', views.edit_stadium_job_posting, name='edit_stadium_job_posting'),
    path('stadium/applications/', views.stadium_job_applications, name='stadium_job_applications'),
    path('stadium/application/<int:application_pk>/', views.stadium_job_application_detail, name='stadium_job_application_detail'),
    path('coach/<int:coach_pk>/review/', views.create_coach_review, name='create_coach_review'),
    path('stadium/<int:stadium_pk>/review/', views.create_stadium_review, name='create_stadium_review'),
    path('stadium/<int:pk>/', views.stadium_profile_detail, name='stadium_profile_detail'),
    path('professional/edit/', views.unified_professional_form_view, name='unified_professional_form'),
    path('upload-banner/', views.upload_profile_banner, name='upload_profile_banner'),
    path('review/<str:username>/', views.review_user_view, name='review_user'),
    
    # URLs cho Nhà tài trợ
    path('sponsor/create/', views.create_sponsor_profile, name='create_sponsor_profile'),
    
    # URLs cho Chuyên gia (Professional)
    path('professional/dashboard/', views.professional_dashboard, name='professional_dashboard'),
    path('professional/job/create/', views.create_professional_job_posting, name='create_professional_job_posting'),
    path('professional/job/<int:job_pk>/edit/', views.edit_professional_job_posting, name='edit_professional_job_posting'),
    path('professional/job/<int:job_pk>/delete/', views.delete_professional_job_posting, name='delete_professional_job_posting'),
    path('professional/applications/', views.professional_job_applications, name='professional_job_applications'),
    path('professional/application/<int:application_pk>/', views.professional_job_application_detail, name='professional_job_application_detail'),
    
    # Allauth URLs đã được include trong dbpsports_core/urls.py
]