"""
Utility functions cho Music Player
"""
from mutagen import File as MutagenFile
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

