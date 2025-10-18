from django.core.management.base import BaseCommand
from music_player.models import Track


class Command(BaseCommand):
    help = 'Test get_file_url method for all tracks'

    def handle(self, *args, **options):
        self.stdout.write("🎵 Testing get_file_url() method...")
        
        tracks = Track.objects.all()
        
        if not tracks.exists():
            self.stdout.write("❌ No tracks found in database")
            return
        
        for track in tracks:
            self.stdout.write(f"\n📁 Track: {track.title}")
            self.stdout.write(f"   File path: {track.file_path}")
            self.stdout.write(f"   Generated URL: {track.get_file_url()}")
        
        self.stdout.write(f"\n✅ Tested {tracks.count()} tracks")
