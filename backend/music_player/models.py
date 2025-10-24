from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.db.models import Count, Sum
import os
import logging

logger = logging.getLogger(__name__)


class Playlist(models.Model):
    """Model để quản lý các playlist nhạc"""
    name = models.CharField(max_length=100, verbose_name="Tên Playlist")
    description = models.TextField(blank=True, null=True, verbose_name="Mô tả")
    cover_image = models.ImageField(upload_to='music/playlist_covers/', blank=True, null=True, verbose_name="Ảnh Bìa Playlist")
    folder_path = models.CharField(max_length=200, verbose_name="Đường dẫn thư mục")
    is_active = models.BooleanField(default=True, verbose_name="Kích hoạt")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Playlist"
        verbose_name_plural = "Playlists"
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    def get_tracks(self):
        """Lấy danh sách các track trong playlist"""
        return self.tracks.filter(is_active=True).order_by('order')
    
    def get_tracks_count(self):
        """Đếm số lượng track trong playlist"""
        return self.tracks.filter(is_active=True).count()


class Track(models.Model):
    """Model để quản lý các bài hát"""
    playlist = models.ForeignKey(Playlist, on_delete=models.CASCADE, related_name='tracks')
    title = models.CharField(max_length=200, verbose_name="Tên bài hát")
    artist = models.CharField(max_length=200, blank=True, null=True, verbose_name="Nghệ sĩ")
    album = models.CharField(max_length=200, blank=True, null=True, verbose_name="Album")
    album_cover = models.ImageField(upload_to='music/album_covers/', blank=True, null=True, verbose_name="Ảnh Bìa Album")
    file_path = models.CharField(max_length=500, verbose_name="Đường dẫn file")
    duration = models.IntegerField(default=0, verbose_name="Thời lượng (giây)")
    order = models.PositiveIntegerField(default=0, verbose_name="Thứ tự")
    is_active = models.BooleanField(default=True, verbose_name="Kích hoạt")
    play_count = models.IntegerField(default=0, verbose_name="Lượt nghe")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Track"
        verbose_name_plural = "Tracks"
        ordering = ['playlist', 'order', 'title']
        unique_together = ['playlist', 'file_path']
    
    def __str__(self):
        return f"{self.title} - {self.artist}" if self.artist else self.title
    
    def get_file_url(self):
        """Lấy URL của file nhạc"""
        # file_path có thể là:
        # - Windows: D:\...\media\music\playlist\folder\file.mp3
        # - Linux: /home/.../media/music/playlist/folder/file.mp3
        # - Relative: media/music/playlist/folder/file.mp3
        
        # Chuẩn hóa path separator
        normalized_path = self.file_path.replace('\\', '/')
        
        # ✅ Pattern 1: Tìm phần sau 'media/music/playlist/'
        if 'media/music/playlist/' in normalized_path:
            relative_path = normalized_path.split('media/music/playlist/')[-1]
            # ✅ CRITICAL FIX: Encode URL để xử lý tên file tiếng Việt
            from urllib.parse import quote
            encoded_path = quote(relative_path, safe='/')
            return f"/media/music/playlist/{encoded_path}"
        
        # ✅ Pattern 2: Absolute path trên Windows/Linux - lấy basename
        # Nếu path bắt đầu bằng drive letter (C:, D:) hoặc root (/)
        if ':/' in normalized_path or normalized_path.startswith('/'):
            basename = os.path.basename(normalized_path)
            # ✅ CRITICAL FIX: Encode basename để xử lý tên file tiếng Việt
            from urllib.parse import quote
            encoded_basename = quote(basename, safe='/')
            return f"/media/music/playlist/{encoded_basename}"
        
        # ✅ Pattern 3: Relative path đã đúng format
        if normalized_path.startswith('/media/'):
            return normalized_path
        
        # Fallback: chỉ lấy basename
        basename = os.path.basename(self.file_path)
        # ✅ CRITICAL FIX: Encode basename để xử lý tên file tiếng Việt
        from urllib.parse import quote
        encoded_basename = quote(basename, safe='/')
        return f"/media/music/playlist/{encoded_basename}"
    
    def get_duration_formatted(self):
        """Lấy thời lượng định dạng mm:ss"""
        minutes = self.duration // 60
        seconds = self.duration % 60
        return f"{minutes:02d}:{seconds:02d}"


