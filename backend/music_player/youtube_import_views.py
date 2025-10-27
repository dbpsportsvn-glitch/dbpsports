"""
YouTube Import Views cho Music Player
Sử dụng yt-dlp để download audio từ YouTube videos/playlists
"""
import os
import tempfile
import logging
import json
import urllib.request
import threading
import time
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
from django.core.files.base import ContentFile
from django.utils import timezone
from io import BytesIO
from PIL import Image
import yt_dlp
from mutagen import File as MutagenFile
from mutagen.id3 import ID3, TIT2, TPE1, TALB, TDRC, APIC
from mutagen.mp3 import MP3
from .models import UserTrack, UserPlaylist, UserPlaylistTrack, MusicPlayerSettings
from .utils import get_audio_duration

logger = logging.getLogger(__name__)

# Global dictionary to track active import sessions
# Key: user_id, Value: {'cancelled': bool, 'thread': threading.Thread, 'progress': dict}
active_imports = {}
import_lock = threading.Lock()


def start_import_session(user_id):
    """Bắt đầu một import session mới"""
    with import_lock:
        active_imports[user_id] = {
            'cancelled': False,
            'thread': None,
            'progress': {'status': 'starting', 'message': 'Đang khởi tạo...', 'percentage': 0},
            'start_time': time.time()
        }
        logger.info(f"Started import session for user {user_id}")


def cancel_import_session(user_id):
    """Hủy import session của user"""
    with import_lock:
        if user_id in active_imports:
            active_imports[user_id]['cancelled'] = True
            logger.info(f"Cancelled import session for user {user_id}")
            return True
        return False


def is_import_cancelled(user_id):
    """Kiểm tra xem import có bị hủy không"""
    with import_lock:
        return active_imports.get(user_id, {}).get('cancelled', False)


def update_import_progress(user_id, status, message, percentage=0):
    """Cập nhật tiến trình import"""
    with import_lock:
        if user_id in active_imports:
            active_imports[user_id]['progress'] = {
                'status': status,
                'message': message,
                'percentage': percentage
            }


def get_import_progress(user_id):
    """Lấy tiến trình import hiện tại"""
    with import_lock:
        return active_imports.get(user_id, {}).get('progress', {})


def end_import_session(user_id):
    """Kết thúc import session"""
    with import_lock:
        if user_id in active_imports:
            del active_imports[user_id]
            logger.info(f"Ended import session for user {user_id}")


def download_and_process_thumbnail(thumbnail_url, max_size=(512, 512), quality=85):
    """
    Download thumbnail từ URL và resize/optimize
    
    Args:
        thumbnail_url: URL của thumbnail
        max_size: Kích thước tối đa (width, height)
        quality: JPEG quality (0-100)
        
    Returns:
        BytesIO: BytesIO chứa image đã được optimize, hoặc None nếu lỗi
    """
    try:
        print(f"🔍 DEBUG download_and_process_thumbnail: thumbnail_url={thumbnail_url}")
        logger.info(f"🔍 DEBUG download_and_process_thumbnail: thumbnail_url={thumbnail_url}")
        
        if not thumbnail_url:
            print("❌ DEBUG: thumbnail_url is empty")
            logger.warning("thumbnail_url is empty")
            return None
        
        # Download thumbnail
        with urllib.request.urlopen(thumbnail_url, timeout=10) as response:
            image_data = response.read()
        
        if not image_data:
            logger.warning("Empty thumbnail data")
            return None
        
        # Open và resize image
        img = Image.open(BytesIO(image_data))
        
        # Convert RGBA/LA/P to RGB if needed
        if img.mode in ('RGBA', 'LA', 'P'):
            background = Image.new('RGB', img.size, (255, 255, 255))
            if img.mode == 'P':
                img = img.convert('RGBA')
            background.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
            img = background
        
        # Resize nếu cần
        if img.width > max_size[0] or img.height > max_size[1]:
            img.thumbnail(max_size, Image.Resampling.LANCZOS)
        
        # Save to BytesIO
        output = BytesIO()
        img.save(output, format='JPEG', quality=quality)
        output.seek(0)
        
        logger.info(f"Thumbnail downloaded and processed: {img.width}x{img.height}, {len(output.getvalue())} bytes")
        return output
        
    except Exception as e:
        logger.error(f"Error downloading thumbnail: {str(e)}", exc_info=True)
        return None


def attach_thumbnail_to_track(track, thumbnail_url):
    """
    Attach thumbnail vào track
    
    Args:
        track: UserTrack instance
        thumbnail_url: URL của thumbnail từ YouTube
        
    Returns:
        bool: True nếu thành công, False nếu lỗi
    """
    try:
        print(f"🔍 DEBUG attach_thumbnail_to_track: track={track.id if track else None}, thumbnail_url={thumbnail_url}")
        logger.info(f"🔍 DEBUG attach_thumbnail_to_track: track={track.id if track else None}, thumbnail_url={thumbnail_url}")
        
        if not thumbnail_url or not track:
            print(f"❌ DEBUG: Missing thumbnail_url or track. thumbnail_url={thumbnail_url}, track={track}")
            logger.warning(f"Missing thumbnail_url or track. thumbnail_url={thumbnail_url}, track={track}")
            return False
        
        # Download và process thumbnail
        thumbnail_io = download_and_process_thumbnail(thumbnail_url)
        if not thumbnail_io:
            print("❌ DEBUG: Could not download thumbnail for track")
            logger.warning("Could not download thumbnail for track")
            return False
        
        # Create filename - sử dụng ID nếu có, hoặc title nếu chưa có ID
        if track.id:
            filename = f"album_cover_{track.id}.jpg"
        else:
            # Fallback: use title for filename
            import re
            safe_title = re.sub(r'[<>:"/\\|?*]', '', track.title)[:50]
            filename = f"album_cover_{safe_title}.jpg"
        
        # Save to track's album_cover field
        track.album_cover.save(filename, ContentFile(thumbnail_io.read()), save=True)
        
        logger.info(f"✅ Thumbnail attached to track: {track.title}")
        return True
        
    except Exception as e:
        logger.error(f"Error attaching thumbnail to track: {str(e)}", exc_info=True)
        return False


def attach_thumbnail_to_playlist(playlist, thumbnail_url):
    """
    Attach thumbnail vào playlist/album
    
    Args:
        playlist: UserPlaylist instance
        thumbnail_url: URL của thumbnail từ YouTube
        
    Returns:
        bool: True nếu thành công, False nếu lỗi
    """
    try:
        if not thumbnail_url or not playlist:
            return False
        
        # Download và process thumbnail
        thumbnail_io = download_and_process_thumbnail(thumbnail_url)
        if not thumbnail_io:
            logger.warning("Could not download thumbnail for playlist")
            return False
        
        # Create filename
        filename = f"playlist_cover_{playlist.id}.jpg"
        
        # Save to playlist's cover_image field
        playlist.cover_image.save(filename, ContentFile(thumbnail_io.read()), save=True)
        
        logger.info(f"Thumbnail attached to playlist: {playlist.name}")
        return True
        
    except Exception as e:
        logger.error(f"Error attaching thumbnail to playlist: {str(e)}", exc_info=True)
        return False


