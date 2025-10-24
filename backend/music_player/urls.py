from django.urls import path
from . import views
from . import admin_views
from . import user_music_views
from . import stats_views
from . import saved_music_apis
from . import youtube_import_views
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
    
    # ✅ Saved Music APIs
    path('saved/track/save/', saved_music_apis.save_track, name='save_track'),
    path('saved/track/unsave/', saved_music_apis.unsave_track, name='unsave_track'),
    path('saved/playlist/save/', saved_music_apis.save_playlist, name='save_playlist'),
    path('saved/playlist/unsave/', saved_music_apis.unsave_playlist, name='unsave_playlist'),
    path('saved/tracks/', saved_music_apis.get_saved_tracks, name='get_saved_tracks'),
    path('saved/playlists/', saved_music_apis.get_saved_playlists, name='get_saved_playlists'),
    path('saved/track/delete/', saved_music_apis.delete_saved_track, name='delete_saved_track'),
    path('saved/playlist/delete/', saved_music_apis.delete_saved_playlist, name='delete_saved_playlist'),
    path('saved/check-status/', saved_music_apis.check_saved_status, name='check_saved_status'),
    path('saved/playlist/<int:playlist_id>/tracks/', saved_music_apis.get_saved_tracks_for_playlist, name='get_saved_tracks_for_playlist'),
    
    # ✅ YouTube Import APIs
    path('youtube/import/', youtube_import_views.YouTubeImportView.as_view(), name='youtube_import'),
    path('youtube/info/', youtube_import_views.get_youtube_info, name='youtube_info'),
    path('youtube/progress/', youtube_import_views.get_youtube_import_progress, name='youtube_progress'),
    
    # Admin views
    path('admin/', admin_views.music_admin, name='admin'),
    path('admin/create-playlist/', admin_views.create_playlist, name='create_playlist'),
    path('admin/upload-music/<int:playlist_id>/', admin_views.upload_music_files, name='upload_music'),
    path('admin/scan-playlist/<int:playlist_id>/', admin_views.scan_playlist, name='admin_scan_playlist'),
    path('admin/delete-playlist/<int:playlist_id>/', admin_views.delete_playlist, name='delete_playlist'),
    path('admin/toggle-playlist/<int:playlist_id>/', admin_views.toggle_playlist_status, name='toggle_playlist_status'),
]
