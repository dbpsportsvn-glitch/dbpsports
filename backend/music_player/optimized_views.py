"""
Optimized Views cho Music Player
- Query optimization với prefetch_related
- Batched initial data endpoint
- Rate limiting
"""
from django.http import JsonResponse
from django.views.decorators.cache import cache_page
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods, require_POST
from django.contrib.auth.decorators import login_required
from django.views import View
from django.db.models import Prefetch
from django.core.cache import cache
from functools import wraps
import json
import os

from .models import Playlist, Track, MusicPlayerSettings, UserTrack, UserPlaylist


# ==========================================
# 1. Optimized Playlist API with Prefetch
# ==========================================

class OptimizedMusicPlayerAPIView(View):
    """
    ✅ OPTIMIZED VERSION - Giảm N+1 queries
    """
    
    @csrf_exempt
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)
    
    def get(self, request):
        try:
            # ✅ Prefetch related tracks để tránh N+1
            playlists = Playlist.objects.filter(
                is_active=True
            ).prefetch_related(
                Prefetch(
                    'tracks',
                    queryset=Track.objects.filter(
                        is_active=True
                    ).order_by('order').only(
                        'id', 'title', 'artist', 'album', 
                        'album_cover', 'file_path', 'duration', 
                        'play_count', 'order', 'playlist_id'
                    )
                )
            ).only(
                'id', 'name', 'description', 
                'cover_image', 'folder_path'
            )
            
            playlists_data = []
            
            for playlist in playlists:
                # ✅ Không trigger thêm query vì đã prefetch
                tracks = playlist.tracks.all()
                
                tracks_data = [
                    {
                        'id': track.id,
                        'title': track.title,
                        'artist': track.artist or '',
                        'album': track.album or '',
                        'album_cover': track.album_cover.url if track.album_cover else None,
                        'file_path': os.path.basename(track.file_path),
                        'file_url': track.get_file_url(),
                        'duration': track.duration,
                        'duration_formatted': track.get_duration_formatted(),
                        'play_count': track.play_count,
                        'order': track.order
                    }
                    for track in tracks
                ]
                
                playlists_data.append({
                    'id': playlist.id,
                    'name': playlist.name,
                    'description': playlist.description or '',
                    'cover_image': playlist.cover_image.url if playlist.cover_image else None,
                    'folder_path': os.path.basename(playlist.folder_path),
                    'tracks': tracks_data,
                    'tracks_count': len(tracks_data)
                })
            
            response = JsonResponse({
                'success': True,
                'playlists': playlists_data
            })
            
            # Disable cache
            response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
            response['Pragma'] = 'no-cache'
            response['Expires'] = '0'
            
            return response
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)


# ==========================================
# 2. Initial Data Endpoint (Batched)
# ==========================================

