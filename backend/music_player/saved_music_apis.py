"""
Saved Music APIs - Lưu bài hát và playlist yêu thích
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods, require_POST
from django.views.decorators.cache import never_cache
from django.core.cache import cache
import json
import logging
from functools import wraps
from .models import SavedTrack, SavedPlaylist, Track, UserTrack, Playlist, UserPlaylist, UserPlaylistTrack

logger = logging.getLogger(__name__)


# ✅ Rate limiting decorator
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


# ✅ Saved Music APIs
@login_required
@require_POST
@rate_limit(max_requests=20, window=60)
def save_track(request):
    """Lưu bài hát vào danh sách yêu thích và tự động tạo playlist"""
    try:
        data = json.loads(request.body)
        track_id = data.get('track_id')
        track_type = data.get('track_type', 'global')  # 'global' hoặc 'user'
        playlist_action = data.get('playlist_action', 'auto_create')  # 'auto_create', 'add_to_existing', 'create_new'
        existing_playlist_id = data.get('existing_playlist_id', None)
        new_playlist_name = data.get('new_playlist_name', None)
        
        if not track_id:
            return JsonResponse({
                'success': False,
                'error': 'Thiếu track_id'
            }, status=400)
        
        # Kiểm tra track đã được lưu chưa
        if track_type == 'global':
            existing = SavedTrack.objects.filter(
                user=request.user,
                global_track_id=track_id
            ).first()
            if existing:
                return JsonResponse({
                    'success': False,
                    'error': 'Bài hát đã được lưu rồi'
                }, status=400)
            
            track = get_object_or_404(Track, id=track_id, is_active=True)
            saved_track = SavedTrack.objects.create(
                user=request.user,
                global_track=track,
                track_title=track.title,
                track_artist=track.artist,
                track_album=track.album,
                track_duration=track.duration,
                track_type='global'
            )
        else:
            existing = SavedTrack.objects.filter(
                user=request.user,
                user_track_id=track_id
            ).first()
            if existing:
                return JsonResponse({
                    'success': False,
                    'error': 'Bài hát đã được lưu rồi'
                }, status=400)
            
            track = get_object_or_404(UserTrack, id=track_id, user=request.user)
            saved_track = SavedTrack.objects.create(
                user=request.user,
                user_track=track,
                track_title=track.title,
                track_artist=track.artist,
                track_album=track.album,
                track_duration=track.duration,
                track_type='user'
            )
        
        # ✅ Tự động tạo hoặc thêm vào playlist
        playlist = None
        
        # Chỉ hỗ trợ user tracks trong user playlists
        if track_type == 'user':
            if playlist_action == 'add_to_existing' and existing_playlist_id:
                # Thêm vào playlist có sẵn
                playlist = get_object_or_404(UserPlaylist, id=existing_playlist_id, user=request.user)
                
                # Kiểm tra track đã có trong playlist chưa
                existing_playlist_track = UserPlaylistTrack.objects.filter(
                    playlist=playlist,
                    user_track=track
                ).first()
                
                if not existing_playlist_track:
                    # Thêm track vào playlist
                    UserPlaylistTrack.objects.create(
                        playlist=playlist,
                        user_track=track,
                        order=playlist.tracks.count()
                    )
                    
            elif playlist_action == 'create_new' and new_playlist_name:
                # Tạo playlist mới
                playlist = UserPlaylist.objects.create(
                    user=request.user,
                    name=new_playlist_name,
                    description=f"Playlist tự động tạo từ bài hát đã lưu",
                    is_public=True  # Mặc định chia sẻ ra global
                )
                
                # Thêm track vào playlist mới
                UserPlaylistTrack.objects.create(
                    playlist=playlist,
                    user_track=track,
                    order=0
                )
                
            else:
                # Mặc định: tự động tạo playlist "Bài Hát Đã Lưu"
                playlist_name = "Bài Hát Đã Lưu"
                playlist, created = UserPlaylist.objects.get_or_create(
                    user=request.user,
                    name=playlist_name,
                    defaults={
                        'description': 'Playlist tự động tạo từ các bài hát đã lưu',
                        'is_public': True  # Mặc định chia sẻ ra global
                    }
                )
                
                # Kiểm tra track đã có trong playlist chưa
                existing_playlist_track = UserPlaylistTrack.objects.filter(
                    playlist=playlist,
                    user_track=track
                ).first()
                
                if not existing_playlist_track:
                    # Thêm track vào playlist
                    UserPlaylistTrack.objects.create(
                        playlist=playlist,
                        user_track=track,
                        order=playlist.tracks.count()
                    )
        else:
            # Đối với global tracks, chỉ tạo playlist trống để hiển thị
            # Global tracks sẽ được quản lý thông qua SavedTrack
            playlist_name = "Bài Hát Đã Lưu"
            playlist, created = UserPlaylist.objects.get_or_create(
                user=request.user,
                name=playlist_name,
                defaults={
                    'description': 'Playlist tự động tạo từ các bài hát đã lưu',
                    'is_public': True  # Mặc định chia sẻ ra global
                }
            )
        
        return JsonResponse({
            'success': True,
            'message': 'Đã lưu bài hát thành công',
            'saved_track_id': saved_track.id,
            'playlist_id': playlist.id if playlist else None,
            'playlist_name': playlist.name if playlist else None,
            'playlist_created': playlist_action in ['auto_create', 'create_new']
        })
        
    except Exception as e:
        logger.error(f"Error saving track: {e}", exc_info=True)
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@never_cache
def get_saved_tracks_for_playlist(request, playlist_id):
    """Lấy danh sách bài hát đã lưu cho playlist cụ thể"""
    try:
        playlist = get_object_or_404(UserPlaylist, id=playlist_id, user=request.user)
        
        # Nếu là playlist "Bài Hát Đã Lưu", lấy từ SavedTrack
        if playlist.name == "Bài Hát Đã Lưu":
            # Getting saved tracks for playlist
            saved_tracks = SavedTrack.objects.filter(user=request.user).select_related('global_track', 'user_track').order_by('-saved_at')
            # Found saved tracks
            
            tracks_data = []
            for saved_track in saved_tracks:
                # Lấy play count từ track gốc
                play_count = 0
                if saved_track.global_track:
                    play_count = saved_track.global_track.play_count or 0
                elif saved_track.user_track:
                    play_count = saved_track.user_track.play_count or 0
                
                track_data = {
                    'id': saved_track.global_track.id if saved_track.global_track else saved_track.user_track.id,
                    'type': saved_track.track_type,
                    'title': saved_track.track_title,
                    'artist': saved_track.track_artist or '',
                    'album': saved_track.track_album or '',
                    'duration': saved_track.track_duration,
                    'duration_formatted': f"{saved_track.track_duration // 60}:{saved_track.track_duration % 60:02d}",
                    'file_url': saved_track.get_track_url(),
                    'album_cover': saved_track.get_album_cover_url(),
                    'play_count': play_count  # ✅ Lấy từ track gốc
                }
                tracks_data.append(track_data)
            # Returning tracks data
        else:
            # Playlist thông thường, lấy từ UserPlaylistTrack
            playlist_tracks = playlist.tracks.all().order_by('order')
            
            tracks_data = []
            for playlist_track in playlist_tracks:
                user_track = playlist_track.user_track
                track_data = {
                    'id': user_track.id,
                    'type': 'user',
                    'title': user_track.title,
                    'artist': user_track.artist or '',
                    'album': user_track.album or '',
                    'duration': user_track.duration,
                    'duration_formatted': f"{user_track.duration // 60}:{user_track.duration % 60:02d}",
                    'file_url': user_track.get_file_url(),
                    'album_cover': user_track.album_cover.url if user_track.album_cover else None,
                    'play_count': user_track.play_count or 0
                }
                tracks_data.append(track_data)
        
        return JsonResponse({
            'success': True,
            'tracks': tracks_data,
            'playlist_name': playlist.name,
            'playlist_description': playlist.description
        })
        
    except Exception as e:
        logger.error(f"Error getting saved tracks for playlist: {e}", exc_info=True)
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@require_POST
@rate_limit(max_requests=20, window=60)
def unsave_track(request):
    """Bỏ lưu bài hát khỏi danh sách yêu thích"""
    try:
        data = json.loads(request.body)
        track_id = data.get('track_id')
        track_type = data.get('track_type', 'global')
        
        if not track_id:
            return JsonResponse({
                'success': False,
                'error': 'Thiếu track_id'
            }, status=400)
        
        # Tìm và xóa saved track
        if track_type == 'global':
            saved_track = SavedTrack.objects.filter(
                user=request.user,
                global_track_id=track_id
            ).first()
        else:
            saved_track = SavedTrack.objects.filter(
                user=request.user,
                user_track_id=track_id
            ).first()
        
        if not saved_track:
            return JsonResponse({
                'success': False,
                'error': 'Bài hát chưa được lưu'
            }, status=400)
        
        saved_track.delete()
        
        return JsonResponse({
            'success': True,
            'message': 'Đã bỏ lưu bài hát thành công'
        })
        
    except Exception as e:
        logger.error(f"Error unsaving track: {e}", exc_info=True)
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@require_POST
@rate_limit(max_requests=20, window=60)
def save_playlist(request):
    """Lưu playlist vào danh sách yêu thích"""
    try:
        data = json.loads(request.body)
        playlist_id = data.get('playlist_id')
        playlist_type = data.get('playlist_type', 'global')  # 'global' hoặc 'user'
        
        if not playlist_id:
            return JsonResponse({
                'success': False,
                'error': 'Thiếu playlist_id'
            }, status=400)
        
        # Kiểm tra playlist đã được lưu chưa
        if playlist_type == 'global':
            existing = SavedPlaylist.objects.filter(
                user=request.user,
                global_playlist_id=playlist_id
            ).first()
            if existing:
                return JsonResponse({
                    'success': False,
                    'error': 'Playlist đã được lưu rồi'
                }, status=400)
            
            playlist = get_object_or_404(Playlist, id=playlist_id, is_active=True)
            saved_playlist = SavedPlaylist.objects.create(
                user=request.user,
                global_playlist=playlist,
                playlist_name=playlist.name,
                playlist_description=playlist.description,
                playlist_type='global'
            )
        else:
            existing = SavedPlaylist.objects.filter(
                user=request.user,
                user_playlist__id=playlist_id
            ).first()
            if existing:
                return JsonResponse({
                    'success': False,
                    'error': 'Playlist đã được lưu rồi'
                }, status=400)
            
            playlist = get_object_or_404(UserPlaylist, id=playlist_id)
            saved_playlist = SavedPlaylist.objects.create(
                user=request.user,
                user_playlist=playlist,
                playlist_name=playlist.name,
                playlist_description=playlist.description,
                playlist_type='user'
            )
        
        return JsonResponse({
            'success': True,
            'message': 'Đã lưu playlist thành công',
            'saved_playlist_id': saved_playlist.id
        })
        
    except Exception as e:
        logger.error(f"Error saving playlist: {e}", exc_info=True)
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@require_POST
@rate_limit(max_requests=20, window=60)
def unsave_playlist(request):
    """Bỏ lưu playlist khỏi danh sách yêu thích"""
    try:
        data = json.loads(request.body)
        playlist_id = data.get('playlist_id')
        playlist_type = data.get('playlist_type', 'global')
        
        if not playlist_id:
            return JsonResponse({
                'success': False,
                'error': 'Thiếu playlist_id'
            }, status=400)
        
        # Tìm và xóa saved playlist
        if playlist_type == 'global':
            saved_playlist = SavedPlaylist.objects.filter(
                user=request.user,
                global_playlist__id=playlist_id
            ).first()
        else:
            saved_playlist = SavedPlaylist.objects.filter(
                user=request.user,
                user_playlist__id=playlist_id
            ).first()
        
        if not saved_playlist:
            return JsonResponse({
                'success': False,
                'error': 'Playlist chưa được lưu'
            }, status=400)
        
        saved_playlist.delete()
        
        return JsonResponse({
            'success': True,
            'message': 'Đã bỏ lưu playlist thành công'
        })
        
    except Exception as e:
        logger.error(f"Error unsaving playlist: {e}", exc_info=True)
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@never_cache
def get_saved_tracks(request):
    """Lấy danh sách bài hát đã lưu"""
    try:
        saved_tracks = SavedTrack.objects.filter(user=request.user).select_related('global_track', 'user_track').order_by('-saved_at')
        
        tracks_data = []
        for saved_track in saved_tracks:
            # Lấy play count từ track gốc
            play_count = 0
            if saved_track.global_track:
                play_count = saved_track.global_track.play_count or 0
            elif saved_track.user_track:
                play_count = saved_track.user_track.play_count or 0
            
            track_data = {
                'id': saved_track.id,
                'track_id': saved_track.global_track.id if saved_track.global_track else saved_track.user_track.id,
                'track_type': saved_track.track_type,
                'title': saved_track.track_title,
                'artist': saved_track.track_artist or '',
                'album': saved_track.track_album or '',
                'duration': saved_track.track_duration,
                'duration_formatted': f"{saved_track.track_duration // 60}:{saved_track.track_duration % 60:02d}",
                'saved_at': saved_track.saved_at.strftime('%Y-%m-%d %H:%M'),
                'file_url': saved_track.get_track_url(),
                'album_cover': saved_track.get_album_cover_url(),
                'play_count': play_count  # ✅ Lấy từ track gốc
            }
            tracks_data.append(track_data)
        
        return JsonResponse({
            'success': True,
            'tracks': tracks_data,
            'count': len(tracks_data)
        })
        
    except Exception as e:
        logger.error(f"Error getting saved tracks: {e}", exc_info=True)
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@never_cache
def get_saved_playlists(request):
    """Lấy danh sách playlist đã lưu"""
    try:
        saved_playlists = SavedPlaylist.objects.filter(user=request.user).select_related('global_playlist', 'user_playlist').order_by('-saved_at')
        
        playlists_data = []
        for saved_playlist in saved_playlists:
            playlist_data = {
                'id': saved_playlist.id,
                'playlist_id': saved_playlist.global_playlist.id if saved_playlist.global_playlist else saved_playlist.user_playlist.id,
                'playlist_type': saved_playlist.playlist_type,
                'name': saved_playlist.playlist_name,
                'description': saved_playlist.playlist_description or '',
                'tracks_count': saved_playlist.get_tracks_count(),
                'saved_at': saved_playlist.saved_at.strftime('%Y-%m-%d %H:%M'),
                'cover_image': saved_playlist.get_cover_image_url()
            }
            playlists_data.append(playlist_data)
        
        return JsonResponse({
            'success': True,
            'playlists': playlists_data,
            'count': len(playlists_data)
        })
        
    except Exception as e:
        logger.error(f"Error getting saved playlists: {e}", exc_info=True)
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@require_POST
@rate_limit(max_requests=10, window=60)
def delete_saved_track(request):
    """Xóa bài hát khỏi danh sách đã lưu"""
    try:
        data = json.loads(request.body)
        saved_track_id = data.get('saved_track_id')
        
        if not saved_track_id:
            return JsonResponse({
                'success': False,
                'error': 'Thiếu saved_track_id'
            }, status=400)
        
        saved_track = get_object_or_404(SavedTrack, id=saved_track_id, user=request.user)
        saved_track.delete()
        
        return JsonResponse({
            'success': True,
            'message': 'Đã xóa bài hát khỏi danh sách đã lưu'
        })
        
    except Exception as e:
        logger.error(f"Error deleting saved track: {e}", exc_info=True)
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@require_POST
@rate_limit(max_requests=10, window=60)
def delete_saved_playlist(request):
    """Xóa playlist khỏi danh sách đã lưu"""
    try:
        data = json.loads(request.body)
        saved_playlist_id = data.get('saved_playlist_id')
        
        if not saved_playlist_id:
            return JsonResponse({
                'success': False,
                'error': 'Thiếu saved_playlist_id'
            }, status=400)
        
        saved_playlist = get_object_or_404(SavedPlaylist, id=saved_playlist_id, user=request.user)
        saved_playlist.delete()
        
        return JsonResponse({
            'success': True,
            'message': 'Đã xóa playlist khỏi danh sách đã lưu'
        })
        
    except Exception as e:
        logger.error(f"Error deleting saved playlist: {e}", exc_info=True)
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@require_POST
@rate_limit(max_requests=20, window=60)
def check_saved_status(request):
    """Kiểm tra trạng thái đã lưu của tracks và playlists"""
    try:
        data = json.loads(request.body)
        tracks = data.get('tracks', [])  # List of {id, type}
        playlists = data.get('playlists', [])  # List of {id, type}
        
        result = {
            'tracks': {},
            'playlists': {}
        }
        
        # Check tracks status
        for track_info in tracks:
            track_id = track_info.get('id')
            track_type = track_info.get('type', 'global')
            
            if track_type == 'global':
                is_saved = SavedTrack.objects.filter(
                    user=request.user,
                    global_track__id=track_id
                ).exists()
            else:
                is_saved = SavedTrack.objects.filter(
                    user=request.user,
                    user_track__id=track_id
                ).exists()
            
            result['tracks'][f"{track_type}_{track_id}"] = is_saved
        
        # Check playlists status
        for playlist_info in playlists:
            playlist_id = playlist_info.get('id')
            playlist_type = playlist_info.get('type', 'global')
            
            if playlist_type == 'global':
                is_saved = SavedPlaylist.objects.filter(
                    user=request.user,
                    global_playlist__id=playlist_id
                ).exists()
            else:
                is_saved = SavedPlaylist.objects.filter(
                    user=request.user,
                    user_playlist__id=playlist_id
                ).exists()
            
            result['playlists'][f"{playlist_type}_{playlist_id}"] = is_saved
        
        return JsonResponse({
            'success': True,
            'saved_status': result
        })
        
    except Exception as e:
        logger.error(f"Error checking saved status: {e}", exc_info=True)
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)