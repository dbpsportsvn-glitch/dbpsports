"""
Views cho User Music Management
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods, require_POST
from django.core.files.storage import default_storage
from django.conf import settings as django_settings
from django.db import models
import os
import json
from mutagen import File as MutagenFile
from .models import UserTrack, UserPlaylist, UserPlaylistTrack, MusicPlayerSettings


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
                'upload_quota': 69,
                'storage_quota_mb': 500
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
                'upload_quota': user_settings.upload_quota,
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
            'duration': track.duration,
            'duration_formatted': track.get_duration_formatted(),
            'file_url': track.get_file_url(),
            'file_size': track.file_size,
            'file_size_formatted': track.get_file_size_formatted(),
            'created_at': track.created_at.isoformat()
        } for track in tracks]
        
        # Lấy usage
        user_settings, _ = MusicPlayerSettings.objects.get_or_create(
            user=request.user,
            defaults={'upload_quota': 69, 'storage_quota_mb': 500}
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


@login_required
@require_POST
def upload_user_track(request):
    """API endpoint để upload bài hát"""
    try:
        # Check quota
        user_settings, _ = MusicPlayerSettings.objects.get_or_create(
            user=request.user,
            defaults={'upload_quota': 69, 'storage_quota_mb': 500}
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
        
        # Validate file size (max 50MB per file)
        max_size = 50 * 1024 * 1024  # 50MB
        if uploaded_file.size > max_size:
            return JsonResponse({
                'success': False,
                'error': 'File quá lớn. Kích thước tối đa là 50MB.'
            }, status=400)
        
        # Check storage quota
        if not user_settings.can_upload(uploaded_file.size):
            usage = user_settings.get_upload_usage()
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
            
            # Delete temp file
            os.remove(temp_path)
            
        except Exception as e:
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
        
        return JsonResponse({
            'success': True,
            'message': 'Upload thành công!',
            'track': {
                'id': track.id,
                'title': track.title,
                'artist': track.artist,
                'album': track.album,
                'duration': track.duration,
                'duration_formatted': track.get_duration_formatted(),
                'file_url': track.get_file_url(),
                'file_size_formatted': track.get_file_size_formatted()
            },
            'usage': user_settings.get_upload_usage()
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@require_POST
def delete_user_track(request, track_id):
    """API endpoint để xóa bài hát"""
    try:
        track = get_object_or_404(UserTrack, id=track_id, user=request.user)
        track.delete()  # Will auto-delete file
        
        # Get updated usage
        user_settings, _ = MusicPlayerSettings.objects.get_or_create(
            user=request.user,
            defaults={'upload_quota': 69, 'storage_quota_mb': 500}
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
        data = json.loads(request.body)
        
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
        
        playlist = UserPlaylist.objects.create(
            user=request.user,
            name=data['name'],
            description=data.get('description', ''),
            is_public=data.get('is_public', False)
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Đã tạo playlist thành công',
            'playlist': {
                'id': playlist.id,
                'name': playlist.name,
                'description': playlist.description,
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

