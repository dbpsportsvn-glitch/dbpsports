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
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Cài đặt Music Player"
        verbose_name_plural = "Cài đặt Music Player"
    
    def __str__(self):
        return f"Cài đặt nhạc của {self.user.username}"