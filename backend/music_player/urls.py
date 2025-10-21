from django.urls import path
from . import views
from . import admin_views
from . import user_music_views
from . import stats_views
# Explicit import for optimized views
from .optimized_views import OptimizedMusicPlayerAPIView, InitialDataAPIView

app_name = 'music_player'

urlpatterns = [
    # ✅ Optimized API endpoints (NEW)
    path('api/initial-data/', InitialDataAPIView.as_view(), name='initial_data'),
    path('api/optimized/', OptimizedMusicPlayerAPIView.as_view(), name='optimized_api'),
    
    # API endpoints (legacy - keep for backward compatibility)
    path('api/', views.MusicPlayerAPIView.as_view(), name='api'),
    path('api/settings/', views.MusicPlayerSettingsView.as_view(), name='settings'),
    path('api/scan-playlist/<int:playlist_id>/', views.scan_playlist_folder, name='scan_playlist'),
    
    # User Music APIs
    path('user/settings/', user_music_views.user_music_settings, name='user_settings'),
    path('user/settings/update/', user_music_views.update_music_settings, name='update_settings'),
    path('user/tracks/', user_music_views.get_user_tracks, name='user_tracks'),
    path('user/tracks/upload/', user_music_views.upload_user_track, name='upload_track'),
    path('user/tracks/<int:track_id>/delete/', user_music_views.delete_user_track, name='delete_track'),
    path('user/tracks/<int:track_id>/update/', user_music_views.update_user_track, name='update_track'),
    path('user/playlists/', user_music_views.get_user_playlists, name='user_playlists'),
    path('user/playlists/create/', user_music_views.create_user_playlist, name='create_playlist'),
    path('user/playlists/<int:playlist_id>/tracks/', user_music_views.get_playlist_tracks, name='playlist_tracks'),
    path('user/playlists/<int:playlist_id>/add-track/<int:track_id>/', user_music_views.add_track_to_playlist, name='add_track_to_playlist'),
    path('user/playlists/<int:playlist_id>/delete/', user_music_views.delete_user_playlist, name='delete_playlist'),
    path('user/playlists/<int:playlist_id>/toggle-public/', user_music_views.toggle_playlist_public, name='toggle_playlist_public'),
    
    # Global Discovery APIs (Public Playlists)
    path('global/playlists/', user_music_views.get_public_playlists, name='public_playlists'),
    path('global/playlists/<int:playlist_id>/', user_music_views.get_public_playlist_detail, name='public_playlist_detail'),
    
    # Statistics APIs
    path('stats/record-play/', stats_views.record_track_play, name='record_play'),
    path('stats/user-stats/', stats_views.get_user_stats, name='user_stats'),
    path('stats/popular/', stats_views.get_popular_tracks, name='popular_tracks'),
    
    # Admin views
    path('admin/', admin_views.music_admin, name='admin'),
    path('admin/create-playlist/', admin_views.create_playlist, name='create_playlist'),
    path('admin/upload-music/<int:playlist_id>/', admin_views.upload_music_files, name='upload_music'),
    path('admin/scan-playlist/<int:playlist_id>/', admin_views.scan_playlist, name='admin_scan_playlist'),
    path('admin/delete-playlist/<int:playlist_id>/', admin_views.delete_playlist, name='delete_playlist'),
    path('admin/toggle-playlist/<int:playlist_id>/', admin_views.toggle_playlist_status, name='toggle_playlist_status'),
]
