"""
YouTube Import Views cho Music Player
Sử dụng yt-dlp để download audio từ YouTube videos/playlists
"""
import os
import tempfile
import logging
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views import View
from django.conf import settings
from django.core.files import File
from django.core.files.storage import default_storage
from django.db import transaction
import yt_dlp
from mutagen import File as MutagenFile
from mutagen.id3 import ID3, TIT2, TPE1, TALB, TDRC, APIC
from mutagen.mp3 import MP3
from .models import UserTrack, UserPlaylist, UserPlaylistTrack, MusicPlayerSettings
from .utils import get_audio_duration

logger = logging.getLogger(__name__)


def get_duration_formatted(duration):
    """Format duration from seconds to MM:SS"""
    if duration is None or duration == 0:
        return "00:00"
    minutes = duration // 60
    seconds = duration % 60
    return f"{minutes:02d}:{seconds:02d}"


class YouTubeImportView(View):
    """API view để import audio từ YouTube"""
    
    @method_decorator(csrf_exempt)
    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)
    
    def post(self, request):
        """Import audio từ YouTube URL"""
        try:
            data = json.loads(request.body)
            youtube_url = data.get('url', '').strip()
            playlist_id = data.get('playlist_id')
            extract_audio_only = data.get('extract_audio_only', True)
            
            if not youtube_url:
                return JsonResponse({
                    'success': False,
                    'error': 'YouTube URL không được để trống'
                }, status=400)
            
            # Validate YouTube URL
            if not self._is_valid_youtube_url(youtube_url):
                return JsonResponse({
                    'success': False,
                    'error': 'URL không hợp lệ. Vui lòng nhập URL YouTube video hoặc playlist'
                }, status=400)
            
            # Detect if it's a playlist URL
            is_playlist = '?list=' in youtube_url or '/playlist' in youtube_url
            if is_playlist:
                logger.info(f"Detected playlist URL: {youtube_url}")
            else:
                logger.info(f"Detected single video URL: {youtube_url}")
            
            # Check user quota
            user_settings = MusicPlayerSettings.objects.get_or_create(user=request.user)[0]
            if not user_settings.can_upload(0):  # We'll check actual size after download
                return JsonResponse({
                    'success': False,
                    'error': f'Bạn đã sử dụng hết quota ({user_settings.storage_quota_mb}MB). Vui lòng liên hệ admin để mở rộng.'
                }, status=400)
            
            # Import từ YouTube
            result = self._import_from_youtube(
                request.user, 
                youtube_url, 
                playlist_id, 
                extract_audio_only
            )
            
            return JsonResponse(result)
            
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'error': 'Dữ liệu JSON không hợp lệ'
            }, status=400)
        except Exception as e:
            logger.error(f"YouTube import error: {str(e)}", exc_info=True)
            return JsonResponse({
                'success': False,
                'error': f'Lỗi khi import: {str(e)}'
            }, status=500)
    
    def _is_valid_youtube_url(self, url):
        """Kiểm tra URL YouTube có hợp lệ không"""
        youtube_domains = [
            'youtube.com', 'www.youtube.com', 'm.youtube.com',
            'youtu.be', 'www.youtu.be'
        ]
        
        for domain in youtube_domains:
            if domain in url:
                return True
        return False
    
    def _import_from_youtube(self, user, url, playlist_id, extract_audio_only):
        """Import audio từ YouTube URL"""
        try:
            # Tạo thư mục temp để download
            with tempfile.TemporaryDirectory() as temp_dir:
                # Cấu hình yt-dlp
                ydl_opts = {
                    'format': 'bestaudio[ext=m4a]/bestaudio/best',
                    'outtmpl': os.path.join(temp_dir, '%(title)s.%(ext)s'),
                    'writethumbnail': True,
                    'writedescription': True,
                    'writeinfojson': True,
                    'ignoreerrors': True,  # Continue on errors
                    'no_warnings': True,
                    'noplaylist': False,  # Allow playlist download
                    'timeout': 30,        # 30 second timeout
                }
                
                # Thêm postprocessor chỉ khi có FFmpeg
                try:
                    import subprocess
                    result = subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True, timeout=5)
                    # FFmpeg có sẵn, thêm postprocessor
                    ydl_opts['postprocessors'] = [{
                        'key': 'FFmpegExtractAudio',
                        'preferredcodec': 'mp3',
                        'preferredquality': '192',
                    }]
                    logger.info("FFmpeg found, will convert to MP3")
                except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
                    # FFmpeg không có, sử dụng format gốc
                    logger.warning("FFmpeg not found, using original format")
                    ydl_opts['format'] = 'bestaudio/best'
                    # Remove postprocessors if they exist
                    if 'postprocessors' in ydl_opts:
                        del ydl_opts['postprocessors']
                
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    # Extract info trước khi download
                    info = ydl.extract_info(url, download=False)
                    
                    if not info:
                        return {
                            'success': False,
                            'error': 'Không thể lấy thông tin từ YouTube URL'
                        }
                    
                    # Xử lý single video hoặc playlist
                    if 'entries' not in info:
                        return self._process_single_video(user, ydl, info, playlist_id, temp_dir)
                    else:
                        return self._process_playlist(user, ydl, info, playlist_id, temp_dir)
                    
        except Exception as e:
            logger.error(f"YouTube import processing error: {str(e)}", exc_info=True)
            return {
                'success': False,
                'error': f'Lỗi khi xử lý: {str(e)}'
            }
    
    def _process_single_video(self, user, ydl, info, playlist_id, temp_dir):
        """Xử lý single video"""
        try:
            # Tạo album từ single video nếu chưa có playlist_id
            created_album = None
            if not playlist_id:
                album_name = f"{info.get('uploader', 'Unknown Artist')} - Single"
                created_album = self._create_album_from_playlist(user, album_name, info)
                if created_album:
                    playlist_id = created_album.id
                    logger.info(f"Created album for single video: {created_album.name} (ID: {created_album.id})")
            
            # Download video
            ydl.download([info['webpage_url']])
            
            # Tìm file đã download
            downloaded_files = [f for f in os.listdir(temp_dir) if f.endswith(('.mp3', '.webm', '.m4a'))]
            
            if not downloaded_files:
                return {
                    'success': False,
                    'error': 'Không thể download audio từ video'
                }
            
            audio_file = os.path.join(temp_dir, downloaded_files[0])
            
            # Tạo UserTrack
            track = self._create_user_track(user, info, audio_file, playlist_id, None)
            
            if track:
                return {
                    'success': True,
                    'message': f'Import thành công: {track.title}',
                    'track': {
                        'id': track.id,
                        'title': track.title,
                        'artist': track.artist,
                        'album': track.album,
                        'duration': track.duration,
                        'file_size': track.file_size
                    },
                    'album': {
                        'id': created_album.id if created_album else playlist_id,
                        'name': created_album.name if created_album else 'Existing Playlist',
                        'created': created_album is not None
                    } if created_album or playlist_id else None
                }
            else:
                return {
                    'success': False,
                    'error': 'Không thể tạo track từ file audio'
                }
                
        except Exception as e:
            logger.error(f"Single video processing error: {str(e)}", exc_info=True)
            return {
                'success': False,
                'error': f'Lỗi khi xử lý video: {str(e)}'
            }
    
    def _process_playlist(self, user, ydl, info, playlist_id, temp_dir):
        """Xử lý playlist"""
        try:
            entries = info.get('entries', [])
            if not entries:
                return {
                    'success': False,
                    'error': 'Playlist không có video nào'
                }
            
            # Tạo album (playlist) từ YouTube playlist nếu chưa có playlist_id
            created_album = None
            if not playlist_id:
                album_name = info.get('title', 'YouTube Import')
                created_album = self._create_album_from_playlist(user, album_name, info)
                if created_album:
                    playlist_id = created_album.id
                    logger.info(f"Created album: {created_album.name} (ID: {created_album.id})")
            
            # Download tất cả videos trong playlist
            ydl.download([info['webpage_url']])
            
            # Tìm tất cả files đã download (ưu tiên mp3)
            all_files = os.listdir(temp_dir)
            downloaded_files = []
            
            # Ưu tiên mp3 files, sau đó m4a, cuối cùng là webm
            mp3_files = [f for f in all_files if f.endswith('.mp3')]
            m4a_files = [f for f in all_files if f.endswith('.m4a')]
            webm_files = [f for f in all_files if f.endswith('.webm')]
            
            if mp3_files:
                downloaded_files = mp3_files
                logger.info("Using MP3 files")
            elif m4a_files:
                downloaded_files = m4a_files
                logger.info("Using M4A files (no MP3 conversion)")
            else:
                downloaded_files = webm_files
                logger.info("Using WEBM files (no conversion)")
            
            logger.info(f"Found downloaded files: {downloaded_files}")
            
            if not downloaded_files:
                return {
                    'success': False,
                    'error': 'Không thể download audio từ playlist'
                }
            
            # Tạo tracks cho tất cả files
            created_tracks = []
            errors = []
            
            logger.info(f"Processing {len(downloaded_files)} downloaded files: {downloaded_files}")
            
            for i, filename in enumerate(downloaded_files):
                try:
                    audio_file = os.path.join(temp_dir, filename)
                    logger.info(f"Processing file {i+1}/{len(downloaded_files)}: {filename}")
                    
                    # Lấy info từ file info.json nếu có
                    info_file = os.path.join(temp_dir, filename.replace('.webm', '.info.json').replace('.mp3', '.info.json').replace('.m4a', '.info.json'))
                    video_info = None
                    
                    if os.path.exists(info_file):
                        try:
                            # Check if file is empty
                            if os.path.getsize(info_file) == 0:
                                logger.warning(f"Empty info.json for {filename}")
                                video_info = None
                            else:
                                # Try different encodings
                                for encoding in ['utf-8', 'utf-8-sig', 'latin-1', 'cp1252']:
                                    try:
                                        with open(info_file, 'r', encoding=encoding) as f:
                                            content = f.read().strip()
                                            if content:  # Check if content is not empty
                                                video_info = json.loads(content)
                                                logger.info(f"Loaded video info for {filename} with {encoding}: {video_info.get('title', 'Unknown')}")
                                                break
                                            else:
                                                logger.warning(f"Empty content in info.json for {filename}")
                                                video_info = None
                                    except (UnicodeDecodeError, json.JSONDecodeError):
                                        continue
                                if not video_info:
                                    logger.warning(f"Could not decode info.json for {filename}")
                        except Exception as e:
                            logger.warning(f"Error reading info.json for {filename}: {e}")
                            video_info = None
                    else:
                        logger.warning(f"No info.json found for {filename}")
                        video_info = None
                    
                    # Tạo UserTrack với playlist info làm album
                    track = self._create_user_track(user, video_info, audio_file, playlist_id, info)
                    
                    if track:
                        created_tracks.append({
                            'id': track.id,
                            'title': track.title,
                            'artist': track.artist,
                            'album': track.album,
                            'duration': track.duration,
                            'file_size': track.file_size
                        })
                        logger.info(f"Successfully created track: {track.title}")
                    else:
                        logger.error(f"Failed to create track for {filename}")
                        errors.append(f"Không thể tạo track cho {filename}")
                    
                except Exception as e:
                    error_msg = f"Lỗi với file {filename}: {str(e)}"
                    errors.append(error_msg)
                    logger.error(f"Playlist track processing error for {filename}: {str(e)}", exc_info=True)
            
            return {
                'success': True,
                'message': f'Import thành công {len(created_tracks)}/{len(downloaded_files)} tracks từ playlist',
                'tracks': created_tracks,
                'errors': errors if errors else None,
                'album': {
                    'id': created_album.id if created_album else playlist_id,
                    'name': created_album.name if created_album else 'Existing Playlist',
                    'created': created_album is not None
                } if created_album or playlist_id else None,
                'debug_info': {
                    'downloaded_files': downloaded_files,
                    'created_count': len(created_tracks),
                    'error_count': len(errors)
                }
            }
            
        except Exception as e:
            logger.error(f"Playlist processing error: {str(e)}", exc_info=True)
            return {
                'success': False,
                'error': f'Lỗi khi xử lý playlist: {str(e)}'
            }
    
    def _create_album_from_playlist(self, user, album_name, playlist_info):
        """Tạo album (playlist) từ YouTube playlist"""
        try:
            from .models import UserPlaylist
            
            # Tạo tên album unique
            base_name = album_name
            counter = 1
            while UserPlaylist.objects.filter(user=user, name=album_name).exists():
                album_name = f"{base_name} ({counter})"
                counter += 1
            
            # Tạo album
            album = UserPlaylist.objects.create(
                user=user,
                name=album_name,
                description=f"Album được tạo từ YouTube playlist: {playlist_info.get('title', 'Unknown')}",
                is_public=False,
                is_active=True
            )
            
            logger.info(f"Created album '{album_name}' for user {user.username}")
            return album
            
        except Exception as e:
            logger.error(f"Error creating album: {str(e)}", exc_info=True)
            return None
    
    def _create_user_track(self, user, video_info, audio_file_path, playlist_id, playlist_info=None):
        """Tạo UserTrack từ file audio và metadata"""
        try:
            logger.info(f"Creating UserTrack for file: {audio_file_path}")
            
            # Lấy metadata từ video info hoặc filename
            if video_info:
                title = video_info.get('title', 'Unknown Title')
                uploader = video_info.get('uploader', 'Unknown Artist')
                upload_date = video_info.get('upload_date', '')
                logger.info(f"Using video info - Title: {title}, Uploader: {uploader}")
            else:
                # Fallback: extract từ filename
                filename = os.path.basename(audio_file_path)
                title, uploader = self._extract_metadata_from_filename(filename)
                upload_date = ''
                logger.info(f"Using filename fallback - Title: {title}, Uploader: {uploader}")
            
            # Clean title (loại bỏ ký tự không hợp lệ)
            title = self._clean_title(title)
            
            # Tạo album name từ playlist hoặc uploader
            if playlist_info:
                album = playlist_info.get('title', 'YouTube Playlist')
                logger.info(f"Using playlist as album: {album}")
                logger.info(f"Playlist info keys: {list(playlist_info.keys()) if playlist_info else 'None'}")
            else:
                album = f"{uploader} - {upload_date[:4]}" if upload_date else uploader
                logger.info(f"Using uploader as album: {album}")
                logger.info(f"No playlist info provided")
            
            # Đọc file size
            file_size = os.path.getsize(audio_file_path)
            logger.info(f"File size: {file_size / (1024*1024):.2f}MB")
            
            # Check quota trước khi tạo track
            user_settings = MusicPlayerSettings.objects.get(user=user)
            if not user_settings.can_upload(file_size):
                error_msg = f'File quá lớn ({file_size / (1024*1024):.2f}MB). Quota còn lại: {user_settings.get_upload_usage()["remaining"]:.2f}MB'
                logger.error(error_msg)
                raise Exception(error_msg)
            
            logger.info(f"Quota check passed. Creating track...")
            
            # Đọc duration từ file
            duration = self._get_audio_duration(audio_file_path)
            
            # Tạo filename an toàn
            safe_filename = self._create_safe_filename(title, uploader)
            
            # Upload file
            with open(audio_file_path, 'rb') as f:
                django_file = File(f, name=safe_filename)
                
                with transaction.atomic():
                    # Tạo UserTrack
                    track = UserTrack.objects.create(
                        user=user,
                        title=title,
                        artist=uploader,
                        album=album,
                        file=django_file,
                        file_size=file_size,
                        duration=duration,
                        is_active=True
                    )
                    
                    # Thêm vào playlist nếu có
                    if playlist_id:
                        try:
                            playlist = UserPlaylist.objects.get(id=playlist_id, user=user)
                            UserPlaylistTrack.objects.create(
                                playlist=playlist,
                                user_track=track,
                                order=playlist.tracks.count() + 1
                            )
                        except UserPlaylist.DoesNotExist:
                            logger.warning(f"Playlist {playlist_id} not found for user {user.username}")
                    
                    logger.info(f"Successfully created UserTrack: {track.title} (ID: {track.id})")
                    return track
                    
        except Exception as e:
            logger.error(f"Create user track error: {str(e)}", exc_info=True)
            return None
    
    def _extract_metadata_from_filename(self, filename):
        """Extract title và artist từ filename"""
        try:
            # Remove extension
            name = os.path.splitext(filename)[0]
            
            # Common patterns in YouTube filenames
            patterns = [
                r'^(.+?)\s*-\s*(.+?)\s*ft\s*(.+)$',  # "Title - Artist ft Other"
                r'^(.+?)\s*-\s*(.+)$',                # "Title - Artist"
                r'^(.+?)\s*by\s*(.+)$',              # "Title by Artist"
                r'^(.+?)\s*\|\s*(.+)$',              # "Title | Artist"
            ]
            
            import re
            for pattern in patterns:
                match = re.match(pattern, name, re.IGNORECASE)
                if match:
                    if len(match.groups()) == 3:  # "Title - Artist ft Other"
                        title = match.group(1).strip()
                        artist = f"{match.group(2).strip()} ft {match.group(3).strip()}"
                    else:  # "Title - Artist" or "Title by Artist"
                        title = match.group(1).strip()
                        artist = match.group(2).strip()
                    
                    # Clean up common YouTube suffixes
                    title = re.sub(r'\s*Official\s*MV.*$', '', title, flags=re.IGNORECASE)
                    title = re.sub(r'\s*4K.*$', '', title, flags=re.IGNORECASE)
                    title = re.sub(r'\s*HD.*$', '', title, flags=re.IGNORECASE)
                    
                    return title, artist
            
            # Fallback: use filename as title
            return name, 'Unknown Artist'
            
        except Exception as e:
            logger.warning(f"Error extracting metadata from filename {filename}: {e}")
            return filename, 'Unknown Artist'
    
    def _clean_title(self, title):
        """Làm sạch title"""
        # Loại bỏ ký tự không hợp lệ
        import re
        title = re.sub(r'[<>:"/\\|?*]', '', title)
        title = title.strip()
        
        # Giới hạn độ dài
        if len(title) > 200:
            title = title[:200].strip()
        
        return title or 'Unknown Title'
    
    def _create_safe_filename(self, title, artist):
        """Tạo filename an toàn"""
        import re
        from datetime import datetime
        
        # Combine title và artist
        filename = f"{artist} - {title}" if artist else title
        
        # Loại bỏ ký tự không hợp lệ
        filename = re.sub(r'[<>:"/\\|?*]', '', filename)
        filename = re.sub(r'[^\w\s-]', '', filename)
        filename = re.sub(r'[-\s]+', '_', filename)
        filename = filename.strip('_')
        
        # Giới hạn độ dài
        if len(filename) > 100:
            filename = filename[:100].strip('_')
        
        # Thêm timestamp để tránh trùng
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{filename}_{timestamp}.mp3"
        
        return filename
    
    def _get_audio_duration(self, file_path):
        """Lấy duration từ file audio"""
        try:
            from mutagen import File as MutagenFile
            audio_file = MutagenFile(file_path)
            if audio_file and hasattr(audio_file, 'info'):
                return int(audio_file.info.length)
        except Exception as e:
            logger.warning(f"Could not get duration from {file_path}: {e}")
        
        # Fallback: sử dụng get_audio_duration từ utils
        try:
            return get_audio_duration(file_path)
        except Exception as e:
            logger.warning(f"Fallback duration extraction failed: {e}")
            return 180  # Default 3 minutes


