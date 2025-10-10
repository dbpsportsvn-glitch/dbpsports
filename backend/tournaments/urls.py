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
    path('transfer-market/', views.transfer_market_view, name='transfer_market'),
    path('transfer-history/', views.transfer_history_view, name='transfer_history'),

    path('jobs/', views.job_market_view, name='job_market'),
    path('jobs/<int:pk>/', views.job_detail_view, name='job_detail'),

    path('shop/', views.shop_view, name='shop'),
    path('archive/', views.archive_view, name='archive'),

    path('dashboard/announcements/', views.announcement_dashboard, name='announcement_dashboard'),
    path('faq/', views.faq_view, name='faq'),
    path('privacy-policy/', views.privacy_policy_view, name='privacy_policy'),
    path('terms-of-service/', views.terms_of_service_view, name='terms_of_service'),
    path('data-deletion-instructions/', views.data_deletion_view, name='data_deletion'),
    path('player/<int:player_pk>/cast_vote/', views.cast_vote_view, name='cast_vote'),
    path('tournament/<int:tournament_pk>/vote/', views.player_voting_view, name='player_voting'),

    # === BẮT ĐẦU KHỐI URL THÔNG BÁO ĐÃ CẬP NHẬT ===
    path('notifications/', views.notification_list, name='notification_list'),
    path('notifications/mark-all-as-read/', views.mark_all_notifications_as_read, name='mark_all_notifications_as_read'),
    path('notifications/<int:pk>/delete/', views.delete_notification, name='delete_notification'), # <-- Dòng quan trọng
    path('notifications/delete-all/', views.delete_all_notifications, name='delete_all_notifications'),
    
    # --- URL liên quan đến Giải đấu (Tournament) ---
    path('tournament/<int:pk>/', views.tournament_detail, name='tournament_detail'),
    path('tournament/<int:tournament_pk>/draw/', views.draw_groups_view, name='draw_groups'),
    path('tournament/<int:tournament_pk>/gallery/bulk-upload/', views.tournament_bulk_upload, name='tournament_bulk_upload'),
    path('tournament/<int:tournament_pk>/schedule/generate/', views.generate_schedule_view, name='generate_schedule'),
    path('tournament/<int:pk>/schedule/print/', views.tournament_schedule_print_view, name='tournament_schedule_print'),
    path('tournament/<int:pk>/toggle_follow/', views.toggle_follow_view, name='toggle_follow'),
    path('team/create_standalone/', views.create_standalone_team, name='create_standalone_team'),
    path('tournament/<int:tournament_pk>/create_team/', views.create_team, name='create_team'),    
    path('tournament/<int:tournament_pk>/media-dashboard/', views.media_dashboard, name='media_dashboard'),
    path('match/<int:pk>/media-edit/', views.media_edit_match, name='media_edit_match'),    
    # Nhà tài trợ
    path('sponsorship/<int:pk>/click/', views.record_sponsor_click_view, name='sponsor_click'),
    path('tournaments/<int:pk>/sponsorship-proposal/', views.sponsorship_proposal_view, name='sponsorship_proposal'),

    # --- URL liên quan đến Đội bóng (Team) ---
    path('tournament/<int:tournament_pk>/create_team/', views.create_team, name='create_team'),
    path('team/<int:pk>/', views.team_detail, name='team_detail'),
    path('team/<int:pk>/update/', views.update_team, name='update_team'),
    path('registration/<int:pk>/payment/', views.team_payment, name='team_payment'),
    path('team/<int:pk>/hall_of_fame/', views.team_hall_of_fame, name='team_hall_of_fame'),
    path('tournament/<int:tournament_pk>/register_team/<int:team_pk>/', views.register_existing_team, name='register_existing_team'),
    path('team/<int:pk>/profile/', views.public_team_detail, name='public_team_detail'),
    path('team/<int:team_pk>/cast_vote/', views.cast_team_vote_view, name='cast_team_vote'),
    path('team/<int:pk>/delete/', views.delete_team, name='delete_team'),

    # --- URL liên quan đến Cầu thủ (Player) ---
    path('player/<int:pk>/claim/', views.claim_player_profile, name='claim_player_profile'),
    path('player/<int:pk>/', views.player_detail, name='player_detail'),
    path('player/<int:pk>/update/', views.update_player, name='update_player'),
    path('player/<int:pk>/delete/', views.delete_player, name='delete_player'),
    path('team/<int:team_pk>/add_free_agent/<int:player_pk>/', views.add_free_agent, name='add_free_agent'),
    path('player/<int:player_pk>/invite_from/<int:team_pk>/', views.invite_player_view, name='invite_player'),
    path('transfers/<int:transfer_pk>/respond/', views.respond_to_transfer_view, name='respond_to_transfer'),
    path('scout/add/<int:player_pk>/from/<int:team_pk>/', views.add_to_scouting_list, name='add_to_scouting_list'),
    path('scout/remove/<int:scout_pk>/', views.remove_from_scouting_list, name='remove_from_scouting_list'),
    path('player/toggle-looking-for-club/', views.toggle_looking_for_club_view, name='toggle_looking_for_club'),    

    # --- URL liên quan đến Trận đấu (Match) ---
    path('match/<int:pk>/', views.match_detail, name='match_detail'),
    path('match/<int:pk>/print/', views.match_print_view, name='match_print'),
    path('match/<int:match_pk>/team/<int:team_pk>/manage_lineup/', views.manage_lineup, name='manage_lineup'),
    path('match/<int:pk>/control/', views.match_control_view, name='match_control'),
    path('match/<int:match_pk>/notes/commentator/', views.commentator_notes_view, name='commentator_notes'),
    path('match/<int:match_pk>/team/<int:team_pk>/notes/captain/', views.captain_note_view, name='captain_note'),
    path('events/<str:event_type>/<int:pk>/delete/', views.delete_match_event, name='delete_match_event'),
    
    # --- URL cho hệ thống quản lý tài chính ---
    path('tournament/<int:tournament_pk>/budget/', views.budget_dashboard, name='budget_dashboard'),
    path('tournament/<int:tournament_pk>/budget/setup/', views.budget_setup, name='budget_setup'),
    path('tournament/<int:tournament_pk>/budget/add-revenue/', views.add_revenue, name='add_revenue'),
    path('tournament/<int:tournament_pk>/budget/add-expense/', views.add_expense, name='add_expense'),
    path('tournament/<int:tournament_pk>/budget/quick-add/', views.quick_add_budget_item, name='quick_add_budget'),
    path('tournament/<int:tournament_pk>/budget/delete/<str:item_type>/<int:item_id>/', views.delete_budget_item, name='delete_budget_item'),
    path('tournament/<int:tournament_pk>/budget/refresh/', views.refresh_budget_auto, name='refresh_budget_auto'),
]