class MusicPlayerSettings(models.Model):
    """Model để lưu cài đặt music player"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='music_settings')
    default_playlist = models.ForeignKey(Playlist, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Playlist mặc định")
    auto_play = models.BooleanField(default=True, verbose_name="Tự động phát")
    volume = models.FloatField(default=0.7, verbose_name="Âm lượng")
    repeat_mode = models.CharField(
        max_length=20,
        choices=[
            ('none', 'Không lặp'),
            ('one', 'Lặp một bài'),
            ('all', 'Lặp tất cả'),
        ],
        default='all',
        verbose_name="Chế độ lặp"
    )
    shuffle = models.BooleanField(default=False, verbose_name="Phát ngẫu nhiên")
    listening_lock = models.BooleanField(default=False, verbose_name="Khóa chế độ nghe nhạc")
    low_power_mode = models.BooleanField(default=False, verbose_name="Chế độ máy yếu")
    storage_quota_mb = models.IntegerField(default=369, verbose_name="Giới hạn dung lượng (MB)")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Cài đặt Music Player"
        verbose_name_plural = "Cài đặt Music Player"
    
    def __str__(self):
        return f"Cài đặt nhạc của {self.user.username}"
    
    def get_upload_usage(self):
        """Lấy dung lượng đã dùng / quota (MB)"""
        tracks = UserTrack.objects.filter(user=self.user, is_active=True)
        total_bytes = sum(track.file_size for track in tracks)
        used_mb = total_bytes / (1024 * 1024)  # Convert to MB
        remaining_mb = self.storage_quota_mb - used_mb
        
        return {
            'used': round(used_mb, 2),
            'total': self.storage_quota_mb,
            'remaining': round(remaining_mb, 2),
            'used_bytes': total_bytes,
            'tracks_count': tracks.count()
        }
    
    def can_upload(self, file_size_bytes=0):
        """Kiểm tra có thể upload file với size này không"""
        usage = self.get_upload_usage()
        file_size_mb = file_size_bytes / (1024 * 1024)
        return usage['remaining'] >= file_size_mb


class UserPlaylist(models.Model):
    """Model để quản lý playlist cá nhân của user"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_playlists')
    name = models.CharField(max_length=100, verbose_name="Tên Playlist")
    description = models.TextField(blank=True, null=True, verbose_name="Mô tả")
    cover_image = models.ImageField(upload_to='music/playlist_covers/%Y/%m/', blank=True, null=True, verbose_name="Ảnh Bìa Playlist")
    is_public = models.BooleanField(default=False, verbose_name="Công khai")
    is_active = models.BooleanField(default=True, verbose_name="Kích hoạt")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Playlist Cá Nhân"
        verbose_name_plural = "Playlists Cá Nhân"
        ordering = ['-created_at']
        unique_together = ['user', 'name']
    
    def __str__(self):
        return f"{self.user.username} - {self.name}"
    
    def get_tracks(self):
        """Lấy danh sách các track trong playlist"""
        try:
            return self.tracks.filter(user_track__is_active=True).order_by('order')
        except Exception:
            return UserPlaylistTrack.objects.none()
    
    def get_tracks_count(self):
        """Đếm số lượng track trong playlist"""
        try:
            # Đặc biệt cho playlist "Bài Hát Đã Lưu" - đếm từ SavedTrack
            if self.name == "Bài Hát Đã Lưu":
                from .saved_music_apis import SavedTrack
                return SavedTrack.objects.filter(user=self.user).count()
            
            # Playlist thông thường - đếm từ UserPlaylistTrack
            return self.tracks.filter(user_track__is_active=True).count()
        except Exception:
            return 0
    
    def get_total_duration(self):
        """Tính tổng thời lượng playlist (giây)"""
        try:
            # Đặc biệt cho playlist "Bài Hát Đã Lưu" - tính từ SavedTrack
            if self.name == "Bài Hát Đã Lưu":
                from .saved_music_apis import SavedTrack
                saved_tracks = SavedTrack.objects.filter(user=self.user)
                return sum(saved_track.track_duration for saved_track in saved_tracks if saved_track.track_duration)
            
            # Playlist thông thường - tính từ UserPlaylistTrack
            tracks = self.get_tracks()
            return sum(track.user_track.duration for track in tracks) if tracks else 0
        except Exception:
            return 0


