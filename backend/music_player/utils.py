"""
Utility functions cho Music Player
"""
from mutagen import File as MutagenFile
from mutagen.id3 import ID3, APIC
from mutagen.mp4 import MP4, MP4Cover
from mutagen.flac import FLAC, Picture
from PIL import Image
from io import BytesIO
from django.core.files.uploadedfile import InMemoryUploadedFile
import os


def get_audio_duration(file_path):
    """
    Đọc thời lượng của file nhạc (tính bằng giây)
    
    Args:
        file_path: Đường dẫn đầy đủ đến file nhạc
        
    Returns:
        int: Thời lượng bài hát tính bằng giây, hoặc 0 nếu không đọc được
    """
    try:
        if not os.path.exists(file_path):
            # File không tồn tại
            return 0
        
        # Sử dụng mutagen để đọc metadata
        audio = MutagenFile(file_path)
        
        if audio is None:
            # Không thể đọc metadata của file
            return 0
        
        if audio.info and hasattr(audio.info, 'length'):
            # Trả về duration làm tròn thành số nguyên
            return int(audio.info.length)
        
        return 0
        
    except Exception as e:
        # Lỗi khi đọc duration của file
        return 0


def get_audio_metadata(file_path):
    """
    Đọc metadata đầy đủ của file nhạc
    
    Args:
        file_path: Đường dẫn đầy đủ đến file nhạc
        
    Returns:
        dict: Dictionary chứa metadata (title, artist, album, duration)
    """
    try:
        if not os.path.exists(file_path):
            return {}
        
        audio = MutagenFile(file_path)
        
        if audio is None:
            return {}
        
        metadata = {}
        
        # Đọc duration
        if audio.info and hasattr(audio.info, 'length'):
            metadata['duration'] = int(audio.info.length)
        
        # Đọc title, artist, album từ tags
        if audio.tags:
            # Mutagen có nhiều format khác nhau, thử các trường phổ biến
            
            # Title
            for key in ['TIT2', 'title', '\xa9nam', 'TITLE']:
                if key in audio.tags:
                    value = audio.tags[key]
                    metadata['title'] = str(value[0]) if isinstance(value, list) else str(value)
                    break
            
            # Artist
            for key in ['TPE1', 'artist', '\xa9ART', 'ARTIST']:
                if key in audio.tags:
                    value = audio.tags[key]
                    metadata['artist'] = str(value[0]) if isinstance(value, list) else str(value)
                    break
            
            # Album
            for key in ['TALB', 'album', '\xa9alb', 'ALBUM']:
                if key in audio.tags:
                    value = audio.tags[key]
                    metadata['album'] = str(value[0]) if isinstance(value, list) else str(value)
                    break
        
        return metadata
        
    except Exception as e:
        # Lỗi khi đọc metadata của file
        return {}


def extract_album_cover(file_path):
    """
    Extract album cover từ file nhạc
    
    Args:
        file_path: Đường dẫn đầy đủ đến file nhạc
        
    Returns:
        InMemoryUploadedFile hoặc None nếu không có album art
    """
    try:
        if not os.path.exists(file_path):
            return None
        
        audio = MutagenFile(file_path)
        if audio is None:
            return None
        
        image_data = None
        
        # Try different tag formats
        if hasattr(audio, 'tags') and audio.tags:
            # MP3 (ID3)
            if isinstance(audio.tags, ID3):
                for tag in audio.tags.values():
                    if isinstance(tag, APIC):
                        image_data = tag.data
                        break
            
            # M4A/AAC (MP4)
            elif isinstance(audio, MP4):
                if 'covr' in audio.tags:
                    image_data = bytes(audio.tags['covr'][0])
            
            # FLAC
            elif isinstance(audio, FLAC):
                if audio.pictures:
                    image_data = audio.pictures[0].data
        
        if not image_data:
            return None
        
        # Convert to PIL Image and resize if needed
        img = Image.open(BytesIO(image_data))
        
        # Resize to max 512x512 to save space
        max_size = 512
        if img.width > max_size or img.height > max_size:
            img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
        
        # Convert to RGB if needed
        if img.mode in ('RGBA', 'LA', 'P'):
            background = Image.new('RGB', img.size, (255, 255, 255))
            if img.mode == 'P':
                img = img.convert('RGBA')
            background.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
            img = background
        
        # Save to BytesIO
        output = BytesIO()
        img.save(output, format='JPEG', quality=85)
        output.seek(0)
        
        # Create InMemoryUploadedFile
        file_name = f"album_cover_{os.path.basename(file_path)}.jpg"
        return InMemoryUploadedFile(
            output,
            'ImageField',
            file_name,
            'image/jpeg',
            output.getbuffer().nbytes,
            None
        )
        
    except Exception as e:
        # Lỗi khi extract album cover
        return None

