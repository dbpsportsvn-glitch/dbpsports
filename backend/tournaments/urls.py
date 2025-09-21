# tournaments/urls.py
from django.urls import path
from . import views
from .views import tournaments_active

urlpatterns = [
    # --- URL Trang chủ & các trang tĩnh ---
    path('', views.home, name='home'),
    path('giai-dau/', tournaments_active, name='tournaments_active'),
    path('livestream/', views.livestream_view, name='livestream'),
    path('livestream/match/<int:pk>/', views.livestream_view, name='livestream_match'),

    path('shop/', views.shop_view, name='shop'),
    path('archive/', views.archive_view, name='archive'),

    path('dashboard/announcements/', views.announcement_dashboard, name='announcement_dashboard'),
    path('faq/', views.faq_view, name='faq'),
    
    # --- URL liên quan đến Giải đấu (Tournament) ---
    path('tournament/<int:pk>/', views.tournament_detail, name='tournament_detail'),
    path('tournament/<int:tournament_pk>/draw/', views.draw_groups_view, name='draw_groups'),
    path('tournament/<int:tournament_pk>/gallery/bulk-upload/', views.tournament_bulk_upload, name='tournament_bulk_upload'),
    path('tournament/<int:tournament_pk>/schedule/generate/', views.generate_schedule_view, name='generate_schedule'),
    
    # --- URL liên quan đến Đội bóng (Team) ---
    path('tournament/<int:tournament_pk>/create_team/', views.create_team, name='create_team'),
    path('team/<int:pk>/', views.team_detail, name='team_detail'),
    path('team/<int:pk>/update/', views.update_team, name='update_team'),
    path('team/<int:pk>/payment/', views.team_payment, name='team_payment'), # Dòng mới

    # --- URL liên quan đến Cầu thủ (Player) ---
    path('player/<int:pk>/claim/', views.claim_player_profile, name='claim_player_profile'),
    path('player/<int:pk>/', views.player_detail, name='player_detail'),
    path('player/<int:pk>/update/', views.update_player, name='update_player'),
    path('player/<int:pk>/delete/', views.delete_player, name='delete_player'),

    # --- URL liên quan đến Trận đấu (Match) ---
    path('match/<int:pk>/', views.match_detail, name='match_detail'),
    path('match/<int:pk>/print/', views.match_print_view, name='match_print'),
    path('match/<int:match_pk>/team/<int:team_pk>/manage_lineup/', views.manage_lineup, name='manage_lineup'),
]