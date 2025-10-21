"""
Backend Query Optimizations
Tối ưu N+1 queries và thêm caching
"""
from django.http import JsonResponse
from django.views.decorators.cache import cache_page
from django.views.decorators.csrf import csrf_exempt
from django.views import View
from django.db.models import Prefetch
import json


# ==========================================
# 1. Optimized Playlist API with Prefetch
# ==========================================

@csrf_exempt
class OptimizedMusicPlayerAPIView(View):
    """
    ✅ OPTIMIZED VERSION
    - Sử dụng prefetch_related để tránh N+1 queries
    - Select only needed fields
    - Single database roundtrip
    """
    
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
                        'play_count', 'order'
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

@csrf_exempt
class InitialDataAPIView(View):
    """
    ✅ NEW: Single endpoint để load tất cả initial data
    Giảm từ 3-4 API calls xuống 1
    """
    
    def get(self, request):
        try:
            user = request.user
            
            # Parallel queries
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
                    user_settings = None
                
                # Limit to 50 most recent tracks
                user_tracks = UserTrack.objects.filter(
                    user=user,
                    is_active=True
                ).order_by('-created_at')[:50]
                
                # User playlists
                user_playlists = UserPlaylist.objects.filter(
                    user=user,
                    is_active=True
                ).order_by('-created_at')
            
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
                'tracks': [
                    {
                        'id': track.id,
                        'title': track.title,
                        'artist': track.artist or '',
                        'album': track.album or '',
                        'album_cover': track.album_cover.url if track.album_cover else None,
                        'file_url': track.get_file_url(),
                        'duration': track.duration,
                        'play_count': track.play_count
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
                'storage_quota_mb': 369
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
                'file_url': track.get_file_url(),
                'file_size': track.file_size,
                'play_count': track.play_count
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
                'is_public': playlist.is_public
            }
            for playlist in playlists
        ]


# ==========================================
# 3. Cached User Playlists
# ==========================================

@cache_page(60)  # Cache 60 seconds
@login_required
@require_http_methods(["GET"])
def get_user_playlists_cached(request):
    """
    ✅ OPTIMIZED: Cached version
    Cache 60s để giảm load database
    """
    try:
        playlists = UserPlaylist.objects.filter(
            user=request.user,
            is_active=True
        ).order_by('-created_at')
        
        playlists_data = [
            {
                'id': playlist.id,
                'name': playlist.name,
                'description': playlist.description or '',
                'is_public': playlist.is_public,
                'tracks_count': playlist.get_tracks_count(),
                'created_at': playlist.created_at.isoformat()
            }
            for playlist in playlists
        ]
        
        return JsonResponse({
            'success': True,
            'playlists': playlists_data
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


# ==========================================
# 4. Paginated User Tracks
# ==========================================

@login_required
@require_http_methods(["GET"])
def get_user_tracks_paginated(request):
    """
    ✅ NEW: Paginated version
    Hỗ trợ pagination cho users có nhiều tracks
    """
    try:
        from django.core.paginator import Paginator
        
        page = int(request.GET.get('page', 1))
        per_page = int(request.GET.get('per_page', 50))
        
        tracks = UserTrack.objects.filter(
            user=request.user,
            is_active=True
        ).order_by('-created_at')
        
        paginator = Paginator(tracks, per_page)
        page_obj = paginator.get_page(page)
        
        tracks_data = [
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
            for track in page_obj
        ]
        
        # Get usage
        user_settings, _ = MusicPlayerSettings.objects.get_or_create(
            user=request.user,
            defaults={'upload_quota': 69, 'storage_quota_mb': 369}
        )
        usage = user_settings.get_upload_usage()
        
        return JsonResponse({
            'success': True,
            'tracks': tracks_data,
            'usage': usage,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total_pages': paginator.num_pages,
                'total_tracks': paginator.count,
                'has_next': page_obj.has_next(),
                'has_previous': page_obj.has_previous()
            }
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


# ==========================================
# 5. Rate Limiting Decorator
# ==========================================

from functools import wraps
from django.core.cache import cache
from django.http import HttpResponse

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


# Usage example:
@rate_limit(max_requests=10, window=60)
@login_required
@require_POST
def upload_user_track_rate_limited(request):
    """Upload với rate limiting"""
    # Existing upload code...
    pass


# ==========================================
# 6. URLs Configuration
# ==========================================

"""
# Thêm vào music_player/urls.py:

from .optimized_views import (
    OptimizedMusicPlayerAPIView,
    InitialDataAPIView,
    get_user_playlists_cached,
    get_user_tracks_paginated
)

urlpatterns = [
    # Optimized endpoints
    path('api/optimized/', OptimizedMusicPlayerAPIView.as_view(), name='optimized_api'),
    path('api/initial-data/', InitialDataAPIView.as_view(), name='initial_data'),
    path('user/playlists/cached/', get_user_playlists_cached, name='user_playlists_cached'),
    path('user/tracks/paginated/', get_user_tracks_paginated, name='user_tracks_paginated'),
]
"""

