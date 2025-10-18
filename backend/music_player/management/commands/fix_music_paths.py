from django.core.management.base import BaseCommand
from music_player.models import Track
import os


class Command(BaseCommand):
    help = 'Fix music file paths in database to match actual folder structure'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be changed without making actual changes',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        self.stdout.write("🔍 Checking music file paths...")
        
        tracks = Track.objects.all()
        updated_count = 0
        
        for track in tracks:
            old_path = track.file_path
            self.stdout.write(f"\n📁 Track: {track.title}")
            self.stdout.write(f"   Old path: {old_path}")
            
            # Kiểm tra file có tồn tại không
            if os.path.exists(old_path):
                self.stdout.write(f"   ✅ File exists")
                continue
            
            # Tìm file trong các folder có thể
            possible_folders = [
                'media/music/playlist/nhac_ai',
                'media/music/playlist/Nhac AI', 
                'media/music/playlist/nhạc_ai',
                'media/music/playlist/Nhạc AI',
                'media/music/playlist',
            ]
            
            filename = os.path.basename(old_path)
            new_path = None
            
            for folder in possible_folders:
                test_path = os.path.join(folder, filename)
                if os.path.exists(test_path):
                    new_path = os.path.abspath(test_path)
                    self.stdout.write(f"   🔍 Found in: {folder}")
                    break
            
            if new_path:
                self.stdout.write(f"   📝 New path: {new_path}")
                if not dry_run:
                    track.file_path = new_path
                    track.save()
                    self.stdout.write(f"   ✅ Updated!")
                else:
                    self.stdout.write(f"   🔄 Would update (dry run)")
                updated_count += 1
            else:
                self.stdout.write(f"   ❌ File not found anywhere")
        
        if dry_run:
            self.stdout.write(f"\n🔍 Dry run complete. Would update {updated_count} tracks.")
        else:
            self.stdout.write(f"\n✅ Update complete. Updated {updated_count} tracks.")
