"""
Views cho User Music Management
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods, require_POST
from django.views.decorators.cache import never_cache
from django.core.files.storage import default_storage
from django.conf import settings as django_settings
from django.db import models
from django.core.cache import cache
import os
import json
import logging
from functools import wraps
from mutagen import File as MutagenFile
from .models import UserTrack, UserPlaylist, UserPlaylistTrack, MusicPlayerSettings, Track, TrackPlayHistory
from .utils import extract_album_cover

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


@login_required
@require_http_methods(["GET"])
def user_music_settings(request):
    """API endpoint để lấy cài đặt music player của user"""
    try:
        user_settings, created = MusicPlayerSettings.objects.get_or_create(
            user=request.user,
            defaults={
                'auto_play': True,
                'volume': 0.7,
                'repeat_mode': 'all',
                'shuffle': False,
                'storage_quota_mb': 369
            }
        )
        
        usage = user_settings.get_upload_usage()
        
        return JsonResponse({
            'success': True,
            'settings': {
                'auto_play': user_settings.auto_play,
                'volume': user_settings.volume,
                'repeat_mode': user_settings.repeat_mode,
                'shuffle': user_settings.shuffle,
                'listening_lock': user_settings.listening_lock,
                'low_power_mode': user_settings.low_power_mode,
                'storage_quota_mb': user_settings.storage_quota_mb,
                'upload_usage': usage
            }
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@require_POST
def update_music_settings(request):
    """API endpoint để cập nhật cài đặt music player"""
    try:
        data = json.loads(request.body)
        user_settings, created = MusicPlayerSettings.objects.get_or_create(user=request.user)
        
        if 'auto_play' in data:
            user_settings.auto_play = data['auto_play']
        if 'volume' in data:
            user_settings.volume = float(data['volume'])
        if 'repeat_mode' in data:
            user_settings.repeat_mode = data['repeat_mode']
        if 'shuffle' in data:
            user_settings.shuffle = data['shuffle']
        if 'listening_lock' in data:
            user_settings.listening_lock = bool(data['listening_lock'])
        if 'low_power_mode' in data:
            user_settings.low_power_mode = bool(data['low_power_mode'])
        
        user_settings.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Đã cập nhật cài đặt thành công'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@require_http_methods(["GET"])
def get_user_tracks(request):
    """API endpoint để lấy danh sách bài hát của user"""
    try:
        tracks = UserTrack.objects.filter(
            user=request.user,
            is_active=True
        ).order_by('-created_at')
        
        tracks_data = [{
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
        } for track in tracks]
        
        # Lấy usage
        user_settings, _ = MusicPlayerSettings.objects.get_or_create(
            user=request.user,
            defaults={'storage_quota_mb': 369}
        )
        usage = user_settings.get_upload_usage()
        
        return JsonResponse({
            'success': True,
            'tracks': tracks_data,
            'usage': usage
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@rate_limit(max_requests=20, window=60)  # ✅ Max 20 uploads per minute
@login_required
@require_POST
def upload_user_track(request):
    """API endpoint để upload bài hát"""
    try:
        # Check quota
        user_settings, _ = MusicPlayerSettings.objects.get_or_create(
            user=request.user,
            defaults={'storage_quota_mb': 369}
        )
        
        # Get file from request
        if 'file' not in request.FILES:
            return JsonResponse({
                'success': False,
                'error': 'Không tìm thấy file'
            }, status=400)
        
        uploaded_file = request.FILES['file']
        
        # Validate file extension
        allowed_extensions = ['.mp3', '.m4a', '.aac', '.ogg', '.wav']
        file_extension = os.path.splitext(uploaded_file.name)[1].lower()
        if file_extension not in allowed_extensions:
            return JsonResponse({
                'success': False,
                'error': f'Định dạng file không được hỗ trợ. Chỉ chấp nhận: {", ".join(allowed_extensions)}'
            }, status=400)
        
        # ✅ Check storage quota before validating file size
        # Max file size = remaining quota của user
        usage = user_settings.get_upload_usage()
        remaining_bytes = usage['remaining'] * 1024 * 1024  # Convert MB to bytes
        
        if uploaded_file.size > remaining_bytes:
            max_size_mb = round(remaining_bytes / (1024 * 1024), 1)
            return JsonResponse({
                'success': False,
                'error': f'File quá lớn. Bạn còn {max_size_mb}MB quota. File của bạn là {round(uploaded_file.size / (1024 * 1024), 1)}MB.'
            }, status=400)
        
        # Double check quota
        if not user_settings.can_upload(uploaded_file.size):
            return JsonResponse({
                'success': False,
                'error': f'Bạn đã dùng {usage["used"]}MB/{usage["total"]}MB. Còn lại {usage["remaining"]}MB. Vui lòng xóa bớt để upload thêm.'
            }, status=400)
        
        # Extract metadata from file
        try:
            # Save temporarily to extract metadata
            temp_path = os.path.join(django_settings.MEDIA_ROOT, 'temp', uploaded_file.name)
            os.makedirs(os.path.dirname(temp_path), exist_ok=True)
            
            with open(temp_path, 'wb+') as destination:
                for chunk in uploaded_file.chunks():
                    destination.write(chunk)
            
            # Extract metadata using mutagen
            audio = MutagenFile(temp_path)
            duration = int(audio.info.length) if audio and audio.info else 0
            
            # Try to get title and artist from ID3 tags
            title = uploaded_file.name.rsplit('.', 1)[0]
            artist = ''
            album = ''
            
            if audio:
                # Try different tag formats
                if hasattr(audio, 'tags') and audio.tags:
                    # MP3/ID3
                    if 'TIT2' in audio.tags:
                        title = str(audio.tags['TIT2'])
                    if 'TPE1' in audio.tags:
                        artist = str(audio.tags['TPE1'])
                    if 'TALB' in audio.tags:
                        album = str(audio.tags['TALB'])
                    # M4A/MP4
                    elif '\xa9nam' in audio.tags:
                        title = str(audio.tags['\xa9nam'][0])
                    if '\xa9ART' in audio.tags:
                        artist = str(audio.tags['\xa9ART'][0])
                    if '\xa9alb' in audio.tags:
                        album = str(audio.tags['\xa9alb'][0])
            
            # Parse from filename if no tags (format: "Artist - Title")
            if not title or title == uploaded_file.name.rsplit('.', 1)[0]:
                name_without_ext = uploaded_file.name.rsplit('.', 1)[0]
                if ' - ' in name_without_ext:
                    parts = name_without_ext.split(' - ', 1)
                    artist = parts[0].strip()
                    title = parts[1].strip()
                else:
                    title = name_without_ext
            
            # Extract album cover
            album_cover_file = extract_album_cover(temp_path)
            
            # Delete temp file
            os.remove(temp_path)
            
        except Exception as e:
            album_cover_file = None
            # Error extracting metadata
            # Use filename as fallback
            name_without_ext = uploaded_file.name.rsplit('.', 1)[0]
            if ' - ' in name_without_ext:
                parts = name_without_ext.split(' - ', 1)
                artist = parts[0].strip()
                title = parts[1].strip()
            else:
                title = name_without_ext
            duration = 0
        
        # Create UserTrack
        track = UserTrack.objects.create(
            user=request.user,
            title=title,
            artist=artist,
            album=album,
            file=uploaded_file,
            file_size=uploaded_file.size,
            duration=duration
        )
        
        # Save album cover if extracted
        if album_cover_file:
            track.album_cover = album_cover_file
            track.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Upload thành công!',
            'track': {
                'id': track.id,
                'title': track.title,
                'artist': track.artist,
                'album': track.album,
                'album_cover': track.album_cover.url if track.album_cover else None,
                'duration': track.duration,
                'duration_formatted': track.get_duration_formatted(),
                'file_url': track.get_file_url(),
                'file_size_formatted': track.get_file_size_formatted()
            },
            'usage': user_settings.get_upload_usage()
        })
        
    except Exception as e:
        logger.error(f"Error uploading track: {str(e)}", exc_info=True)
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@require_POST
@never_cache
def delete_user_track(request, track_id):
    """API endpoint để xóa bài hát"""
    try:
        track = get_object_or_404(UserTrack, id=track_id, user=request.user)
        track.delete()  # Will auto-delete file
        
        # Get updated usage
        user_settings, _ = MusicPlayerSettings.objects.get_or_create(
            user=request.user,
            defaults={'storage_quota_mb': 369}
        )
        usage = user_settings.get_upload_usage()
        
        return JsonResponse({
            'success': True,
            'message': 'Đã xóa bài hát thành công',
            'usage': usage
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@require_POST
def update_user_track(request, track_id):
    """API endpoint để cập nhật thông tin bài hát"""
    try:
        track = get_object_or_404(UserTrack, id=track_id, user=request.user)
        data = json.loads(request.body)
        
        if 'title' in data:
            track.title = data['title']
        if 'artist' in data:
            track.artist = data['artist']
        if 'album' in data:
            track.album = data['album']
        
        track.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Đã cập nhật thông tin bài hát',
            'track': {
                'id': track.id,
                'title': track.title,
                'artist': track.artist,
                'album': track.album
            }
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@require_http_methods(["GET"])
def get_user_playlists(request):
    """API endpoint để lấy danh sách playlist của user"""
    try:
        playlists = UserPlaylist.objects.filter(
            user=request.user,
            is_active=True
        ).order_by('-created_at')
        
        playlists_data = []
        for playlist in playlists:
            try:
                playlists_data.append({
                    'id': playlist.id,
                    'name': playlist.name,
                    'description': playlist.description or '',
                    'is_public': playlist.is_public,
                    'tracks_count': playlist.get_tracks_count(),
                    'total_duration': playlist.get_total_duration(),
                    'created_at': playlist.created_at.isoformat()
                })
            except Exception as e:
                # Error processing playlist
                continue
        
        return JsonResponse({
            'success': True,
            'playlists': playlists_data
        })
    except Exception as e:
        import traceback
        # Error in get_user_playlists
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@require_POST
def create_user_playlist(request):
    """API endpoint để tạo playlist mới"""
    try:
        # Check if it's JSON or form data
        if request.content_type == 'application/json':
            data = json.loads(request.body)
            cover_image = None
        else:
            # Form data with file upload
            data = request.POST
            cover_image = request.FILES.get('cover_image')
        
        if not data.get('name'):
            return JsonResponse({
                'success': False,
                'error': 'Tên playlist không được để trống'
            }, status=400)
        
        # Check if playlist with same name exists
        existing = UserPlaylist.objects.filter(
            user=request.user,
            name=data['name']
        ).first()
        
        if existing:
            return JsonResponse({
                'success': False,
                'error': f'Bạn đã có playlist tên "{data["name"]}" rồi!'
            }, status=400)
        
        # ✅ Fix checkbox handling: HTML checkbox submits 'on' when checked, or absent when unchecked
        is_public_value = data.get('is_public', False)
        if isinstance(is_public_value, str):
            is_public = is_public_value.lower() in ['on', 'true', '1', 'yes']
        else:
            is_public = bool(is_public_value)
        
        playlist = UserPlaylist.objects.create(
            user=request.user,
            name=data['name'],
            description=data.get('description', ''),
            is_public=is_public,
            cover_image=cover_image
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Đã tạo playlist thành công',
            'playlist': {
                'id': playlist.id,
                'name': playlist.name,
                'description': playlist.description,
                'cover_image': playlist.cover_image.url if playlist.cover_image else None,
                'is_public': playlist.is_public
            }
        })
    except Exception as e:
        import traceback
        # Error in create_user_playlist
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@require_http_methods(["GET"])
@never_cache
def get_playlist_tracks(request, playlist_id):
    """API endpoint để lấy tracks trong playlist"""
    try:
        playlist = get_object_or_404(UserPlaylist, id=playlist_id, user=request.user)
        tracks = playlist.get_tracks()
        
        tracks_data = [{
            'id': track.user_track.id,
            'title': track.user_track.title,
            'artist': track.user_track.artist or '',
            'duration': track.user_track.duration,
            'duration_formatted': track.user_track.get_duration_formatted(),
            'file_url': track.user_track.get_file_url(),
            'play_count': track.user_track.play_count,  # ✅ Include play_count
            'order': track.order
        } for track in tracks]
        
        return JsonResponse({
            'success': True,
            'playlist': {
                'id': playlist.id,
                'name': playlist.name,
                'description': playlist.description
            },
            'tracks': tracks_data
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@require_POST
def add_track_to_playlist(request, playlist_id, track_id):
    """API endpoint để thêm track vào playlist"""
    try:
        playlist = get_object_or_404(UserPlaylist, id=playlist_id, user=request.user)
        track = get_object_or_404(UserTrack, id=track_id, user=request.user)
        
        # Check if track already in playlist
        existing = UserPlaylistTrack.objects.filter(
            playlist=playlist,
            user_track=track
        ).first()
        
        if existing:
            return JsonResponse({
                'success': False,
                'error': 'Bài hát đã có trong playlist này rồi!'
            }, status=400)
        
        # Add track to playlist
        max_order = playlist.tracks.aggregate(models.Max('order'))['order__max'] or 0
        UserPlaylistTrack.objects.create(
            playlist=playlist,
            user_track=track,
            order=max_order + 1
        )
        
        return JsonResponse({
            'success': True,
            'message': f'Đã thêm "{track.title}" vào playlist "{playlist.name}"'
        })
    except Exception as e:
        import traceback
        # Error in add_track_to_playlist
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@require_POST
def delete_user_playlist(request, playlist_id):
    """API endpoint để xóa playlist"""
    try:
        playlist = get_object_or_404(UserPlaylist, id=playlist_id, user=request.user)
        playlist_name = playlist.name
        playlist.delete()
        
        return JsonResponse({
            'success': True,
            'message': f'Đã xóa playlist "{playlist_name}" thành công'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@require_POST
def toggle_playlist_public(request, playlist_id):
    """API endpoint để toggle public/private cho playlist"""
    try:
        playlist = get_object_or_404(UserPlaylist, id=playlist_id, user=request.user)
        playlist.is_public = not playlist.is_public
        playlist.save()
        
        status = "công khai" if playlist.is_public else "riêng tư"
        return JsonResponse({
            'success': True,
            'message': f'Đã chuyển playlist "{playlist.name}" sang chế độ {status}',
            'is_public': playlist.is_public
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@require_http_methods(["GET"])
def get_public_playlists(request):
    """API endpoint để lấy danh sách public playlists (Global Discovery)"""
    try:
        # Get search query if provided
        search_query = request.GET.get('search', '').strip()
        
        # Base query: only public and active playlists
        playlists = UserPlaylist.objects.filter(
            is_public=True,
            is_active=True
        ).select_related('user')
        
        # Apply search filter if provided
        if search_query:
            playlists = playlists.filter(
                models.Q(name__icontains=search_query) |
                models.Q(description__icontains=search_query) |
                models.Q(user__username__icontains=search_query) |
                models.Q(user__first_name__icontains=search_query) |
                models.Q(user__last_name__icontains=search_query)
            )
        
        # Order by most recently updated
        playlists = playlists.order_by('-updated_at')[:100]  # Limit to 100
        
        playlists_data = []
        for playlist in playlists:
            try:
                # Get first track's album cover as playlist thumbnail
                first_track = playlist.tracks.filter(
                    user_track__is_active=True
                ).select_related('user_track').first()
                
                thumbnail = None
                if playlist.cover_image:
                    thumbnail = playlist.cover_image.url
                elif first_track and first_track.user_track.album_cover:
                    thumbnail = first_track.user_track.album_cover.url
                
                playlists_data.append({
                    'id': playlist.id,
                    'name': playlist.name,
                    'description': playlist.description or '',
                    'cover_image': thumbnail,
                    'tracks_count': playlist.get_tracks_count(),
                    'total_duration': playlist.get_total_duration(),
                    'owner': {
                        'username': playlist.user.username,
                        'full_name': playlist.user.get_full_name() or playlist.user.username,
                        'id': playlist.user.id
                    },
                    'created_at': playlist.created_at.isoformat(),
                    'updated_at': playlist.updated_at.isoformat()
                })
            except Exception as e:
                # Skip problematic playlists
                continue
        
        return JsonResponse({
            'success': True,
            'playlists': playlists_data,
            'count': len(playlists_data),
            'search_query': search_query
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@never_cache
@require_http_methods(["GET"])
def get_public_playlist_detail(request, playlist_id):
    """API endpoint để xem chi tiết public playlist (bao gồm cả admin và user playlists)"""
    try:
        # ✅ Thử lấy admin playlist trước (Playlist model)
        try:
            from .models import Playlist as AdminPlaylist
            
            admin_playlist = AdminPlaylist.objects.get(
                id=playlist_id,
                is_active=True
            )
            
            # Get tracks
            tracks = admin_playlist.get_tracks()
            
            tracks_data = []
            for track in tracks:
                tracks_data.append({
                    'id': track.id,
                    'title': track.title,
                    'artist': track.artist or '',
                    'album': track.album or '',
                    'album_cover': track.album_cover.url if track.album_cover else None,
                    'duration': track.duration,
                    'duration_formatted': track.get_duration_formatted(),
                    'file_url': track.get_file_url(),
                    'play_count': track.play_count,
                    'order': track.order
                })
            
            response = JsonResponse({
                'success': True,
                'playlist': {
                    'id': admin_playlist.id,
                    'name': admin_playlist.name,
                    'description': admin_playlist.description or '',
                    'cover_image': admin_playlist.cover_image.url if admin_playlist.cover_image else None,
                    'tracks_count': len(tracks_data),
                    'total_duration': sum(t.duration for t in tracks),
                    'owner': {
                        'username': 'admin',
                        'full_name': 'DBP Sports',
                        'id': 0
                    },
                    'created_at': admin_playlist.created_at.isoformat(),
                    'updated_at': admin_playlist.updated_at.isoformat()
                },
                'tracks': tracks_data
            })
            
            # ✅ Disable cache để luôn lấy data mới nhất
            response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
            response['Pragma'] = 'no-cache'
            response['Expires'] = '0'
            
            return response
        except AdminPlaylist.DoesNotExist:
            pass
        
        # ✅ Nếu không phải admin playlist, lấy user playlist
        playlist = get_object_or_404(
            UserPlaylist.objects.select_related('user'),
            id=playlist_id,
            is_public=True,
            is_active=True
        )
        
        # Get tracks
        tracks = playlist.tracks.filter(
            user_track__is_active=True
        ).select_related('user_track').order_by('order')
        
        tracks_data = []
        for track_entry in tracks:
            track = track_entry.user_track
            tracks_data.append({
                'id': track.id,
                'title': track.title,
                'artist': track.artist or '',
                'album': track.album or '',
                'album_cover': track.album_cover.url if track.album_cover else None,
                'duration': track.duration,
                'duration_formatted': track.get_duration_formatted(),
                'file_url': track.get_file_url(),
                'play_count': track.play_count,
                'order': track_entry.order
            })
        
        response = JsonResponse({
            'success': True,
            'playlist': {
                'id': playlist.id,
                'name': playlist.name,
                'description': playlist.description or '',
                'cover_image': playlist.cover_image.url if playlist.cover_image else None,
                'tracks_count': len(tracks_data),
                'total_duration': playlist.get_total_duration(),
                'owner': {
                    'username': playlist.user.username,
                    'full_name': playlist.user.get_full_name() or playlist.user.username,
                    'id': playlist.user.id
                },
                'created_at': playlist.created_at.isoformat(),
                'updated_at': playlist.updated_at.isoformat()
            },
            'tracks': tracks_data
        })
        
        # ✅ Disable cache để luôn lấy data mới nhất
        response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response['Pragma'] = 'no-cache'
        response['Expires'] = '0'
        
        return response
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