@csrf_exempt
@require_POST
@login_required
def get_youtube_import_progress(request):
    """API endpoint để lấy tiến trình import"""
    try:
        # Tạm thời return progress giả
        # TODO: Implement real progress tracking
        return JsonResponse({
            'success': True,
            'progress': 50,
            'status': 'downloading',
            'message': 'Đang download audio...'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@csrf_exempt
@require_POST
@login_required
def get_youtube_info(request):
    """Lấy thông tin video/playlist từ YouTube URL mà không download"""
    try:
        data = json.loads(request.body)
        url = data.get('url', '').strip()
        
        if not url:
            return JsonResponse({
                'success': False,
                'error': 'URL không được để trống'
            }, status=400)
        
        # Detect if it's a playlist URL
        is_playlist = '?list=' in url or '/playlist' in url
        if is_playlist:
            logger.info(f"Detected playlist URL: {url}")
        else:
            logger.info(f"Detected single video URL: {url}")
        
        # Cấu hình yt-dlp để extract info (hỗ trợ cả video và playlist)
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'noplaylist': False,  # Allow playlist info extraction
            'extract_flat': False, # Extract full info for better metadata
            'timeout': 15,        # 15 second timeout
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            if not info:
                return JsonResponse({
                    'success': False,
                    'error': 'Không thể lấy thông tin từ URL'
                }, status=400)
            
            # Xử lý single video
            if 'entries' not in info:
                return JsonResponse({
                    'success': True,
                    'info': {
                        'type': 'video',
                        'id': info.get('id'),
                        'title': info.get('title', 'Unknown'),
                        'uploader': info.get('uploader', 'Unknown'),
                        'duration': info.get('duration', 0),
                        'duration_formatted': get_duration_formatted(info.get('duration', 0)),
                        'thumbnail': info.get('thumbnail', ''),
                        'webpage_url': info.get('webpage_url', url),
                    }
                })
            
            # Xử lý playlist
            entries = info.get('entries', [])
            videos_info = []
            
            logger.info(f"Playlist info: {info.get('title', 'Unknown')} with {len(entries)} entries")
            
            for entry in entries[:10]:  # Chỉ lấy 10 videos đầu để preview
                if entry:
                    # Handle both flat and full extraction
                    if isinstance(entry, dict):
                        video_data = {
                            'id': entry.get('id'),
                            'title': entry.get('title', 'Unknown'),
                            'uploader': entry.get('uploader', 'Unknown'),
                            'duration': entry.get('duration', 0),
                            'duration_formatted': get_duration_formatted(entry.get('duration', 0)),
                            'thumbnail': entry.get('thumbnail', ''),
                            'webpage_url': entry.get('url', entry.get('webpage_url', '')),
                        }
                    else:
                        # Fallback for flat extraction
                        video_data = {
                            'id': str(entry),
                            'title': 'Unknown',
                            'uploader': 'Unknown',
                            'duration': 0,
                            'duration_formatted': '00:00',
                            'thumbnail': '',
                            'webpage_url': '',
                        }
                    
                    videos_info.append(video_data)
            
            return JsonResponse({
                'success': True,
                'info': {
                    'type': 'playlist',
                    'id': info.get('id'),
                    'title': info.get('title', 'Unknown Playlist'),
                    'uploader': info.get('uploader', 'Unknown'),
                    'entry_count': len(entries),
                    'thumbnail': info.get('thumbnail', ''),
                    'webpage_url': info.get('webpage_url', url),
                    'entries': videos_info,
                }
            })
            
    except Exception as e:
        logger.error(f"YouTube info extraction error: {str(e)}", exc_info=True)
        return JsonResponse({
            'success': False,
            'error': f'Lỗi khi lấy thông tin: {str(e)}'
        }, status=500)
