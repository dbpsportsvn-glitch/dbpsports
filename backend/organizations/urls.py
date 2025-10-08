# organizations/urls.py
from django.urls import path
# --- SỬA ĐỔI IMPORT ---
# Import tường minh các views để dễ quản lý
from .views import (
    organization_dashboard, create_tournament, manage_tournament, edit_tournament,
    delete_tournament, manage_match, create_match, delete_match, delete_group,
    delete_goal, delete_card, manage_knockout, delete_photo, delete_all_photos,
    delete_team, edit_player, delete_player, create_organization, remove_member,
    manage_sponsors_view, delete_sponsorship_view, add_tournament_staff,
    remove_tournament_staff, manage_jobs_view, edit_job_view,
    update_application_status_view, create_review_view, delete_closed_jobs_view,
    create_announcement, edit_announcement, delete_announcement, send_announcement_email,
    
    # Views mới cho Gói tài trợ
    SponsorshipPackageListView, SponsorshipPackageCreateView, 
    SponsorshipPackageUpdateView, SponsorshipPackageDeleteView,
)

app_name = 'organizations'

urlpatterns = [
    path('dashboard/', organization_dashboard, name='dashboard'),
    path('create/', create_organization, name='create'),
    path('members/<int:pk>/remove/', remove_member, name='remove_member'),
    
    # Quản lý giải đấu
    path('tournaments/create/', create_tournament, name='create_tournament'),
    path('tournaments/<int:pk>/manage/', manage_tournament, name='manage_tournament'),
    path('tournaments/<int:pk>/edit/', edit_tournament, name='edit_tournament'),
    path('tournaments/<int:pk>/delete/', delete_tournament, name='delete_tournament'),

    # Quản lý trận đấu
    path('tournaments/<int:tournament_pk>/create-match/', create_match, name='create_match'),
    path('match/<int:pk>/manage/', manage_match, name='manage_match'),
    path('match/<int:pk>/delete/', delete_match, name='delete_match'),
    path('goal/<int:pk>/delete/', delete_goal, name='delete_goal'),
    path('card/<int:pk>/delete/', delete_card, name='delete_card'),

    # Quản lý vòng Knockout & Bảng đấu
    path('tournaments/<int:pk>/knockout/', manage_knockout, name='manage_knockout'),
    path('groups/<int:pk>/delete/', delete_group, name='delete_group'),

    # Quản lý Media
    path('photo/<int:pk>/delete/', delete_photo, name='delete_photo'),
    path('tournaments/<int:tournament_pk>/photos/delete-all/', delete_all_photos, name='delete_all_photos'),

    # Quản lý Đội & Cầu thủ
    path('registrations/<int:pk>/delete/', delete_team, name='delete_team_registration'),
    path('player/<int:pk>/edit/', edit_player, name='edit_player'),
    path('player/<int:pk>/delete/', delete_player, name='delete_player'),

    # === QUẢN LÝ NHÀ TÀI TRỢ & GÓI TÀI TRỢ ===
    # URLs cho quản lý Nhà tài trợ (Sponsorship)
    path('tournaments/<int:tournament_pk>/sponsors/', manage_sponsors_view, name='manage_sponsors'),
    path('sponsorships/<int:pk>/delete/', delete_sponsorship_view, name='delete_sponsorship'),
    
    # --- THÊM URLS MỚI CHO GÓI TÀI TRỢ ---
    path('tournaments/<int:tournament_id>/manage/sponsorship-packages/', SponsorshipPackageListView.as_view(), name='manage_sponsorship_packages'),
    path('tournaments/<int:tournament_id>/manage/sponsorship-packages/create/', SponsorshipPackageCreateView.as_view(), name='create_sponsorship_package'),
    path('manage/sponsorship-packages/<int:pk>/update/', SponsorshipPackageUpdateView.as_view(), name='update_sponsorship_package'),
    path('manage/sponsorship-packages/<int:pk>/delete/', SponsorshipPackageDeleteView.as_view(), name='delete_sponsorship_package'),
    # --- KẾT THÚC ---

    # Quản lý nhân sự giải đấu
    path('tournaments/<int:tournament_pk>/staff/add/', add_tournament_staff, name='add_tournament_staff'),
    path('staff/<int:pk>/remove/', remove_tournament_staff, name='remove_tournament_staff'),

    # Quản lý thị trường công việc
    path('tournaments/<int:tournament_pk>/jobs/', manage_jobs_view, name='manage_jobs'),
    path('jobs/<int:pk>/edit/', edit_job_view, name='edit_job'),
    path('applications/<int:pk>/update/', update_application_status_view, name='update_application_status'),
    path('applications/<int:application_pk>/review/', create_review_view, name='create_review'),
    path('tournaments/<int:tournament_pk>/jobs/delete-closed/', delete_closed_jobs_view, name='delete_closed_jobs'),

    # Quản lý thông báo
    path('tournaments/<int:tournament_pk>/announcements/create/', create_announcement, name='create_announcement'),
    path('announcements/<int:pk>/edit/', edit_announcement, name='edit_announcement'),
    path('announcements/<int:pk>/delete/', delete_announcement, name='delete_announcement'),
    path('announcements/<int:pk>/send/', send_announcement_email, name='send_announcement_email'),
]