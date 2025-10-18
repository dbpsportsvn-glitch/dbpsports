from django.urls import path
from . import views
from . import admin_views

app_name = 'music_player'

urlpatterns = [
    # API endpoints
    path('api/', views.MusicPlayerAPIView.as_view(), name='api'),
    path('api/settings/', views.MusicPlayerSettingsView.as_view(), name='settings'),
    path('api/scan-playlist/<int:playlist_id>/', views.scan_playlist_folder, name='scan_playlist'),
    
    # Admin views
    path('admin/', admin_views.music_admin, name='admin'),
    path('admin/create-playlist/', admin_views.create_playlist, name='create_playlist'),
    path('admin/upload-music/<int:playlist_id>/', admin_views.upload_music_files, name='upload_music'),
    path('admin/scan-playlist/<int:playlist_id>/', admin_views.scan_playlist, name='admin_scan_playlist'),
    path('admin/delete-playlist/<int:playlist_id>/', admin_views.delete_playlist, name='delete_playlist'),
    path('admin/toggle-playlist/<int:playlist_id>/', admin_views.toggle_playlist_status, name='toggle_playlist_status'),
]