class InitialDataAPIView(View):
    """
    ✅ NEW: Single endpoint để load tất cả initial data
    Giảm từ 3-4 API calls xuống 1
    """
    
    @csrf_exempt
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)
    
    def get(self, request):
        try:
            user = request.user
            
            # Parallel queries với prefetch
            playlists = Playlist.objects.filter(
                is_active=True
            ).prefetch_related(
                Prefetch(
                    'tracks',
                    queryset=Track.objects.filter(is_active=True).order_by('order')
                )
            )
            
            # User settings (nếu authenticated)
            user_settings = None
            user_tracks = []
            user_playlists = []
            
            if user.is_authenticated:
                try:
                    user_settings = MusicPlayerSettings.objects.get(user=user)
                except MusicPlayerSettings.DoesNotExist:
                    # Create default settings
                    user_settings = MusicPlayerSettings.objects.create(
                        user=user,
                        auto_play=True,
                        volume=0.7,
                        repeat_mode='all',
                        shuffle=False,
                        storage_quota_mb=369
                    )
                
                # Limit to 50 most recent tracks
                user_tracks = UserTrack.objects.filter(
                    user=user,
                    is_active=True
                ).order_by('-created_at')[:50]
                
                # User playlists
                user_playlists = UserPlaylist.objects.filter(
                    user=user,
                    is_active=True
                ).order_by('-created_at')[:20]
            
            # Serialize data
            playlists_data = self._serialize_playlists(playlists)
            settings_data = self._serialize_settings(user_settings)
            user_tracks_data = self._serialize_user_tracks(user_tracks)
            user_playlists_data = self._serialize_user_playlists(user_playlists)
            
            response = JsonResponse({
                'success': True,
                'playlists': playlists_data,
                'settings': settings_data,
                'user_tracks': user_tracks_data,
                'user_playlists': user_playlists_data
            })
            
            response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
            return response
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)
    
    def _serialize_playlists(self, playlists):
        """Helper to serialize playlists"""
        result = []
        for playlist in playlists:
            tracks = playlist.tracks.all()
            result.append({
                'id': playlist.id,
                'name': playlist.name,
                'description': playlist.description or '',
                'cover_image': playlist.cover_image.url if playlist.cover_image else None,
                'folder_path': os.path.basename(playlist.folder_path),
                'tracks': [
                    {
                        'id': track.id,
                        'title': track.title,
                        'artist': track.artist or '',
                        'album': track.album or '',
                        'album_cover': track.album_cover.url if track.album_cover else None,
                        'file_path': os.path.basename(track.file_path),
                        'file_url': track.get_file_url(),
                        'duration': track.duration,
                        'duration_formatted': track.get_duration_formatted(),
                        'play_count': track.play_count,
                        'order': track.order
                    }
                    for track in tracks
                ],
                'tracks_count': len(tracks)
            })
        return result
    
    def _serialize_settings(self, settings):
        """Helper to serialize user settings"""
        if not settings:
            return {
                'auto_play': True,
                'volume': 0.7,
                'repeat_mode': 'all',
                'shuffle': False,
                'listening_lock': False,
                'low_power_mode': False,
                'storage_quota_mb': 369,
                'upload_usage': {
                    'used': 0,
                    'total': 369,
                    'remaining': 369,
                    'tracks_count': 0
                }
            }
        
        return {
            'auto_play': settings.auto_play,
            'volume': settings.volume,
            'repeat_mode': settings.repeat_mode,
            'shuffle': settings.shuffle,
            'listening_lock': settings.listening_lock,
            'low_power_mode': settings.low_power_mode,
            'storage_quota_mb': settings.storage_quota_mb,
            'upload_usage': settings.get_upload_usage()
        }
    
    def _serialize_user_tracks(self, tracks):
        """Helper to serialize user tracks"""
        return [
            {
                'id': track.id,
                'title': track.title,
                'artist': track.artist or '',
                'album': track.album or '',
                'album_cover': track.album_cover.url if track.album_cover else None,
                'duration': track.duration,
                'duration_formatted': track.get_duration_formatted(),
                'file_url': track.get_file_url(),
                'file_size': track.file_size,
                'file_size_formatted': track.get_file_size_formatted(),
                'play_count': track.play_count,
                'created_at': track.created_at.isoformat()
            }
            for track in tracks
        ]
    
    def _serialize_user_playlists(self, playlists):
        """Helper to serialize user playlists"""
        return [
            {
                'id': playlist.id,
                'name': playlist.name,
                'description': playlist.description or '',
                'cover_image': playlist.cover_image.url if playlist.cover_image else None,
                'tracks_count': playlist.get_tracks_count(),
                'is_public': playlist.is_public,
                'created_at': playlist.created_at.isoformat()
            }
            for playlist in playlists
        ]


# ==========================================
# 3. Rate Limiting Decorator
# ==========================================

def rate_limit(max_requests=10, window=60):
    """
    Rate limiting decorator
    max_requests: số requests tối đa
    window: thời gian window (seconds)
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapped(request, *args, **kwargs):
            if request.user.is_authenticated:
                key = f'rate_limit_{view_func.__name__}_{request.user.id}'
            else:
                # Use IP for anonymous users
                ip = request.META.get('REMOTE_ADDR', '')
                key = f'rate_limit_{view_func.__name__}_{ip}'
            
            current = cache.get(key, 0)
            
            if current >= max_requests:
                return JsonResponse({
                    'success': False,
                    'error': f'Quá nhiều requests. Vui lòng chờ {window} giây.'
                }, status=429)
            
            cache.set(key, current + 1, window)
            return view_func(request, *args, **kwargs)
        
        return wrapped
    return decorator

