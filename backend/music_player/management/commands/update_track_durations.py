"""
Management command để cập nhật duration cho các tracks hiện có
"""
from django.core.management.base import BaseCommand
from music_player.models import Track
from music_player.utils import get_audio_duration
import os


class Command(BaseCommand):
    help = 'Cập nhật duration cho tất cả các tracks từ file nhạc'

    def add_arguments(self, parser):
        parser.add_argument(
            '--playlist',
            type=int,
            help='ID của playlist cần cập nhật (nếu không chỉ định sẽ cập nhật tất cả)',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Cập nhật lại duration cho cả những track đã có duration',
        )

    def handle(self, *args, **options):
        playlist_id = options.get('playlist')
        force = options.get('force', False)
        
        # Lấy queryset tracks cần cập nhật
        if playlist_id:
            tracks = Track.objects.filter(playlist_id=playlist_id)
            self.stdout.write(f'Đang cập nhật tracks của playlist ID {playlist_id}...')
        else:
            tracks = Track.objects.all()
            self.stdout.write('Đang cập nhật tất cả tracks...')
        
        # Nếu không force, chỉ cập nhật tracks có duration = 0
        if not force:
            tracks = tracks.filter(duration=0)
            self.stdout.write('Chỉ cập nhật tracks có duration = 0')
        
        total_tracks = tracks.count()
        
        if total_tracks == 0:
            self.stdout.write(self.style.WARNING('Không có tracks nào cần cập nhật.'))
            return
        
        self.stdout.write(f'Tìm thấy {total_tracks} tracks cần cập nhật.')
        
        updated_count = 0
        error_count = 0
        
        for track in tracks:
            try:
                # Kiểm tra file tồn tại
                if not os.path.exists(track.file_path):
                    self.stdout.write(
                        self.style.WARNING(
                            f'File không tồn tại: {track.title} - {track.file_path}'
                        )
                    )
                    error_count += 1
                    continue
                
                # Đọc duration từ file
                duration = get_audio_duration(track.file_path)
                
                if duration > 0:
                    old_duration = track.duration
                    track.duration = duration
                    track.save(update_fields=['duration'])
                    
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'✓ {track.title} ({track.artist or "Unknown"}): '
                            f'{old_duration}s → {duration}s'
                        )
                    )
                    updated_count += 1
                else:
                    self.stdout.write(
                        self.style.WARNING(
                            f'Không thể đọc duration: {track.title} - {track.file_path}'
                        )
                    )
                    error_count += 1
                    
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(
                        f'Lỗi khi xử lý track {track.title}: {str(e)}'
                    )
                )
                error_count += 1
                continue
        
        # Tổng kết
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('=' * 50))
        self.stdout.write(self.style.SUCCESS(f'Hoàn thành!'))
        self.stdout.write(self.style.SUCCESS(f'- Tổng số tracks: {total_tracks}'))
        self.stdout.write(self.style.SUCCESS(f'- Cập nhật thành công: {updated_count}'))
        if error_count > 0:
            self.stdout.write(self.style.WARNING(f'- Lỗi: {error_count}'))
        self.stdout.write(self.style.SUCCESS('=' * 50))