def _get_cookie_file_path(user=None):
    """Lấy đường dẫn cookie file, ưu tiên cookie của user, fallback về cookie mặc định"""
    # Ưu tiên cookie của user nếu có
    if user:
        try:
            from .models import UserYouTubeCookie
            user_cookie = UserYouTubeCookie.objects.filter(user=user, is_active=True).first()
            if user_cookie and user_cookie.is_cookie_valid():
                cookie_path = user_cookie.get_cookie_file_path()
                if cookie_path and os.path.exists(cookie_path):
                    logger.info(f"Using user cookie file: {cookie_path}")
                    return cookie_path
        except Exception as e:
            logger.warning(f"Error accessing user cookie: {e}")
    
    # Fallback về cookie file mặc định
    default_cookie_path = os.path.join(settings.BASE_DIR, 'music_player', 'youtube_cookies.txt')
    if os.path.exists(default_cookie_path):
        logger.info(f"Using default cookie file: {default_cookie_path}")
        return default_cookie_path
    
    logger.warning("No valid cookie file found")
    return None


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
            import_playlist = data.get('import_playlist', False)  # Mặc định: import file đơn lẻ
            
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
            
            # ✅ Lưu original URL để logging
            original_url = youtube_url
            
            # Detect if it's a playlist URL (phân biệt playlist thực sự vs video với radio mode)
            import re
            # Playlist thực sự: có /playlist hoặc có list= với playlist ID (không phải radio mode RD...)
            has_list_param = bool(re.search(r'[?&]list=', youtube_url))
            is_radio_mode = bool(re.search(r'[?&]list=RD', youtube_url))
            is_playlist = '/playlist' in youtube_url or (has_list_param and not is_radio_mode)
            
            # ✅ Special handling for radio mode - always treat as single video
            if is_radio_mode:
                logger.info("Radio mode detected in import - treating as single video")
                is_playlist = False
                # Clean radio mode parameters immediately - improved regex
                youtube_url = re.sub(r'[?&]list=[^&]*', '', youtube_url)
                youtube_url = re.sub(r'[?&]start_radio=[^&]*', '', youtube_url)
                youtube_url = re.sub(r'[?&]index=[^&]*', '', youtube_url)
                youtube_url = re.sub(r'[?&]+$', '', youtube_url)
                youtube_url = re.sub(r'\?$', '', youtube_url)  # Remove trailing ?
                logger.info(f"Radio mode URL cleaned in import: {original_url} -> {youtube_url}")
            
            # Xử lý logic import dựa trên checkbox
            if is_radio_mode and not import_playlist:
                # Radio mode và không muốn import playlist - đã clean URL ở trên
                logger.info("Radio mode with single video import - URL already cleaned")
            elif is_playlist and not import_playlist:
                # URL là playlist nhưng user không muốn import playlist
                # Chuyển thành single video bằng cách loại bỏ playlist parameter
                if '?list=' in youtube_url:
                    youtube_url = youtube_url.split('?list=')[0]
                elif '/playlist' in youtube_url:
                    # Không thể chuyển playlist URL thành single video
                    return JsonResponse({
                        'success': False,
                        'error': 'URL này là playlist. Vui lòng tick "Import cả playlist" hoặc sử dụng URL video đơn lẻ.'
                    }, status=400)
            elif not is_playlist and import_playlist:
                # URL là single video nhưng user muốn import playlist
                return JsonResponse({
                    'success': False,
                    'error': 'URL này là video đơn lẻ. Bỏ tick "Import cả playlist" để import video này.'
                }, status=400)
            
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
                extract_audio_only,
                import_playlist
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
    
    def _check_ffmpeg(self):
        """Kiểm tra FFmpeg có sẵn không"""
        try:
            import subprocess
            result = subprocess.run(['ffmpeg', '-version'], 
                                  capture_output=True, text=True, timeout=5)
            return result.returncode == 0
        except:
            return False
    
    def _import_from_youtube(self, user, url, playlist_id, extract_audio_only, import_playlist=False):
        """Import audio từ YouTube URL"""
        user_id = user.id
        
        try:
            # Bắt đầu import session
            start_import_session(user_id)
            update_import_progress(user_id, 'preparing', 'Đang chuẩn bị download...', 10)
            
            # Kiểm tra cancel trước khi bắt đầu
            if is_import_cancelled(user_id):
                logger.info(f"Import cancelled before starting for user {user_id}")
                return {
                    'success': False,
                    'error': 'Import đã bị hủy',
                    'cancelled': True
                }
            
            # Tạo thư mục temp để download
            with tempfile.TemporaryDirectory() as temp_dir:
                
                # Custom progress hook để kiểm tra cancel
                def progress_hook(d):
                    if is_import_cancelled(user_id):
                        logger.info(f"Import cancelled during download for user {user_id}")
                        raise Exception("Import cancelled by user")
                    
                    if d['status'] == 'downloading':
                        # Cập nhật progress
                        downloaded_bytes = d.get('downloaded_bytes', 0)
                        total_bytes = d.get('total_bytes', 0)
                        if total_bytes > 0:
                            percentage = min(90, int((downloaded_bytes / total_bytes) * 80) + 10)  # 10-90%
                            update_import_progress(user_id, 'downloading', f'Đang download... {percentage}%', percentage)
                        else:
                            update_import_progress(user_id, 'downloading', 'Đang download...', 50)
                    elif d['status'] == 'finished':
                        update_import_progress(user_id, 'processing', 'Đang xử lý file...', 90)
                
                # Cấu hình yt-dlp với tối ưu chống bot detection
                ydl_opts = {
                    # Format sẽ được set sau khi kiểm tra FFmpeg
                    'outtmpl': os.path.join(temp_dir, '%(title)s.%(ext)s'),
                    'writethumbnail': False,  # Disable để tránh lỗi
                    'writedescription': False,  # Disable để tránh lỗi
                    'writeinfojson': True,  # ✅ Enable để lấy metadata cho thumbnails
                    'ignoreerrors': True,  # Continue on errors
                    'no_warnings': True,
                    'noplaylist': False,  # Allow playlist download
                    'timeout': 60,        # Tăng timeout lên 60s
                    'progress_hooks': [progress_hook],  # ✅ Thêm progress hook để cancel
                    
                    # ✅ Format sorting - ưu tiên audio formats
                    'format_sort': ['ext:m4a', 'ext:webm', 'ext:mp3', 'ext:ogg', 'ext:mp4'],
                    'format_sort_force': True,
                    
                    # ✅ Anti-bot detection optimizations
                    'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'referer': 'https://www.youtube.com/',
                    'http_headers': {
                        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                        'Accept-Language': 'en-US,en;q=0.5',
                        'Accept-Encoding': 'gzip, deflate',
                        'DNT': '1',
                        'Connection': 'keep-alive',
                        'Upgrade-Insecure-Requests': '1',
                    },
                    
                    # ✅ Rate limiting và retry logic
                    'retries': 3,
                    'fragment_retries': 3,
                    'retry_sleep_functions': {'http': lambda n: min(4 ** n, 60)},
                    
                    # ✅ Cookie support với fallback
                    'cookiefile': _get_cookie_file_path(user) if os.path.exists(_get_cookie_file_path(user)) else None,
                    
                    # ✅ Throttling để tránh spam
                    'sleep_interval': 1,
                    'max_sleep_interval': 5,
                    
                    # ✅ Extract info optimizations
                    'extract_flat': False,
                    'writesubtitles': False,
                    'writeautomaticsub': False,
                }
                
                # ✅ PRODUCTION OPTIMIZATION: Kiểm tra FFmpeg một lần và quyết định strategy
                ffmpeg_available = self._check_ffmpeg()
                logger.info(f"🔍 [FFmpeg Check] FFmpeg available: {ffmpeg_available}")
                print(f"🔍 [FFmpeg Check] FFmpeg available: {ffmpeg_available}")
                
                if ffmpeg_available:
                    # Local environment với FFmpeg - sử dụng postprocessors để convert sang MP3
                    logger.info("✅ [Strategy] Using FFmpeg postprocessors for MP3 conversion")
                    print("✅ [Strategy] Using FFmpeg postprocessors for MP3 conversion")
                    ydl_opts['postprocessors'] = [{
                        'key': 'FFmpegExtractAudio',
                        'preferredcodec': 'mp3',
                        'preferredquality': '192',
                    }]
                else:
                    # Production environment không có FFmpeg - download trực tiếp audio streams
                    logger.info("⚠️ [Strategy] No FFmpeg - downloading audio from available formats")
                    print("⚠️ [Strategy] No FFmpeg - downloading audio from available formats")
                    
                    # Loại bỏ các tham số không tương thích với không có FFmpeg
                    ydl_opts.pop('audioformat', None)
                    ydl_opts.pop('audioquality', None)
                    ydl_opts.pop('extractaudio', None)
                    
                    # Xóa postprocessors hoàn toàn
                    ydl_opts.pop('postprocessors', None)
                    
                    # Format selection: Đơn giản nhất - chỉ lấy best format có sẵn
                    # Không filter gì cả - để đảm bảo download được
                    ydl_opts['format'] = 'best'
                    
                    logger.info("✅ [Strategy] Audio download configured (may include video)")
                    print("✅ [Strategy] Audio download configured (may include video)")
                
                # Debug logging
                logger.info(f"🔍 [Config] ydl_opts format: {ydl_opts.get('format', 'N/A')}")
                logger.info(f"🔍 [Config] ydl_opts postprocessors: {ydl_opts.get('postprocessors', [])}")
                print(f"🔍 [Config] ydl_opts format: {ydl_opts.get('format', 'N/A')}")
                print(f"🔍 [Config] ydl_opts postprocessors: {ydl_opts.get('postprocessors', [])}")
                
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    # Extract info trước khi download
                    logger.info(f"🔍 [Extract Info] Extracting info from URL: {url}")
                    print(f"🔍 [Extract Info] Extracting info from URL: {url}")
                    info = ydl.extract_info(url, download=False)
                    
                    if not info:
                        logger.error("❌ [Extract Info] Failed to extract info from YouTube URL")
                        print("❌ [Extract Info] Failed to extract info from YouTube URL")
                        return {
                            'success': False,
                            'error': 'Không thể lấy thông tin từ YouTube URL'
                        }
                    
                    logger.info(f"✅ [Extract Info] Info extracted successfully. Title: {info.get('title', 'N/A')}")
                    print(f"✅ [Extract Info] Info extracted successfully. Title: {info.get('title', 'N/A')}")
                    
                    # Log available formats
                    formats = info.get('formats', [])
                    logger.info(f"📊 [Extract Info] Available formats count: {len(formats)}")
                    print(f"📊 [Extract Info] Available formats count: {len(formats)}")
                    
                    # Log first 5 formats để debug
                    if formats:
                        logger.info(f"📊 [Extract Info] First 5 formats:")
                        print(f"📊 [Extract Info] First 5 formats:")
                        for fmt in formats[:5]:
                            format_id = fmt.get('format_id', 'N/A')
                            ext = fmt.get('ext', 'N/A')
                            acodec = fmt.get('acodec', 'N/A')
                            vcodec = fmt.get('vcodec', 'N/A')
                            logger.info(f"  - Format {format_id}: ext={ext}, acodec={acodec}, vcodec={vcodec}")
                            print(f"  - Format {format_id}: ext={ext}, acodec={acodec}, vcodec={vcodec}")
                    
                    # Kiểm tra cancel trước khi xử lý
                    if is_import_cancelled(user_id):
                        logger.info(f"Import cancelled before processing for user {user_id}")
                        return {
                            'success': False,
                            'error': 'Import đã bị hủy',
                            'cancelled': True
                        }
                    
                    # Xử lý single video hoặc playlist dựa trên import_playlist
                    if 'entries' not in info or not import_playlist:
                        result = self._process_single_video(user, ydl, info, playlist_id, temp_dir, ydl_opts)
                    else:
                        result = self._process_playlist(user, ydl, info, playlist_id, temp_dir)
                    
                    # Kiểm tra cancel sau khi xử lý
                    if is_import_cancelled(user_id):
                        logger.info(f"Import cancelled after processing for user {user_id}")
                        return {
                            'success': False,
                            'error': 'Import đã bị hủy',
                            'cancelled': True
                        }
                    
                    # Cập nhật progress hoàn thành
                    update_import_progress(user_id, 'completed', 'Import hoàn thành!', 100)
                    return result
                    
        except Exception as e:
            logger.error(f"YouTube import processing error: {str(e)}", exc_info=True)
            
            # Kiểm tra nếu lỗi do cancel
            if is_import_cancelled(user_id):
                return {
                    'success': False,
                    'error': 'Import đã bị hủy',
                    'cancelled': True
                }
            
            return {
                'success': False,
                'error': f'Lỗi khi xử lý: {str(e)}'
            }
        finally:
            # Cleanup session
            end_import_session(user_id)
    
    def _process_single_video(self, user, ydl, info, playlist_id, temp_dir, ydl_opts):
        """Xử lý single video"""
        try:
            # Tạo album từ single video nếu chưa có playlist_id
            created_album = None
            if not playlist_id:
                album_name = f"{info.get('uploader', 'Unknown Artist')} - Single"
                created_album = self._create_album_from_playlist(user, album_name, info)
                if created_album:
                    playlist_id = created_album.id
            
            # Download video với error handling và fallback
            logger.info(f"🚀 [Download] Starting download for URL: {info['webpage_url']}")
            print(f"🚀 [Download] Starting download for URL: {info['webpage_url']}")
            download_success = False
            
            # Thử download với format hiện tại
            try:
                logger.info("📥 [Download] Attempting download with current format...")
                print("📥 [Download] Attempting download with current format...")
                # Note: Cannot access ydl.opts directly, logging disabled here
                ydl.download([info['webpage_url']])
                logger.info("✅ [Download] Download completed successfully")
                print("✅ [Download] Download completed successfully")
                
                # Check files immediately after download
                files_after_download = os.listdir(temp_dir)
                logger.info(f"📁 [Download] Files immediately after download: {files_after_download}")
                print(f"📁 [Download] Files immediately after download: {files_after_download}")
                
                download_success = True
            except Exception as download_error:
                logger.error(f"❌ [Download] Download failed with current format: {str(download_error)}")
                print(f"❌ [Download] Download failed with current format: {str(download_error)}")
                logger.error(f"❌ [Download] Error type: {type(download_error).__name__}")
                print(f"❌ [Download] Error type: {type(download_error).__name__}")
                
                # Fallback: thử với format đơn giản hơn
                logger.info("🔄 [Download] Trying fallback format...")
                print(f"🔄 [Download] Trying fallback - FFmpeg available: {self._check_ffmpeg()}")
                
                # Strategy 1: Thử với format IDs cụ thể từ debug info
                # Format 91 có acodec=mp4a.40.5 và vcodec - hãy thử trực tiếp
                fallback_formats = [
                    '91',  # Try format 91 directly - it has audio
                    'bestaudio[acodec!=none]/best[acodec!=none][height<=480]/best[acodec!=none]',
                    'worstaudio[acodec!=none]/worst[acodec!=none][height<=720]/worst[acodec!=none]',
                    'best[acodec!=none]/worst[acodec!=none]',  # Simplest - any format with audio
                    'best[height<=480]',  # Lower quality video+audio
                    'worst',  # Last resort - take anything
                ]
                
                for i, fallback_format in enumerate(fallback_formats):
                    try:
                        logger.info(f"🔄 [Fallback {i+1}] Trying fallback strategy: {fallback_format}")
                        print(f"🔄 [Fallback {i+1}] Trying fallback strategy: {fallback_format}")
                        
                        # Create new ydl_opts for this fallback
                        fallback_opts = ydl_opts.copy()
                        fallback_opts['format'] = fallback_format
                        
                        # Only add audio settings if FFmpeg is available
                        if self._check_ffmpeg():
                            fallback_opts['audioformat'] = 'mp3'
                            fallback_opts['audioquality'] = '128'
                        
                        logger.info(f"🔍 [Fallback {i+1}] ydl_opts: {fallback_opts}")
                        print(f"🔍 [Fallback {i+1}] Format: {fallback_format}")
                        
                        ydl = yt_dlp.YoutubeDL(fallback_opts)
                        ydl.download([info['webpage_url']])
                        
                        logger.info(f"✅ [Fallback {i+1}] Download completed successfully")
                        print(f"✅ [Fallback {i+1}] Download completed successfully")
                        download_success = True
                        break
                    except Exception as fallback_error:
                        logger.error(f"❌ [Fallback {i+1}] Strategy failed: {str(fallback_error)}")
                        print(f"❌ [Fallback {i+1}] Strategy failed: {str(fallback_error)}")
                        logger.error(f"❌ [Fallback {i+1}] Error type: {type(fallback_error).__name__}")
                        print(f"❌ [Fallback {i+1}] Error type: {type(fallback_error).__name__}")
                        continue
                
                if not download_success:
                    logger.error(f"❌ [Download] All fallback strategies failed")
                    print(f"❌ [Download] All fallback strategies failed")
                    return {
                        'success': False,
                        'error': f'Lỗi download: {str(download_error)}. Tất cả fallback strategies đều thất bại.'
                    }
            
            if not download_success:
                logger.error(f"❌ [Download] Download failed - no success flag")
                print(f"❌ [Download] Download failed - no success flag")
                return {
                    'success': False,
                    'error': 'Không thể download audio từ video'
                }
            
            # ✅ Debug: List all files in temp directory
            logger.info(f"📁 [Files] Checking files in temp directory: {temp_dir}")
            print(f"📁 [Files] Checking files in temp directory: {temp_dir}")
            all_files = os.listdir(temp_dir)
            logger.info(f"📁 [Files] All files in temp directory ({len(all_files)}): {all_files}")
            print(f"📁 [Files] All files in temp directory ({len(all_files)}): {all_files}")
            
            # Log file details
            for f in all_files:
                file_path = os.path.join(temp_dir, f)
                file_size = os.path.getsize(file_path)
                logger.info(f"  - {f}: {file_size} bytes")
                print(f"  - {f}: {file_size} bytes")
            
            # Tìm file đã download - mở rộng format support
            # Accept video formats too (mp4, webm) vì chúng có thể chứa audio-only hoặc audio+video
            audio_extensions = ('.mp3', '.webm', '.m4a', '.mp4', '.ogg', '.wav', '.mkv', '.avi', '.flv')
            
            # Debug: Log each file và check if it matches extensions
            logger.info(f"🔍 [Files] Checking each file against audio_extensions:")
            print(f"🔍 [Files] Checking each file against audio_extensions:")
            for f in all_files:
                matches = f.lower().endswith(audio_extensions)
                logger.info(f"  - {f}: matches={matches}")
                print(f"  - {f}: matches={matches}")
            
            downloaded_files = [f for f in all_files if f.lower().endswith(audio_extensions)]
            
            # Double-check: verify files actually exist in filesystem
            verified_files = []
            for f in downloaded_files:
                file_path = os.path.join(temp_dir, f)
                if os.path.exists(file_path):
                    verified_files.append(f)
                    logger.info(f"✅ [Files] Verified: {f} exists at {file_path}")
                    print(f"✅ [Files] Verified: {f} exists at {file_path}")
                else:
                    logger.error(f"❌ [Files] File not found: {f} at {file_path}")
                    print(f"❌ [Files] File not found: {f} at {file_path}")
            
            downloaded_files = verified_files
            logger.info(f"🎵 [Files] Audio/video files found (verified): {downloaded_files}")
            print(f"🎵 [Files] Audio/video files found (verified): {downloaded_files}")
            
            if not downloaded_files:
                logger.error(f"❌ [Files] No audio files found in {temp_dir}")
                print(f"❌ [Files] No audio files found in {temp_dir}")
                logger.error(f"❌ [Files] All files were: {all_files}")
                print(f"❌ [Files] All files were: {all_files}")
                
                # Check if only .info.json was downloaded
                info_json_files = [f for f in all_files if f.endswith('.info.json')]
                if info_json_files:
                    logger.error(f"⚠️ [Files] Only .info.json files were downloaded. This usually means yt-dlp couldn't download the audio stream.")
                    print(f"⚠️ [Files] Only .info.json files were downloaded. This usually means yt-dlp couldn't download the audio stream.")
                    
                    # Collect debug info
                    debug_info = {
                        'available_formats': len(info.get('formats', [])),
                        'first_formats': [
                            {'id': f.get('format_id'), 'ext': f.get('ext'), 'acodec': f.get('acodec'), 'vcodec': f.get('vcodec')}
                            for f in info.get('formats', [])[:5]
                        ] if info.get('formats') else [],
                        'files_downloaded': all_files,
                        'video_id': info.get('id'),
                        'video_title': info.get('title')
                    }
                    
                    logger.error(f"🔍 [Debug] Available formats: {debug_info}")
                    print(f"🔍 [Debug] Available formats: {debug_info}")
                    
                    return {
                        'success': False,
                        'error': f'Không thể download audio từ video. yt-dlp chỉ download được metadata (.info.json) nhưng không download được audio stream.',
                        'debug_info': debug_info
                    }
                
                return {
                    'success': False,
                    'error': f'Không thể download audio từ video. Files trong thư mục: {all_files}'
                }
            
            # ✅ Validate downloaded file format
            # Safety check: make sure downloaded_files is not empty
            if not downloaded_files:
                logger.error(f"❌ [Files] downloaded_files is empty!")
                print(f"❌ [Files] downloaded_files is empty!")
                return {
                    'success': False,
                    'error': 'Không có file audio nào được download',
                    'debug_info': {
                        'all_files': all_files,
                        'audio_extensions_searched': audio_extensions
                    }
                }
            
            logger.info(f"📄 [File] Processing downloaded_files[0]: {downloaded_files[0]}")
            print(f"📄 [File] Processing downloaded_files[0]: {downloaded_files[0]}")
            
            audio_file = os.path.join(temp_dir, downloaded_files[0])
            file_extension = os.path.splitext(audio_file)[1].lower()
            logger.info(f"📄 [File] Full path: {audio_file}, extension: {file_extension}")
            print(f"📄 [File] Full path: {audio_file}, extension: {file_extension}")
            
            # ✅ Nếu file là MP4, có thể sử dụng trực tiếp (browser can play MP4 audio)
            # Browser HTML5 audio element can play MP4 videos directly - no need for FFmpeg
            if file_extension == '.mp4' and not self._check_ffmpeg():
                logger.info("📄 [File] MP4 file detected without FFmpeg - using directly")
                print(f"📄 [File] MP4 file detected without FFmpeg - using directly")
                logger.info("✅ [File] Browser can play MP4 files directly via HTML5 audio")
                print("✅ [File] Browser can play MP4 files directly via HTML5 audio")
                # Continue with MP4 file - no alternative download needed
            
            # ✅ Validate audio file trước khi tạo UserTrack
            logger.info(f"🔍 [Validation] Validating audio file: {audio_file}")
            print(f"🔍 [Validation] Validating audio file: {audio_file}")
            
            # List all files again before validation
            all_files_check = os.listdir(temp_dir)
            logger.info(f"🔍 [Validation] All files before validation: {all_files_check}")
            print(f"🔍 [Validation] All files before validation: {all_files_check}")
            
            # Log file existence check
            logger.info(f"🔍 [Validation] audio_file exists: {os.path.exists(audio_file)}")
            print(f"🔍 [Validation] audio_file exists: {os.path.exists(audio_file)}")
            
            if not os.path.exists(audio_file):
                logger.error(f"❌ [Validation] Audio file does not exist: {audio_file}")
                print(f"❌ [Validation] Audio file does not exist: {audio_file}")
                logger.error(f"❌ [Validation] Downloaded files list: {downloaded_files}")
                print(f"❌ [Validation] Downloaded files list: {downloaded_files}")
                logger.error(f"❌ [Validation] All files in temp_dir: {all_files_check}")
                print(f"❌ [Validation] All files in temp_dir: {all_files_check}")
                
                # Return debug info
                return {
                    'success': False,
                    'error': 'File audio không tồn tại sau khi download',
                    'debug_info': {
                        'audio_file_path': audio_file,
                        'downloaded_files': downloaded_files,
                        'all_files': all_files_check,
                        'audio_extensions_searched': audio_extensions
                    }
                }
            
            file_size = os.path.getsize(audio_file)
            logger.info(f"📊 [Validation] Audio file size: {file_size} bytes ({file_size / (1024*1024):.2f} MB)")
            print(f"📊 [Validation] Audio file size: {file_size} bytes ({file_size / (1024*1024):.2f} MB)")
            
            if file_size == 0:
                logger.error(f"Audio file is empty: {audio_file}")
                return {
                    'success': False,
                    'error': 'File audio rỗng sau khi download'
                }
            
            if file_size < 1024:  # Less than 1KB
                logger.error(f"Audio file too small: {audio_file} ({file_size} bytes)")
                return {
                    'success': False,
                    'error': 'File audio quá nhỏ, có thể bị lỗi download'
                }
            
            # Tạo UserTrack
            logger.info(f"🎵 [Create Track] Creating UserTrack from audio file...")
            print(f"🎵 [Create Track] Creating UserTrack from audio file...")
            track = self._create_user_track(user, info, audio_file, playlist_id, None)
            
            if track:
                logger.info(f"✅ [Create Track] Track created successfully: {track.title}")
                print(f"✅ [Create Track] Track created successfully: {track.title}")
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
            
            # ✅ Giới hạn số lượng video import để tránh timeout
            MAX_IMPORT_VIDEOS = 30  # Giới hạn 30 video để tránh timeout
            if len(entries) > MAX_IMPORT_VIDEOS:
                logger.warning(f"Playlist có {len(entries)} video, giới hạn import {MAX_IMPORT_VIDEOS} video đầu tiên")
                entries = entries[:MAX_IMPORT_VIDEOS]
            
            # Tạo album (playlist) từ YouTube playlist nếu chưa có playlist_id
            created_album = None
            if not playlist_id:
                album_name = info.get('title', 'YouTube Import')
                created_album = self._create_album_from_playlist(user, album_name, info)
                if created_album:
                    playlist_id = created_album.id
            
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
            elif m4a_files:
                downloaded_files = m4a_files
            else:
                downloaded_files = webm_files
            
            if not downloaded_files:
                return {
                    'success': False,
                    'error': 'Không thể download audio từ playlist'
                }
            
            # Tạo tracks cho tất cả files
            created_tracks = []
            errors = []
            
            for i, filename in enumerate(downloaded_files):
                try:
                    audio_file = os.path.join(temp_dir, filename)
                    
                    # Lấy info từ file info.json nếu có
                    info_file = os.path.join(temp_dir, filename.replace('.webm', '.info.json').replace('.mp3', '.info.json').replace('.m4a', '.info.json'))
                    video_info = None
                    
                    if os.path.exists(info_file) and os.path.getsize(info_file) > 0:
                        try:
                            with open(info_file, 'r', encoding='utf-8') as f:
                                content = f.read().strip()
                                if content:
                                    video_info = json.loads(content)
                                    logger.info(f"✅ Loaded video info for {filename}: {video_info.get('title', 'Unknown')}")
                        except Exception as e:
                            logger.error(f"Error loading video info: {str(e)}")
                    
                    # Tạo UserTrack với playlist info làm album
                    track = self._create_user_track(user, video_info, audio_file, playlist_id, info)
                    
                    logger.info(f"✅ Created track: {track.title if track else 'Failed'} with thumbnail: {video_info.get('thumbnail') if video_info and track else 'None'}")
                    
                    if track:
                        created_tracks.append({
                            'id': track.id,
                            'title': track.title,
                            'artist': track.artist,
                            'album': track.album,
                            'duration': track.duration,
                            'file_size': track.file_size
                        })
                    else:
                        errors.append(f"Không thể tạo track cho {filename}")
                    
                except Exception as e:
                    error_msg = f"Lỗi với file {filename}: {str(e)}"
                    errors.append(error_msg)
                    logger.error(f"Playlist track processing error for {filename}: {str(e)}", exc_info=True)
            
            # ✅ Thông báo về giới hạn import
            original_count = len(info.get('entries', []))
            imported_count = len(created_tracks)
            limit_message = ""
            if original_count > MAX_IMPORT_VIDEOS:
                limit_message = f" (Giới hạn {MAX_IMPORT_VIDEOS}/{original_count} video để tránh timeout)"
            
            return {
                'success': True,
                'message': f'Import thành công {imported_count}/{len(downloaded_files)} tracks từ playlist{limit_message}',
                'tracks': created_tracks,
                'errors': errors if errors else None,
                'album': {
                    'id': created_album.id if created_album else playlist_id,
                    'name': created_album.name if created_album else 'Existing Playlist',
                    'created': created_album is not None
                } if created_album or playlist_id else None,
                'limit_info': {
                    'original_count': original_count,
                    'imported_count': imported_count,
                    'max_limit': MAX_IMPORT_VIDEOS,
                    'was_limited': original_count > MAX_IMPORT_VIDEOS
                } if original_count > MAX_IMPORT_VIDEOS else None
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
            
            # Gắn thumbnail từ YouTube playlist
            thumbnail_url = playlist_info.get('thumbnail')
            if thumbnail_url:
                attach_thumbnail_to_playlist(album, thumbnail_url)
            
            return album
            
        except Exception as e:
            logger.error(f"Error creating album: {str(e)}", exc_info=True)
            return None
    
    def _create_user_track(self, user, video_info, audio_file_path, playlist_id, playlist_info=None):
        """Tạo UserTrack từ file audio và metadata"""
        print(f"🔍 DEBUG: Starting _create_user_track with file: {audio_file_path}")
        try:
            # Lấy metadata từ video info hoặc filename
            if video_info:
                title = video_info.get('title', 'Unknown Title')
                uploader = video_info.get('uploader', 'Unknown Artist')
                upload_date = video_info.get('upload_date', '')
                thumbnail_url = video_info.get('thumbnail')
                
                # ✅ DEBUG: Log thumbnail_url từ video_info
                print(f"🔍 DEBUG: Extracted thumbnail_url from video_info: {thumbnail_url}")
                logger.info(f"🔍 DEBUG: Extracted thumbnail_url from video_info: {thumbnail_url}")
                logger.info(f"🔍 DEBUG: video_info keys: {list(video_info.keys())}")
                
                # Check if 'thumbnail' is in video_info
                if 'thumbnail' in video_info:
                    print(f"🔍 DEBUG: thumbnail key exists in video_info: {video_info['thumbnail']}")
                    logger.info(f"🔍 DEBUG: thumbnail key exists in video_info: {video_info['thumbnail']}")
                else:
                    print("❌ DEBUG: thumbnail key NOT found in video_info")
                    logger.warning("thumbnail key NOT found in video_info")
                    logger.info(f"Available keys: {list(video_info.keys())}")
            else:
                # Fallback: extract từ filename
                filename = os.path.basename(audio_file_path)
                title, uploader = self._extract_metadata_from_filename(filename)
                upload_date = ''
                thumbnail_url = '' # No thumbnail in filename fallback
                print(f"❌ DEBUG: No video_info, using filename fallback")
                logger.warning(f"No video_info, using filename fallback")
            
            # Clean title (loại bỏ ký tự không hợp lệ)
            title = self._clean_title(title)
            
            # Tạo album name từ playlist hoặc uploader
            if playlist_info:
                album = playlist_info.get('title', 'YouTube Playlist')
            else:
                album = f"{uploader} - {upload_date[:4]}" if upload_date else uploader
            
            # Đọc file size
            file_size = os.path.getsize(audio_file_path)
            
            # Check quota trước khi tạo track
            user_settings = MusicPlayerSettings.objects.get(user=user)
            if not user_settings.can_upload(file_size):
                error_msg = f'File quá lớn ({file_size / (1024*1024):.2f}MB). Quota còn lại: {user_settings.get_upload_usage()["remaining"]:.2f}MB'
                logger.error(error_msg)
                raise Exception(error_msg)
            
            
            # Đọc duration từ file
            duration = self._get_audio_duration(audio_file_path, video_info)
            
            # Tạo filename an toàn với extension gốc
            safe_filename = self._create_safe_filename(title, uploader, audio_file_path)
            print(f"🔍 DEBUG: Original file: {audio_file_path}")
            print(f"🔍 DEBUG: Safe filename: {safe_filename}")
            print(f"🔍 DEBUG: Original extension: {os.path.splitext(audio_file_path)[1]}")
            print(f"🔍 DEBUG: Safe filename extension: {os.path.splitext(safe_filename)[1]}")
            logger.info(f"Original file: {audio_file_path}")
            logger.info(f"Safe filename: {safe_filename}")
            logger.info(f"Original extension: {os.path.splitext(audio_file_path)[1]}")
            logger.info(f"Safe filename extension: {os.path.splitext(safe_filename)[1]}")
            
            # Upload file với extension gốc
            with open(audio_file_path, 'rb') as f:
                # ✅ Đảm bảo Django File sử dụng đúng extension
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
                        play_count=0,  # ✅ Đảm bảo play_count = 0
                        is_active=True
                    )
                    
                    # ✅ Ensure track is saved before attaching thumbnail
                    track.refresh_from_db()
                    
                    # ✅ Debug: Log file path sau khi tạo
                    print(f"🔍 DEBUG: Created track with file path: {track.file.path}")
                    print(f"🔍 DEBUG: File extension: {os.path.splitext(track.file.path)[1]}")
                    logger.info(f"Created track with file path: {track.file.path}")
                    logger.info(f"File extension: {os.path.splitext(track.file.path)[1]}")
                    
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
                            pass
                    
                    # ✅ Gắn thumbnail vào track - SAU KHI track đã có ID
                    print(f"🔍 DEBUG: Checking thumbnail_url before attachment: {thumbnail_url}")
                    logger.info(f"🔍 DEBUG: Checking thumbnail_url before attachment: {thumbnail_url}")
                    
                    if thumbnail_url:
                        print(f"🔍 DEBUG: Attaching thumbnail to track ID: {track.id}, URL: {thumbnail_url}")
                        logger.info(f"🔍 DEBUG: Attaching thumbnail to track ID: {track.id}, URL: {thumbnail_url}")
                        result = attach_thumbnail_to_track(track, thumbnail_url)
                        print(f"🔍 DEBUG: Thumbnail attachment result: {result}")
                        logger.info(f"🔍 DEBUG: Thumbnail attachment result: {result}")
                    else:
                        print("❌ DEBUG: thumbnail_url is empty, skipping attachment")
                        logger.warning("thumbnail_url is empty, skipping attachment")
                    
                    return track
                    
        except Exception as e:
            print(f"❌ ERROR: Create user track error: {str(e)}")
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
    
    def _create_safe_filename(self, title, artist, original_file_path=None):
        """Tạo filename an toàn với extension gốc"""
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
        
        # ✅ Giữ nguyên extension gốc nếu có
        if original_file_path and os.path.exists(original_file_path):
            original_ext = os.path.splitext(original_file_path)[1]
            if original_ext:
                extension = original_ext
            else:
                extension = '.mp3'  # Fallback
        else:
            extension = '.mp3'  # Default
        
        # Thêm timestamp để tránh trùng
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{filename}_{timestamp}{extension}"
        
        return filename
    
    def _get_audio_duration(self, file_path, video_info=None):
        """Lấy duration từ file audio với multiple fallbacks"""
        
        # Method 0: Sử dụng duration từ video_info nếu có (ưu tiên cao nhất)
        if video_info and video_info.get('duration'):
            duration = int(video_info.get('duration'))
            return duration
        
        # Method 1: Sử dụng mutagen (tốt nhất cho MP3/M4A)
        try:
            from mutagen import File as MutagenFile
            audio_file = MutagenFile(file_path)
            if audio_file and hasattr(audio_file, 'info') and audio_file.info.length:
                duration = int(audio_file.info.length)
                return duration
        except Exception as e:
            pass
        
        # Method 2: Sử dụng get_audio_duration từ utils
        try:
            from .utils import get_audio_duration
            duration = get_audio_duration(file_path)
            if duration > 0:
                return duration
        except Exception as e:
            pass
        
        # Method 3: Sử dụng ffprobe nếu có
        try:
            import subprocess
            result = subprocess.run([
                'ffprobe', '-v', 'quiet', '-show_entries', 'format=duration',
                '-of', 'csv=p=0', file_path
            ], capture_output=True, text=True, timeout=10)
            if result.returncode == 0 and result.stdout.strip():
                duration = int(float(result.stdout.strip()))
                return duration
        except Exception as e:
            pass
        
        # Method 4: Sử dụng mutagen với different approach
        try:
            from mutagen import File as MutagenFile
            audio_file = MutagenFile(file_path)
            if audio_file:
                # Try different ways to get duration
                if hasattr(audio_file, 'info') and audio_file.info:
                    if hasattr(audio_file.info, 'length') and audio_file.info.length:
                        duration = int(audio_file.info.length)
                        return duration
                
                # Try to get duration from tags
                if hasattr(audio_file, 'tags') and audio_file.tags:
                    for tag in ['length', 'duration', 'DURATION']:
                        if tag in audio_file.tags:
                            try:
                                duration = int(float(audio_file.tags[tag][0]))
                                return duration
                            except:
                                continue
        except Exception as e:
            pass
        
        # Fallback: Return 180s only as last resort
        return 180  # Default 3 minutes
    
    def format_duration(self, seconds):
        """Format duration thành mm:ss"""
        minutes = seconds // 60
        seconds = seconds % 60
        return f"{minutes}:{seconds:02d}"


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
        import_playlist = data.get('import_playlist', False)  # Mặc định: import file đơn lẻ
        user = request.user
        
        logger.info(f"YouTube info request from user {user.username}: URL={url}, import_playlist={import_playlist}")
        
        if not url:
            logger.warning("Empty URL provided")
            return JsonResponse({
                'success': False,
                'error': 'URL không được để trống'
            }, status=400)
        
        # Log original URL for debugging
        original_url = url
        
        # Detect if it's a playlist URL (phân biệt playlist thực sự vs video với radio mode)
        import re
        # Playlist thực sự: có /playlist hoặc có list= với playlist ID (không phải radio mode RD...)
        has_list_param = bool(re.search(r'[?&]list=', url))
        is_radio_mode = bool(re.search(r'[?&]list=RD', url))
        is_playlist = '/playlist' in url or (has_list_param and not is_radio_mode)
        
        # ✅ Special handling for radio mode - always treat as single video
        if is_radio_mode:
            logger.info("Radio mode detected - treating as single video")
            is_playlist = False
            # Clean radio mode parameters immediately - improved regex
            url = re.sub(r'[?&]list=[^&]*', '', url)
            url = re.sub(r'[?&]start_radio=[^&]*', '', url)
            url = re.sub(r'[?&]index=[^&]*', '', url)
            url = re.sub(r'[?&]+$', '', url)
            url = re.sub(r'\?$', '', url)  # Remove trailing ?
            logger.info(f"Radio mode URL cleaned: {original_url} -> {url}")
        
        logger.info(f"URL analysis: has_list_param={has_list_param}, is_radio_mode={is_radio_mode}, is_playlist={is_playlist}")
        
        # ✅ Xử lý logic preview dựa trên checkbox và radio mode
        if is_radio_mode and not import_playlist:
            # Radio mode và không muốn import playlist - đã clean URL ở trên
            logger.info("Radio mode with single video import - URL already cleaned")
        elif is_playlist and not import_playlist:
            # URL là playlist nhưng user không muốn import playlist
            # Chuyển thành single video bằng cách loại bỏ playlist parameter
            if '?list=' in url:
                url = url.split('?list=')[0]
            elif '/playlist' in url:
                # Không thể chuyển playlist URL thành single video
                return JsonResponse({
                    'success': False,
                    'error': 'URL này là playlist. Vui lòng tick "Import cả playlist" hoặc sử dụng URL video đơn lẻ.'
                }, status=400)
        elif not is_playlist and ('&list=' in url or '?list=' in url) and not import_playlist:
            # URL có &list= hoặc ?list= (radio mode) nhưng user không muốn import playlist
            # Loại bỏ các parameter liên quan đến playlist/radio
            # Loại bỏ &list= và ?list= và &start_radio= parameters
            url = re.sub(r'[?&]list=[^&]*', '', url)
            url = re.sub(r'&start_radio=[^&]*', '', url)
            # Clean up any remaining ? or & at the end
            url = re.sub(r'[?&]+$', '', url)
            logger.info(f"URL cleaned from radio mode: {original_url} -> {url}")
        elif not is_playlist and import_playlist:
            # URL là single video nhưng user muốn import playlist
            return JsonResponse({
                'success': False,
                'error': 'URL này là video đơn lẻ. Bỏ tick "Import cả playlist" để import video này.'
            }, status=400)
        
        # Cấu hình yt-dlp để extract info với tối ưu chống bot detection
        cookie_path = _get_cookie_file_path(user)
        logger.info(f"Using cookie file: {cookie_path}")
        
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'noplaylist': False,  # Allow playlist info extraction
            'extract_flat': False, # Extract full info for better metadata
            'timeout': 15,        # 15 second timeout
            
            # ✅ Anti-bot detection optimizations
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'referer': 'https://www.youtube.com/',
            'http_headers': {
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            },
            
            # ✅ Rate limiting và retry logic
            'retries': 2,
            'fragment_retries': 2,
            'retry_sleep_functions': {'http': lambda n: min(2 ** n, 10)},
            
            # ✅ Cookie support
            'cookiefile': cookie_path,
            
            # ✅ Throttling để tránh spam
            'sleep_interval': 0.5,
            'max_sleep_interval': 2,
        }
        
        logger.info(f"Final URL for yt-dlp: {url}")
        logger.info(f"yt-dlp options: {ydl_opts}")
        logger.info(f"Starting yt-dlp extraction for URL: {url}")
        
        info = None
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # Thêm timeout cho yt-dlp extraction (Windows compatible)
                import threading
                import time
                
                info = None
                error = None
                
                def extract_info():
                    nonlocal info, error
                    try:
                        info = ydl.extract_info(url, download=False)
                    except Exception as e:
                        error = e
                
                # Chạy extraction trong thread riêng
                thread = threading.Thread(target=extract_info)
                thread.daemon = True
                thread.start()
                
                # Đợi tối đa 25 giây
                thread.join(timeout=25)
                
                if thread.is_alive():
                    logger.error("yt-dlp extraction timeout after 25 seconds")
                    return JsonResponse({
                        'success': False,
                        'error': 'Timeout khi lấy thông tin từ YouTube. Vui lòng thử lại.'
                    }, status=408)
                
                if error:
                    logger.error(f"yt-dlp extraction error: {str(error)}", exc_info=True)
                    return JsonResponse({
                        'success': False,
                        'error': f'Lỗi yt-dlp: {str(error)}'
                    }, status=500)
                
                logger.info(f"yt-dlp extraction completed. Info keys: {list(info.keys()) if info else 'None'}")
        except Exception as e:
            logger.error(f"yt-dlp wrapper error: {str(e)}", exc_info=True)
            return JsonResponse({
                'success': False,
                'error': f'Lỗi khởi tạo yt-dlp: {str(e)}'
            }, status=500)
            
        # Xử lý kết quả nếu không có lỗi
        if not info:
            logger.error("yt-dlp returned no info")
            return JsonResponse({
                'success': False,
                'error': 'Không thể lấy thông tin từ URL'
            }, status=400)
            
        # Xử lý single video hoặc playlist dựa trên import_playlist
        if 'entries' not in info or not import_playlist:
            # Single video hoặc không muốn import playlist
            logger.info("Processing as single video")
            logger.info(f"Video info: title={info.get('title')}, uploader={info.get('uploader')}, duration={info.get('duration')}")
            
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
                    'import_mode': 'single'  # Thêm flag để frontend biết
                }
            })
        else:
            # Playlist và muốn import playlist
            logger.info("Processing as playlist")
            entries = info.get('entries', [])
            logger.info(f"Playlist has {len(entries)} entries")
            
            videos_info = []
            
            for i, entry in enumerate(entries[:10]):  # Chỉ lấy 10 videos đầu để preview
                if entry:
                    logger.info(f"Processing entry {i}: {entry.get('title', 'Unknown') if isinstance(entry, dict) else 'Flat entry'}")
                    
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
            
            logger.info(f"Returning playlist info with {len(videos_info)} videos")
            
            # ✅ Cảnh báo cho playlist lớn
            warning_message = None
            if len(entries) > 50:
                warning_message = f"Cảnh báo: Playlist có {len(entries)} video. Import sẽ mất rất nhiều thời gian và có thể timeout. Khuyến nghị import playlist nhỏ hơn (< 50 video)."
            elif len(entries) > 20:
                warning_message = f"Playlist có {len(entries)} video. Import sẽ mất vài phút."
            
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
                    'import_mode': 'playlist',  # Thêm flag để frontend biết
                    'warning': warning_message  # ✅ Thêm cảnh báo
                }
            })
            
    except Exception as e:
        logger.error(f"YouTube info extraction error: {str(e)}", exc_info=True)
        return JsonResponse({
            'success': False,
            'error': f'Lỗi khi lấy thông tin: {str(e)}'
        }, status=500)


