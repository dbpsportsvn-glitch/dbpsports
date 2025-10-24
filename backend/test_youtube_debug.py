#!/usr/bin/env python
"""
Script để test YouTube import và debug lỗi
"""
import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dbpsports_core.settings')
django.setup()

from django.contrib.auth.models import User
from music_player.models import MusicPlayerSettings, UserTrack
from music_player.youtube_import_views import YouTubeImportView
import json

def test_youtube_import():
    """Test YouTube import với URL cụ thể"""
    
    # Lấy user đầu tiên
    user = User.objects.first()
    if not user:
        print("Không tìm thấy user nào!")
        return
    
    print(f"Testing với user: {user.username}")
    
    # Kiểm tra quota
    user_settings = MusicPlayerSettings.objects.get_or_create(user=user)[0]
    usage = user_settings.get_upload_usage()
    print(f"Quota: {user_settings.storage_quota_mb}MB")
    print(f"Used: {usage['used']:.2f}MB")
    print(f"Remaining: {usage['remaining']:.2f}MB")
    
    # Test URL
    test_url = "https://youtu.be/_DoOVy5BBNU?list=PL00KCN8NwzW6lP5tnY43YdH75xLLNs7aI"
    print(f"\nTesting URL: {test_url}")
    
    # Tạo view instance
    view = YouTubeImportView()
    
    try:
        # Test import
        result = view._import_from_youtube(user, test_url, None, True)
        print(f"\nImport result: {result}")
        
        if result.get('errors'):
            print("\nErrors:")
            for error in result['errors']:
                print(f"  - {error}")
        
        # Kiểm tra tracks được tạo
        tracks = UserTrack.objects.filter(user=user).order_by('-id')[:5]
        print(f"\nRecent tracks: {tracks.count()}")
        for track in tracks:
            print(f"  - {track.title} by {track.artist} ({track.album})")
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_youtube_import()
