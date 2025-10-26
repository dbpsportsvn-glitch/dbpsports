"""
Management command để cập nhật duration cho các YouTube tracks đã import
"""
from django.core.management.base import BaseCommand
from music_player.models import UserTrack
from music_player.utils import get_audio_duration
import os
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Cập nhật duration cho các YouTube tracks đã import'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Cập nhật lại duration cho cả những track đã có duration > 0',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Chỉ hiển thị những track sẽ được cập nhật, không thực hiện cập nhật',
        )

    def handle(self, *args, **options):
        force = options.get('force', False)
        dry_run = options.get('dry_run', False)
        
        # Lấy queryset tracks cần cập nhật
        if force:
            tracks = UserTrack.objects.all()
            self.stdout.write('Cập nhật tất cả tracks...')
        else:
            # Chỉ cập nhật tracks có duration = 180 (default fallback)
            tracks = UserTrack.objects.filter(duration=180)
            self.stdout.write('Chỉ cập nhật tracks có duration = 180s (default fallback)...')
        
        total_tracks = tracks.count()
        
        if total_tracks == 0:
            self.stdout.write(self.style.WARNING('Không có tracks nào cần cập nhật.'))
            return
        
        self.stdout.write(f'Tìm thấy {total_tracks} tracks cần cập nhật.')
        
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN - Không thực hiện cập nhật'))
        
        updated_count = 0
        error_count = 0
        
        for track in tracks:
            try:
                # Kiểm tra file tồn tại
                if not track.file or not os.path.exists(track.file.path):
                    self.stdout.write(
                        self.style.WARNING(
                            f'File không tồn tại: {track.title} - {track.file.path if track.file else "No file"}'
                        )
                    )
                    error_count += 1
                    continue
                
                # Đọc duration từ file
                old_duration = track.duration
                duration = get_audio_duration(track.file.path)
                
                if duration > 0 and duration != old_duration:
                    if not dry_run:
                        track.duration = duration
                        track.save(update_fields=['duration'])
                    
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'✓ {track.title} ({track.artist or "Unknown"}): '
                            f'{old_duration}s → {duration}s ({self.format_duration(duration)})'
                        )
                    )
                    updated_count += 1
                else:
                    self.stdout.write(
                        self.style.WARNING(
                            f'Không cần cập nhật: {track.title} - Duration: {old_duration}s'
                        )
                    )
                    
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
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN HOÀN THÀNH'))
        else:
            self.stdout.write(self.style.SUCCESS('Hoàn thành!'))
        self.stdout.write(self.style.SUCCESS(f'- Tổng số tracks: {total_tracks}'))
        self.stdout.write(self.style.SUCCESS(f'- Đã cập nhật: {updated_count}'))
        self.stdout.write(self.style.SUCCESS(f'- Lỗi: {error_count}'))
    
    def format_duration(self, seconds):
        """Format duration thành mm:ss"""
        minutes = seconds // 60
        seconds = seconds % 60
        return f"{minutes}:{seconds:02d}"