@csrf_exempt
@require_POST
@login_required
def upload_youtube_cookie(request):
    """API endpoint để upload cookie file của user"""
    try:
        if 'cookie_file' not in request.FILES:
            return JsonResponse({
                'success': False,
                'error': 'Vui lòng chọn file cookie'
            }, status=400)
        
        cookie_file = request.FILES['cookie_file']
        
        # Validate file type
        if not cookie_file.name.endswith('.txt'):
            return JsonResponse({
                'success': False,
                'error': 'File cookie phải có định dạng .txt'
            }, status=400)
        
        # Validate file size (max 1MB)
        if cookie_file.size > 1024 * 1024:
            return JsonResponse({
                'success': False,
                'error': 'File cookie quá lớn (tối đa 1MB)'
            }, status=400)
        
        # Validate cookie content
        try:
            content = cookie_file.read().decode('utf-8')
            cookie_file.seek(0)  # Reset file pointer
            
            # Kiểm tra có phải Netscape cookie format không
            if not ('youtube.com' in content and 
                   any(cookie in content for cookie in ['SID', 'HSID', 'SSID', 'APISID', 'SAPISID'])):
                return JsonResponse({
                    'success': False,
                    'error': 'File cookie không hợp lệ. Vui lòng export cookie từ trình duyệt với domain youtube.com'
                }, status=400)
                
        except UnicodeDecodeError:
            return JsonResponse({
                'success': False,
                'error': 'File cookie không đúng định dạng UTF-8'
            }, status=400)
        
        # Lưu cookie file
        from .models import UserYouTubeCookie
        
        # Xóa cookie cũ nếu có
        UserYouTubeCookie.objects.filter(user=request.user).delete()
        
        # Tạo cookie mới
        user_cookie = UserYouTubeCookie.objects.create(
            user=request.user,
            cookie_file=cookie_file,
            is_active=True
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Cookie file đã được upload thành công!',
            'cookie_id': user_cookie.id,
            'is_valid': user_cookie.is_cookie_valid()
        })
        
    except Exception as e:
        logger.error(f"YouTube cookie upload error: {str(e)}", exc_info=True)
        return JsonResponse({
            'success': False,
            'error': f'Lỗi khi upload cookie: {str(e)}'
        }, status=500)