# ✅ OPTIMIZED: Cache Vietnamese mapping for better performance
VIETNAMESE_CHAR_MAP = {
    # A variants
    'à': 'a', 'á': 'a', 'ạ': 'a', 'ả': 'a', 'ã': 'a',
    'ằ': 'a', 'ắ': 'a', 'ặ': 'a', 'ẳ': 'a', 'ẵ': 'a',
    'ầ': 'a', 'ấ': 'a', 'ậ': 'a', 'ẩ': 'a', 'ẫ': 'a',
    'À': 'A', 'Á': 'A', 'Ạ': 'A', 'Ả': 'A', 'Ã': 'A',
    'Ằ': 'A', 'Ắ': 'A', 'Ặ': 'A', 'Ẳ': 'A', 'Ẵ': 'A',
    'Ầ': 'A', 'Ấ': 'A', 'Ậ': 'A', 'Ẩ': 'A', 'Ẫ': 'A',
    
    # E variants
    'è': 'e', 'é': 'e', 'ẹ': 'e', 'ẻ': 'e', 'ẽ': 'e',
    'ề': 'e', 'ế': 'e', 'ệ': 'e', 'ể': 'e', 'ễ': 'e',
    'ê': 'e',
    'È': 'E', 'É': 'E', 'Ẹ': 'E', 'Ẻ': 'E', 'Ẽ': 'E',
    'Ề': 'E', 'Ế': 'E', 'Ệ': 'E', 'Ể': 'E', 'Ễ': 'E',
    'Ê': 'E',
    
    # I variants
    'ì': 'i', 'í': 'i', 'ị': 'i', 'ỉ': 'i', 'ĩ': 'i',
    'Ì': 'I', 'Í': 'I', 'Ị': 'I', 'Ỉ': 'I', 'Ĩ': 'I',
    
    # O variants
    'ò': 'o', 'ó': 'o', 'ọ': 'o', 'ỏ': 'o', 'õ': 'o',
    'ồ': 'o', 'ố': 'o', 'ộ': 'o', 'ổ': 'o', 'ỗ': 'o',
    'ờ': 'o', 'ớ': 'o', 'ợ': 'o', 'ở': 'o', 'ỡ': 'o',
    'ô': 'o', 'ơ': 'o',
    'Ò': 'O', 'Ó': 'O', 'Ọ': 'O', 'Ỏ': 'O', 'Õ': 'O',
    'Ồ': 'O', 'Ố': 'O', 'Ộ': 'O', 'Ổ': 'O', 'Ỗ': 'O',
    'Ờ': 'O', 'Ớ': 'O', 'Ợ': 'O', 'Ở': 'O', 'Ỡ': 'O',
    'Ô': 'O', 'Ơ': 'O',
    
    # U variants
    'ù': 'u', 'ú': 'u', 'ụ': 'u', 'ủ': 'u', 'ũ': 'u',
    'ừ': 'u', 'ứ': 'u', 'ự': 'u', 'ử': 'u', 'ữ': 'u',
    'ư': 'u',
    'Ù': 'U', 'Ú': 'U', 'Ụ': 'U', 'Ủ': 'U', 'Ũ': 'U',
    'Ừ': 'U', 'Ứ': 'U', 'Ự': 'U', 'Ử': 'U', 'Ữ': 'U',
    'Ư': 'U',
    
    # Y variants
    'ỳ': 'y', 'ý': 'y', 'ỵ': 'y', 'ỷ': 'y', 'ỹ': 'y',
    'Ỳ': 'Y', 'Ý': 'Y', 'Ỵ': 'Y', 'Ỷ': 'Y', 'Ỹ': 'Y',
    
    # D variants
    'đ': 'd', 'Đ': 'D'
}

