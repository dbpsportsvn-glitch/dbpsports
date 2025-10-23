from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views import View
import json
import os
import logging
from .models import Playlist, Track, MusicPlayerSettings
from .utils import get_audio_duration

logger = logging.getLogger(__name__)


@method_decorator(csrf_exempt, name='dispatch')
class MusicPlayerAPIView(View):
    """API view cho Music Player"""
    
    def get(self, request):
        """Lấy danh sách playlist và tracks"""
        try:
            playlists = Playlist.objects.filter(is_active=True)
            playlists_data = []
            
            for playlist in playlists:
                tracks = playlist.get_tracks()
                tracks_data = []
                
                for track in tracks:
                    # Lấy tên file từ đường dẫn đầy đủ
                    import os
                    file_name = os.path.basename(track.file_path)
                    
                    tracks_data.append({
                        'id': track.id,
                        'title': track.title,
                        'artist': track.artist or '',
                        'album': track.album or '',
                        'album_cover': track.album_cover.url if track.album_cover else None,
                        'file_path': file_name,
                        'file_url': track.get_file_url(),
                        'duration': track.duration,
                        'duration_formatted': track.get_duration_formatted(),
                        'play_count': track.play_count,
                        'order': track.order
                    })
                
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
            
            # ✅ Thêm headers để disable cache
            response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
            response['Pragma'] = 'no-cache'
            response['Expires'] = '0'
            
            return response
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class MusicPlayerSettingsView(View):
    """API view để lấy cài đặt music player"""
    
    def get(self, request):
        """Lấy cài đặt của user hiện tại"""
        try:
            user = request.user
            
            if not user.is_authenticated:
                return JsonResponse({
                    'success': True,
                    'settings': {
                        'auto_play': True,
                        'volume': 0.7,
                        'repeat_mode': 'all',
                        'shuffle': False,
                        'listening_lock': False,
                        'low_power_mode': False,
                        'default_playlist_id': None
                    }
                })
            
            try:
                settings = MusicPlayerSettings.objects.get(user=user)
                settings_data = {
                    'auto_play': settings.auto_play,
                    'volume': settings.volume,
                    'repeat_mode': settings.repeat_mode,
                    'shuffle': settings.shuffle,
                    'listening_lock': settings.listening_lock,
                    'low_power_mode': settings.low_power_mode,
                    'default_playlist_id': settings.default_playlist.id if settings.default_playlist else None
                }
            except MusicPlayerSettings.DoesNotExist:
                settings_data = {
                    'auto_play': True,
                    'volume': 0.7,
                    'repeat_mode': 'all',
                    'shuffle': False,
                    'listening_lock': False,
                    'low_power_mode': False,
                    'default_playlist_id': None
                }
            
            return JsonResponse({
                'success': True,
                'settings': settings_data
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)
    
    def post(self, request):
        """Cập nhật cài đặt music player"""
        try:
            data = json.loads(request.body)
            user = request.user
            
            if not user.is_authenticated:
                return JsonResponse({
                    'success': False,
                    'error': 'User not authenticated'
                }, status=401)
            
            # Lấy hoặc tạo settings
            settings, created = MusicPlayerSettings.objects.get_or_create(user=user)
            
            # Cập nhật settings
            if 'auto_play' in data:
                settings.auto_play = data['auto_play']
            if 'volume' in data:
                settings.volume = max(0.0, min(1.0, float(data['volume'])))
            if 'repeat_mode' in data:
                settings.repeat_mode = data['repeat_mode']
            if 'shuffle' in data:
                settings.shuffle = data['shuffle']
            if 'listening_lock' in data:
                settings.listening_lock = bool(data['listening_lock'])
            if 'low_power_mode' in data:
                settings.low_power_mode = bool(data['low_power_mode'])
            if 'default_playlist_id' in data:
                try:
                    playlist = Playlist.objects.get(id=data['default_playlist_id'])
                    settings.default_playlist = playlist
                except Playlist.DoesNotExist:
                    pass
            
            settings.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Settings updated successfully'
            })
            
        except Exception as e:
            logger.error(f"Error updating music settings: {str(e)}", exc_info=True)
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)


def scan_playlist_folder(request, playlist_id):
    """Scan thư mục playlist và tự động thêm tracks"""
    try:
        playlist = Playlist.objects.get(id=playlist_id)
        folder_path = playlist.folder_path
        
        if not os.path.exists(folder_path):
            return JsonResponse({
                'success': False,
                'error': 'Folder not found'
            }, status=404)
        
        # Lấy danh sách file nhạc
        audio_extensions = ['.mp3', '.wav', '.ogg', '.m4a', '.aac']
        files = []
        
        for file in os.listdir(folder_path):
            if any(file.lower().endswith(ext) for ext in audio_extensions):
                files.append(file)
        
        files.sort()
        
        # Xóa tracks cũ
        Track.objects.filter(playlist=playlist).delete()
        
        # Thêm tracks mới
        for i, file in enumerate(files):
            # Tách tên file thành title và artist
            name_without_ext = os.path.splitext(file)[0]
            if ' - ' in name_without_ext:
                artist, title = name_without_ext.split(' - ', 1)
            else:
                artist = ''
                title = name_without_ext
            
            # Đường dẫn đầy đủ đến file
            full_file_path = os.path.join(folder_path, file)
            
            # Đọc duration từ file nhạc
            duration = get_audio_duration(full_file_path)
            
            Track.objects.create(
                playlist=playlist,
                title=title.strip(),
                artist=artist.strip() if artist else None,
                file_path=full_file_path,
                duration=duration,
                order=i + 1
            )
        
        return JsonResponse({
            'success': True,
            'message': f'Scanned {len(files)} tracks successfully',
            'tracks_count': len(files)
        })
        
    except Playlist.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Playlist not found'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)