@csrf_exempt
@require_POST
@login_required
def delete_youtube_cookie(request):
    """API endpoint để xóa cookie file của user"""
    try:
        from .models import UserYouTubeCookie
        
        user_cookie = UserYouTubeCookie.objects.filter(user=request.user).first()
        if user_cookie:
            user_cookie.delete()
            return JsonResponse({
                'success': True,
                'message': 'Cookie file đã được xóa thành công!'
            })
        else:
            return JsonResponse({
                'success': False,
                'error': 'Không tìm thấy cookie file để xóa'
            }, status=404)
            
    except Exception as e:
        logger.error(f"YouTube cookie delete error: {str(e)}", exc_info=True)
        return JsonResponse({
            'success': False,
            'error': f'Lỗi khi xóa cookie: {str(e)}'
        }, status=500)


@csrf_exempt
@require_POST
@login_required
def get_youtube_cookie_status(request):
    """API endpoint để lấy trạng thái cookie của user"""
    try:
        from .models import UserYouTubeCookie
        
        user_cookie = UserYouTubeCookie.objects.filter(user=request.user).first()
        
        if user_cookie:
            return JsonResponse({
                'success': True,
                'has_cookie': True,
                'is_valid': user_cookie.is_cookie_valid(),
                'created_at': user_cookie.created_at.isoformat(),
                'file_name': user_cookie.cookie_file.name if user_cookie.cookie_file else None
            })
        else:
            return JsonResponse({
                'success': True,
                'has_cookie': False,
                'is_valid': False
            })
            
    except Exception as e:
        logger.error(f"YouTube cookie status error: {str(e)}", exc_info=True)
        return JsonResponse({
            'success': False,
            'error': f'Lỗi khi lấy trạng thái cookie: {str(e)}'
        }, status=500)


