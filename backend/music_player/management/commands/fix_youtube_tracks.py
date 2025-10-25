"""
Script để cập nhật duration và play_count cho các YouTube tracks đã import
"""
from django.core.management.base import BaseCommand
from django.db import models
from music_player.models import UserTrack
from music_player.utils import get_audio_duration
import os
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Cập nhật duration và play_count cho các YouTube tracks đã import'

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
        
        self.stdout.write(self.style.SUCCESS('=' * 60))
        self.stdout.write(self.style.SUCCESS('CẬP NHẬT YOUTUBE TRACKS'))
        self.stdout.write(self.style.SUCCESS('=' * 60))
        
        # Lấy queryset tracks cần cập nhật
        if force:
            tracks = UserTrack.objects.all()
            self.stdout.write('Cập nhật tất cả UserTrack...')
        else:
            # Chỉ cập nhật tracks có duration = 180 (default fallback) hoặc play_count = None
            tracks = UserTrack.objects.filter(
                models.Q(duration=180) | models.Q(play_count__isnull=True)
            )
            self.stdout.write('Cập nhật tracks có duration = 180s hoặc play_count = NULL...')
        
        total_tracks = tracks.count()
        
        if total_tracks == 0:
            self.stdout.write(self.style.WARNING('Không có tracks nào cần cập nhật.'))
            return
        
        self.stdout.write(f'Tìm thấy {total_tracks} tracks cần cập nhật.')
        
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN - Không thực hiện cập nhật'))
        
        updated_duration_count = 0
        updated_play_count_count = 0
        error_count = 0
        
        for track in tracks:
            try:
                updated_fields = []
                
                # Cập nhật duration nếu cần
                if force or track.duration == 180:
                    if track.file and os.path.exists(track.file.path):
                        old_duration = track.duration
                        duration = get_audio_duration(track.file.path)
                        
                        if duration > 0 and duration != old_duration:
                            if not dry_run:
                                track.duration = duration
                            updated_fields.append(f'duration: {old_duration}s → {duration}s ({self.format_duration(duration)})')
                            updated_duration_count += 1
                
                # Cập nhật play_count nếu cần
                if track.play_count is None:
                    if not dry_run:
                        track.play_count = 0
                    updated_fields.append('play_count: NULL → 0')
                    updated_play_count_count += 1
                
                # Lưu nếu có thay đổi
                if updated_fields and not dry_run:
                    track.save(update_fields=['duration', 'play_count'])
                
                if updated_fields:
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'✓ {track.title} ({track.artist or "Unknown"}): '
                            f'{", ".join(updated_fields)}'
                        )
                    )
                else:
                    self.stdout.write(
                        self.style.WARNING(
                            f'Không cần cập nhật: {track.title} - Duration: {track.duration}s, Play Count: {track.play_count}'
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
        self.stdout.write(self.style.SUCCESS('=' * 60))
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN HOÀN THÀNH'))
        else:
            self.stdout.write(self.style.SUCCESS('Hoàn thành!'))
        self.stdout.write(self.style.SUCCESS(f'- Tổng số tracks: {total_tracks}'))
        self.stdout.write(self.style.SUCCESS(f'- Đã cập nhật duration: {updated_duration_count}'))
        self.stdout.write(self.style.SUCCESS(f'- Đã cập nhật play_count: {updated_play_count_count}'))
        self.stdout.write(self.style.SUCCESS(f'- Lỗi: {error_count}'))
    
    def format_duration(self, seconds):
        """Format duration thành mm:ss"""
        minutes = seconds // 60
        seconds = seconds % 60
        return f"{minutes}:{seconds:02d}"