# ✅ OPTIMIZED: Allowed audio extensions
ALLOWED_AUDIO_EXTENSIONS = {'.mp3', '.wav', '.m4a', '.flac', '.aac', '.ogg', '.wma'}

def sanitize_filename(instance, filename):
    """
    ✅ ENHANCED: Sanitize filename to avoid encoding issues by slugifying Vietnamese characters + unique ID
    
    Improvements:
    - Cached Vietnamese mapping (no dict creation per call)
    - Filename length validation
    - Extension validation with fallback
    - Optimized regex patterns
    - Consistent handling for cache and URL encoding
    """
    import re
    import random
    from pathlib import Path
    from datetime import datetime
    
    # Extract extension and validate
    ext = Path(filename).suffix.lower()
    if ext not in ALLOWED_AUDIO_EXTENSIONS:
        ext = '.mp3'  # Default fallback for invalid extensions
    
    # Get name without extension
    name_without_ext = Path(filename).stem
    
    # ✅ ENHANCED: Use cached mapping instead of creating new dict
    slug = name_without_ext.lower()
    for viet, eng in VIETNAMESE_CHAR_MAP.items():
        slug = slug.replace(viet, eng)
    
    # ✅ ENHANCED: Combined regex for better performance
    # Remove special characters and normalize spaces/dashes in one pass
    slug = re.sub(r'[^\w\s-]', '', slug)  # Remove special chars
    slug = re.sub(r'[-\s]+', '_', slug)  # Normalize spaces/dashes to underscores
    slug = slug.strip('_')  # Remove leading/trailing underscores
    
    # ✅ ENHANCED: Filename length validation (keep room for path)
    max_filename_length = 200
    if len(slug) > max_filename_length - 10:  # Reserve space for ID and extension
        slug = slug[:max_filename_length - 10]
        slug = slug.rstrip('_')  # Clean up after truncation
    
    # Generate unique ID to avoid conflicts
    unique_id = random.randint(10000, 99999)
    
    # Combine slug + ID + extension
    safe_filename = f"{slug}_{unique_id}{ext}"
    
    # Format date path
    now = datetime.now()
    date_path = now.strftime('%Y/%m')
    
    # ✅ ENHANCED: Log the sanitization process for debugging
    # Filename sanitization completed
    
    return f'music/user_uploads/{date_path}/{safe_filename}'


