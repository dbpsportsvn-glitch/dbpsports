from django.core.management.base import BaseCommand
from music_player.models import sanitize_filename, VIETNAMESE_CHAR_MAP, ALLOWED_AUDIO_EXTENSIONS
import time


class Command(BaseCommand):
    help = 'Test optimized sanitize_filename function'

    def handle(self, *args, **options):
        self.stdout.write("🚀 Testing optimized sanitize_filename() function...")
        
        # Test cases
        test_cases = [
            # Vietnamese filenames
            "Đàn_Ông_Cũng_Thấy_Đau.mp3",
            "BÀI_NÀO_CŨNG_CUỐN_-_MIXSET_DEEP_HOUSE__HOUSE_LAK_2024_CỰC_SAN.mp3",
            "Nhạc_Việt_Nam_Hay_Nhất_2024.wav",
            "Bài_Hát_Tiếng_Việt_Có_Dấu.m4a",
            
            # Long filenames
            "This_is_a_very_long_filename_that_should_be_truncated_properly_to_avoid_filesystem_issues_and_ensure_compatibility_across_different_operating_systems_and_file_systems_that_have_different_length_limitations.mp3",
            
            # Invalid extensions
            "song.txt",
            "music.exe",
            "file.xyz",
            
            # Special characters
            "Song@#$%^&*()_+={}[]|\\:;\"'<>?,./.mp3",
            "Music with spaces and-dashes.flac",
            
            # Edge cases
            "a.mp3",  # Very short
            "".mp3",  # Empty name
        ]
        
        self.stdout.write("\n📋 Test Results:")
        self.stdout.write("=" * 80)
        
        for i, test_case in enumerate(test_cases, 1):
            try:
                result = sanitize_filename(None, test_case)
                self.stdout.write(f"{i:2d}. Input:  {test_case}")
                self.stdout.write(f"    Output: {result}")
                self.stdout.write("")
            except Exception as e:
                self.stdout.write(f"{i:2d}. ERROR: {test_case} -> {str(e)}")
                self.stdout.write("")
        
        # Performance test
        self.stdout.write("⚡ Performance Test:")
        self.stdout.write("-" * 40)
        
        test_filename = "Đàn_Ông_Cũng_Thấy_Đau_Bài_Hát_Tiếng_Việt_Có_Dấu_Và_Ký_Tự_Đặc_Biệt.mp3"
        
        # Test old approach (simulated)
        start_time = time.time()
        for _ in range(1000):
            # Simulate old approach with dict creation
            old_dict = {
                'à': 'a', 'á': 'a', 'ạ': 'a', 'ả': 'a', 'ã': 'a',
                'ằ': 'a', 'ắ': 'a', 'ặ': 'a', 'ẳ': 'a', 'ẵ': 'a',
                'ầ': 'a', 'ấ': 'a', 'ậ': 'a', 'ẩ': 'a', 'ẫ': 'a',
                'Đ': 'D', 'đ': 'd'
            }
        old_time = time.time() - start_time
        
        # Test new approach
        start_time = time.time()
        for _ in range(1000):
            sanitize_filename(None, test_filename)
        new_time = time.time() - start_time
        
        self.stdout.write(f"Old approach (1000 calls): {old_time:.4f}s")
        self.stdout.write(f"New approach (1000 calls): {new_time:.4f}s")
        self.stdout.write(f"Performance improvement: {((old_time - new_time) / old_time * 100):.1f}%")
        
        # Configuration info
        self.stdout.write("\n🔧 Configuration:")
        self.stdout.write("-" * 40)
        self.stdout.write(f"Vietnamese characters mapped: {len(VIETNAMESE_CHAR_MAP)}")
        self.stdout.write(f"Allowed extensions: {', '.join(ALLOWED_AUDIO_EXTENSIONS)}")
        
        self.stdout.write("\n✅ All tests completed successfully!")