@csrf_exempt
@require_POST
@login_required
def cancel_youtube_import(request):
    """API endpoint để hủy import đang chạy"""
    try:
        user_id = request.user.id
        logger.info(f"Cancel import request from user {user_id}")
        
        if cancel_import_session(user_id):
            return JsonResponse({
                'success': True,
                'message': 'Import đã được hủy thành công'
            })
        else:
            return JsonResponse({
                'success': False,
                'error': 'Không có import nào đang chạy để hủy'
            }, status=404)
            
    except Exception as e:
        logger.error(f"Cancel import error: {str(e)}", exc_info=True)
        return JsonResponse({
            'success': False,
            'error': f'Lỗi khi hủy import: {str(e)}'
        }, status=500)


@csrf_exempt
@require_POST
@login_required
def get_youtube_import_status(request):
    """API endpoint để lấy trạng thái import hiện tại"""
    try:
        user_id = request.user.id
        progress = get_import_progress(user_id)
        
        if progress:
            return JsonResponse({
                'success': True,
                'progress': progress
            })
        else:
            return JsonResponse({
                'success': True,
                'progress': {'status': 'idle', 'message': 'Không có import nào đang chạy', 'percentage': 0}
            })
            
    except Exception as e:
        logger.error(f"Get import status error: {str(e)}", exc_info=True)
        return JsonResponse({
            'success': False,
            'error': f'Lỗi khi lấy trạng thái import: {str(e)}'
        }, status=500)