class UserTrack(models.Model):
    """Model để quản lý bài hát upload bởi user"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_tracks')
    title = models.CharField(max_length=200, verbose_name="Tên bài hát")
    artist = models.CharField(max_length=200, blank=True, null=True, verbose_name="Nghệ sĩ")
    album = models.CharField(max_length=200, blank=True, null=True, verbose_name="Album")
    album_cover = models.ImageField(upload_to='music/album_covers/%Y/%m/', blank=True, null=True, verbose_name="Ảnh bìa Album")
    file = models.FileField(upload_to=sanitize_filename, verbose_name="File nhạc")
    file_size = models.BigIntegerField(default=0, verbose_name="Kích thước file (bytes)")
    duration = models.IntegerField(default=0, verbose_name="Thời lượng (giây)")
    is_active = models.BooleanField(default=True, verbose_name="Kích hoạt")
    play_count = models.IntegerField(default=0, verbose_name="Lượt nghe")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Bài Hát Cá Nhân"
        verbose_name_plural = "Bài Hát Cá Nhân"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} - {self.artist}" if self.artist else self.title
    
    def get_file_url(self):
        """Lấy URL của file nhạc với encoding nhất quán"""
        if not self.file:
            return ""
        
        # ✅ ENHANCED: Django automatically handles URL encoding for special characters
        # The file.name is already sanitized by sanitize_filename() function
        # Django's file.url automatically encodes any remaining special characters
        url = self.file.url
        
        # ✅ ENHANCED: Log both original name and URL for debugging
        # UserTrack file_url generated
        
        return url
    
    def get_duration_formatted(self):
        """Lấy thời lượng định dạng mm:ss"""
        minutes = self.duration // 60
        seconds = self.duration % 60
        return f"{minutes:02d}:{seconds:02d}"
    
    def get_file_size_formatted(self):
        """Lấy kích thước file định dạng MB"""
        size_mb = self.file_size / (1024 * 1024)
        return f"{size_mb:.2f} MB"
    
    def delete(self, *args, **kwargs):
        """Override delete để xóa file khi xóa track - HOÀN TOÀN XÂY DỰNG LẠI"""
        file_path = None
        file_name = None
        
        # ✅ Bước 1: Lưu thông tin file trước khi xóa
        if self.file:
            file_path = self.file.name
            file_name = self.file.name
        
        # ✅ Bước 2: Xóa file từ storage
        if self.file:
            try:
                # Check if file exists before deleting
                if self.file.storage.exists(self.file.name):
                    # Delete the file
                    self.file.delete(save=False)
                    logger.info(f"✅ Successfully deleted file: {self.file.name}")
                else:
                    logger.warning(f"⚠️ File does not exist: {self.file.name}")
            except Exception as e:
                logger.error(f"❌ Failed to delete file {self.file.name}: {e}")
                # Không raise exception, tiếp tục xóa record
        
        # ✅ Bước 3: Xóa album cover nếu có
        if self.album_cover:
            try:
                if self.album_cover.storage.exists(self.album_cover.name):
                    self.album_cover.delete(save=False)
                    logger.info(f"✅ Successfully deleted album cover: {self.album_cover.name}")
            except Exception as e:
                logger.error(f"❌ Failed to delete album cover {self.album_cover.name}: {e}")
        
        # ✅ Bước 4: Xóa record khỏi database
        super().delete(*args, **kwargs)
        
        # ✅ Bước 5: Log hoàn thành
        logger.info(f"✅ Successfully deleted UserTrack {self.id} ({file_name}) from database")


class UserPlaylistTrack(models.Model):
    """Model trung gian để quản lý track trong playlist của user"""
    playlist = models.ForeignKey(UserPlaylist, on_delete=models.CASCADE, related_name='tracks')
    user_track = models.ForeignKey(UserTrack, on_delete=models.CASCADE, related_name='playlist_entries')
    order = models.PositiveIntegerField(default=0, verbose_name="Thứ tự")
    added_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Track trong Playlist"
        verbose_name_plural = "Tracks trong Playlist"
        ordering = ['playlist', 'order']
        unique_together = ['playlist', 'user_track']
    
    def __str__(self):
        return f"{self.playlist.name} - {self.user_track.title}"


class SavedTrack(models.Model):
    """Model để lưu bài hát yêu thích của user"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='saved_tracks', verbose_name="Người dùng")
    
    # Track có thể là global hoặc user track (nullable vì chỉ 1 trong 2)
    global_track = models.ForeignKey(Track, on_delete=models.CASCADE, null=True, blank=True, related_name='saved_by_users', verbose_name="Track Global")
    user_track = models.ForeignKey(UserTrack, on_delete=models.CASCADE, null=True, blank=True, related_name='saved_by_users', verbose_name="Track Cá Nhân")
    
    # Metadata để phục hồi thông tin nếu track bị xóa
    track_title = models.CharField(max_length=200, verbose_name="Tên bài hát")
    track_artist = models.CharField(max_length=200, blank=True, null=True, verbose_name="Nghệ sĩ")
    track_album = models.CharField(max_length=200, blank=True, null=True, verbose_name="Album")
    track_duration = models.IntegerField(default=0, verbose_name="Thời lượng (giây)")
    track_type = models.CharField(max_length=20, choices=[('global', 'Global'), ('user', 'User')], verbose_name="Loại Track")
    
    saved_at = models.DateTimeField(auto_now_add=True, verbose_name="Thời gian lưu")
    
    class Meta:
        verbose_name = "Bài Hát Đã Lưu"
        verbose_name_plural = "Bài Hát Đã Lưu"
        ordering = ['-saved_at']
        unique_together = [
            ['user', 'global_track'],  # Mỗi user chỉ lưu 1 lần mỗi global track
            ['user', 'user_track'],   # Mỗi user chỉ lưu 1 lần mỗi user track
        ]
        indexes = [
            models.Index(fields=['user', '-saved_at']),
            models.Index(fields=['global_track']),
            models.Index(fields=['user_track']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.track_title}"
    
    def get_track_url(self):
        """Lấy URL của track"""
        if self.global_track:
            return self.global_track.get_file_url()
        elif self.user_track:
            return self.user_track.get_file_url()
        return None
    
    def get_album_cover_url(self):
        """Lấy URL ảnh bìa album"""
        if self.global_track and self.global_track.album_cover:
            return self.global_track.album_cover.url
        elif self.user_track and self.user_track.album_cover:
            return self.user_track.album_cover.url
        return None


class SavedPlaylist(models.Model):
    """Model để lưu playlist/album yêu thích của user"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='saved_playlists', verbose_name="Người dùng")
    
    # Playlist có thể là global hoặc user playlist (nullable vì chỉ 1 trong 2)
    global_playlist = models.ForeignKey(Playlist, on_delete=models.CASCADE, null=True, blank=True, related_name='saved_by_users', verbose_name="Playlist Global")
    user_playlist = models.ForeignKey(UserPlaylist, on_delete=models.CASCADE, null=True, blank=True, related_name='saved_by_users', verbose_name="Playlist Cá Nhân")
    
    # Metadata để phục hồi thông tin nếu playlist bị xóa
    playlist_name = models.CharField(max_length=200, verbose_name="Tên Playlist")
    playlist_description = models.TextField(blank=True, null=True, verbose_name="Mô tả")
    playlist_type = models.CharField(max_length=20, choices=[('global', 'Global'), ('user', 'User')], verbose_name="Loại Playlist")
    
    saved_at = models.DateTimeField(auto_now_add=True, verbose_name="Thời gian lưu")
    
    class Meta:
        verbose_name = "Playlist Đã Lưu"
        verbose_name_plural = "Playlist Đã Lưu"
        ordering = ['-saved_at']
        unique_together = [
            ['user', 'global_playlist'],  # Mỗi user chỉ lưu 1 lần mỗi global playlist
            ['user', 'user_playlist'],    # Mỗi user chỉ lưu 1 lần mỗi user playlist
        ]
        indexes = [
            models.Index(fields=['user', '-saved_at']),
            models.Index(fields=['global_playlist']),
            models.Index(fields=['user_playlist']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.playlist_name}"
    
    def get_cover_image_url(self):
        """Lấy URL ảnh bìa playlist"""
        if self.global_playlist and self.global_playlist.cover_image:
            return self.global_playlist.cover_image.url
        elif self.user_playlist and self.user_playlist.cover_image:
            return self.user_playlist.cover_image.url
        return None
    
    def get_tracks_count(self):
        """Lấy số lượng track trong playlist"""
        if self.global_playlist:
            return self.global_playlist.get_tracks_count()
        elif self.user_playlist:
            return self.user_playlist.tracks.count()
        return 0


class TrackPlayHistory(models.Model):
    """Model để lưu lịch sử nghe nhạc chi tiết"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='play_history', verbose_name="Người dùng")
    
    # Track có thể là global hoặc user track (nullable vì chỉ 1 trong 2)
    global_track = models.ForeignKey(Track, on_delete=models.SET_NULL, null=True, blank=True, related_name='play_history', verbose_name="Track Global")
    user_track = models.ForeignKey(UserTrack, on_delete=models.SET_NULL, null=True, blank=True, related_name='play_history', verbose_name="Track Cá Nhân")
    
    # Thông tin về lượt nghe
    played_at = models.DateTimeField(auto_now_add=True, verbose_name="Thời gian nghe", db_index=True)
    listen_duration = models.IntegerField(default=0, verbose_name="Thời lượng nghe (giây)")
    is_completed = models.BooleanField(default=False, verbose_name="Nghe hết bài")
    
    # Metadata (để phục hồi thông tin nếu track bị xóa)
    track_title = models.CharField(max_length=200, verbose_name="Tên bài hát")
    track_artist = models.CharField(max_length=200, blank=True, null=True, verbose_name="Nghệ sĩ")
    track_duration = models.IntegerField(default=0, verbose_name="Thời lượng track (giây)")
    
    class Meta:
        verbose_name = "Lịch Sử Nghe"
        verbose_name_plural = "Lịch Sử Nghe"
        ordering = ['-played_at']
        indexes = [
            models.Index(fields=['user', '-played_at']),
            models.Index(fields=['global_track', '-played_at']),
            models.Index(fields=['user_track', '-played_at']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.track_title} ({self.played_at.strftime('%Y-%m-%d %H:%M')})"
    
    def get_completion_percentage(self):
        """Tính % hoàn thành"""
        if self.track_duration > 0:
            return round((self.listen_duration / self.track_duration) * 100, 1)
        return 0
    
    @classmethod
    def should_count_as_play(cls, user, track_id, track_type='global'):
        """
        Kiểm tra có nên tính là 1 lượt nghe mới không
        Quy tắc: Cùng user + track trong vòng 5 phút gần nhất = không tính
        """
        five_minutes_ago = timezone.now() - timezone.timedelta(minutes=5)
        
        if track_type == 'global':
            recent_play = cls.objects.filter(
                user=user,
                global_track_id=track_id,
                played_at__gte=five_minutes_ago
            ).exists()
        else:
            recent_play = cls.objects.filter(
                user=user,
                user_track_id=track_id,
                played_at__gte=five_minutes_ago
            ).exists()
        
        return not recent_play
    
    @classmethod
    def get_user_stats(cls, user, days=30):
        """Lấy thống kê của user trong X ngày gần nhất"""
        since = timezone.now() - timezone.timedelta(days=days)
        history = cls.objects.filter(user=user, played_at__gte=since)
        
        return {
            'total_plays': history.count(),
            'total_listen_time': history.aggregate(Sum('listen_duration'))['listen_duration__sum'] or 0,
            'completed_plays': history.filter(is_completed=True).count(),
        }
    
    @classmethod
    def get_popular_tracks(cls, limit=10, days=7):
        """Lấy top tracks được nghe nhiều nhất trong X ngày"""
        since = timezone.now() - timezone.timedelta(days=days)
        
        # Top global tracks
        global_tracks = cls.objects.filter(
            played_at__gte=since,
            global_track__isnull=False
        ).values('global_track', 'track_title', 'track_artist').annotate(
            play_count=Count('id')
        ).order_by('-play_count')[:limit]
        
        # Top user tracks
        user_tracks = cls.objects.filter(
            played_at__gte=since,
            user_track__isnull=False
        ).values('user_track', 'track_title', 'track_artist').annotate(
            play_count=Count('id')
        ).order_by('-play_count')[:limit]
        
        return {
            'global_tracks': list(global_tracks),
            'user_tracks': list(user_tracks)
        }