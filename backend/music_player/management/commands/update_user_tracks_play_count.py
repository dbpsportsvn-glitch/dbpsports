"""
Management command để cập nhật play_count cho các UserTrack
"""
from django.core.management.base import BaseCommand
from music_player.models import UserTrack
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Cập nhật play_count cho các UserTrack'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Chỉ hiển thị những track sẽ được cập nhật, không thực hiện cập nhật',
        )

    def handle(self, *args, **options):
        dry_run = options.get('dry_run', False)
        
        # Lấy tất cả UserTrack
        tracks = UserTrack.objects.all()
        total_tracks = tracks.count()
        
        if total_tracks == 0:
            self.stdout.write(self.style.WARNING('Không có UserTrack nào.'))
            return
        
        self.stdout.write(f'Tìm thấy {total_tracks} UserTrack.')
        
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN - Không thực hiện cập nhật'))
        
        updated_count = 0
        
        for track in tracks:
            try:
                # Kiểm tra play_count
                if track.play_count is None:
                    if not dry_run:
                        track.play_count = 0
                        track.save(update_fields=['play_count'])
                    
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'✓ {track.title} ({track.artist or "Unknown"}): '
                            f'play_count NULL → 0'
                        )
                    )
                    updated_count += 1
                else:
                    self.stdout.write(
                        self.style.WARNING(
                            f'Không cần cập nhật: {track.title} - play_count: {track.play_count}'
                        )
                    )
                    
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(
                        f'Lỗi khi xử lý track {track.title}: {str(e)}'
                    )
                )
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
