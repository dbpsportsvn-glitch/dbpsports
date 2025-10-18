from django.db import models
from django.contrib.auth.models import User
import os


class Playlist(models.Model):
    """Model để quản lý các playlist nhạc"""
    name = models.CharField(max_length=100, verbose_name="Tên Playlist")
    description = models.TextField(blank=True, null=True, verbose_name="Mô tả")
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
    file_path = models.CharField(max_length=500, verbose_name="Đường dẫn file")
    duration = models.IntegerField(default=0, verbose_name="Thời lượng (giây)")
    order = models.PositiveIntegerField(default=0, verbose_name="Thứ tự")
    is_active = models.BooleanField(default=True, verbose_name="Kích hoạt")
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
        
        # Tìm và lấy phần sau 'media/music/playlist/'
        if 'media/music/playlist/' in normalized_path:
            relative_path = normalized_path.split('media/music/playlist/')[-1]
            return f"/media/music/playlist/{relative_path}"
        
        # Fallback: chỉ lấy basename (trường hợp file không nằm trong subfolder)
        return f"/media/music/playlist/{os.path.basename(self.file_path)}"
    
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
    upload_quota = models.IntegerField(default=69, verbose_name="Giới hạn số bài upload (deprecated)")
    storage_quota_mb = models.IntegerField(default=500, verbose_name="Giới hạn dung lượng (MB)")
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
            return self.tracks.filter(user_track__is_active=True).count()
        except Exception:
            return 0
    
    def get_total_duration(self):
        """Tính tổng thời lượng playlist (giây)"""
        try:
            tracks = self.get_tracks()
            return sum(track.user_track.duration for track in tracks) if tracks else 0
        except Exception:
            return 0


class UserTrack(models.Model):
    """Model để quản lý bài hát upload bởi user"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_tracks')
    title = models.CharField(max_length=200, verbose_name="Tên bài hát")
    artist = models.CharField(max_length=200, blank=True, null=True, verbose_name="Nghệ sĩ")
    album = models.CharField(max_length=200, blank=True, null=True, verbose_name="Album")
    file = models.FileField(upload_to='music/user_uploads/%Y/%m/', verbose_name="File nhạc")
    file_size = models.BigIntegerField(default=0, verbose_name="Kích thước file (bytes)")
    duration = models.IntegerField(default=0, verbose_name="Thời lượng (giây)")
    is_active = models.BooleanField(default=True, verbose_name="Kích hoạt")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Bài Hát Cá Nhân"
        verbose_name_plural = "Bài Hát Cá Nhân"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} - {self.artist}" if self.artist else self.title
    
    def get_file_url(self):
        """Lấy URL của file nhạc"""
        return self.file.url if self.file else ""
    
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
        """Override delete để xóa file khi xóa track"""
        # Xóa file từ storage
        if self.file:
            self.file.delete(save=False)
        super().delete(*args, **kwargs)


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