@csrf_exempt
@require_POST
@login_required
def test_youtube_endpoint(request):
    """Test endpoint để debug YouTube import"""
    try:
        logger.info("Test endpoint called")
        return JsonResponse({
            'success': True,
            'message': 'Test endpoint hoạt động bình thường',
            'timestamp': timezone.now().isoformat(),
            'user': request.user.username
        })
    except Exception as e:
        logger.error(f"Test endpoint error: {str(e)}", exc_info=True)
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@csrf_exempt
@require_POST
@login_required
def debug_url_processing(request):
    """Debug endpoint để test URL processing"""
    try:
        data = json.loads(request.body)
        url = data.get('url', '').strip()
        
        logger.info(f"Debug URL processing: {url}")
        
        # Test URL processing logic
        import re
        has_list_param = bool(re.search(r'[?&]list=', url))
        is_radio_mode = bool(re.search(r'[?&]list=RD', url))
        is_playlist = '/playlist' in url or (has_list_param and not is_radio_mode)
        
        # Clean URL if needed
        cleaned_url = url
        if not is_playlist and ('&list=' in url or '?list=' in url):
            cleaned_url = re.sub(r'[?&]list=[^&]*', '', url)
            cleaned_url = re.sub(r'&start_radio=[^&]*', '', cleaned_url)
            cleaned_url = re.sub(r'[?&]+$', '', cleaned_url)
        
        return JsonResponse({
            'success': True,
            'original_url': url,
            'cleaned_url': cleaned_url,
            'has_list_param': has_list_param,
            'is_radio_mode': is_radio_mode,
            'is_playlist': is_playlist,
            'url_changed': url != cleaned_url
        })
    except Exception as e:
        logger.error(f"Debug URL processing error: {str(e)}", exc_info=True)
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)
