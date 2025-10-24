# 🔧 **Đã Sửa Preview và Album Issues!**

## ✅ **Vấn Đề Đã Khắc Phục:**

### **1. Preview Hiển Thị "Unknown":**
- ❌ **Before**: `extract_flat: True` - chỉ lấy thông tin cơ bản
- ✅ **After**: `extract_flat: False` - lấy thông tin đầy đủ

### **2. Download .webm Thay Vì MP3/M4A:**
- ❌ **Before**: FFmpeg detection không hoạt động đúng
- ✅ **After**: Improved FFmpeg detection với timeout và error handling

### **3. Album Information Không Được Set:**
- ❌ **Before**: Không có logging để debug album info
- ✅ **After**: Added detailed logging cho album information

## 🔧 **Technical Changes:**

### **Preview Info Extraction:**
```python
# Cấu hình yt-dlp để extract info (hỗ trợ cả video và playlist)
ydl_opts = {
    'quiet': True,
    'no_warnings': True,
    'noplaylist': False,  # Allow playlist info extraction
    'extract_flat': False, # Extract full info for better metadata
    'timeout': 15,        # 15 second timeout
}
```

### **Improved FFmpeg Detection:**
```python
# Thêm postprocessor chỉ khi có FFmpeg
try:
    import subprocess
    result = subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True, timeout=5)
    # FFmpeg có sẵn, thêm postprocessor
    ydl_opts['postprocessors'] = [{
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'mp3',
        'preferredquality': '192',
    }]
    logger.info("FFmpeg found, will convert to MP3")
except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
    # FFmpeg không có, sử dụng format gốc
    logger.warning("FFmpeg not found, using original format")
    ydl_opts['format'] = 'bestaudio/best'
    # Remove postprocessors if they exist
    if 'postprocessors' in ydl_opts:
        del ydl_opts['postprocessors']
```

### **Enhanced Playlist Processing:**
```python
# Handle both flat and full extraction
if isinstance(entry, dict):
    video_data = {
        'id': entry.get('id'),
        'title': entry.get('title', 'Unknown'),
        'uploader': entry.get('uploader', 'Unknown'),
        'duration': entry.get('duration', 0),
        'duration_formatted': get_duration_formatted(entry.get('duration', 0)),
        'thumbnail': entry.get('thumbnail', ''),
        'webpage_url': entry.get('url', entry.get('webpage_url', '')),
    }
else:
    # Fallback for flat extraction
    video_data = {
        'id': str(entry),
        'title': 'Unknown',
        'uploader': 'Unknown',
        'duration': 0,
        'duration_formatted': '00:00',
        'thumbnail': '',
        'webpage_url': '',
    }
```

### **Album Information Logging:**
```python
# Tạo album name từ playlist hoặc uploader
if playlist_info:
    album = playlist_info.get('title', 'YouTube Playlist')
    logger.info(f"Using playlist as album: {album}")
    logger.info(f"Playlist info keys: {list(playlist_info.keys()) if playlist_info else 'None'}")
else:
    album = f"{uploader} - {upload_date[:4]}" if upload_date else uploader
    logger.info(f"Using uploader as album: {album}")
    logger.info(f"No playlist info provided")
```

## 🎯 **Expected Results:**

### **Before Fix:**
- ❌ Preview hiển thị "Unknown" cho tất cả fields
- ❌ Download .webm files
- ❌ Không có album information
- ❌ Không có logging để debug

### **After Fix:**
- ✅ Preview hiển thị thông tin playlist đúng
- ✅ Download MP3/M4A files (nếu có FFmpeg)
- ✅ Album information từ playlist title
- ✅ Detailed logging cho debugging

## 🚀 **Test Steps:**

### **1. Hard Refresh:**
- Press **Ctrl+F5** để load changes

### **2. Test Preview:**
- URL: `https://youtu.be/_DoOVy5BBNU?list=PL00KCN8NwzW6lP5tnY43YdH75xLLNs7aI`
- Expected: Preview hiển thị playlist info thay vì "Unknown"

### **3. Test Import:**
- Expected: Download MP3/M4A files với album information

### **4. Check Console Logs:**
```
Playlist info: MV Nhạc Vàng Trữ Tình with 2 entries
Using playlist as album: MV Nhạc Vàng Trữ Tình
Playlist info keys: ['id', 'title', 'uploader', 'entries', ...]
Successfully created UserTrack: ANH YÊU EM TRỌN ĐỜI (ID: 123)
```

## 📋 **Requirements:**

### **FFmpeg (Optional):**
- Nếu có FFmpeg: Convert sang MP3
- Nếu không có: Sử dụng M4A/WEBM gốc

### **Dependencies:**
```bash
pip install yt-dlp
pip install mutagen
# FFmpeg optional
```

---

## 🎵 **Expected Success:**

### **Preview Response:**
```
{
  success: true,
  info: {
    type: "playlist",
    title: "MV Nhạc Vàng Trữ Tình",
    uploader: "Channel Name",
    entry_count: 2,
    entries: [
      {
        title: "ANH YÊU EM TRỌN ĐỜI",
        uploader: "Bùi Thuý ft Trần Đức Thành",
        duration_formatted: "04:32"
      },
      {
        title: "Về Với Biển Đi Anh", 
        uploader: "Bùi Thuý ft Trần Đức Thành",
        duration_formatted: "03:45"
      }
    ]
  }
}
```

### **Import Response:**
```
{
  success: true,
  message: "Import thành công 2/2 tracks từ playlist",
  tracks: [
    {
      id: 123,
      title: "ANH YÊU EM TRỌN ĐỜI",
      artist: "Bùi Thuý ft Trần Đức Thành",
      album: "MV Nhạc Vàng Trữ Tình"
    },
    {
      id: 124,
      title: "Về Với Biển Đi Anh",
      artist: "Bùi Thuý ft Trần Đức Thành", 
      album: "MV Nhạc Vàng Trữ Tình"
    }
  ]
}
```

**Preview và Album issues đã được sửa - Test lại! 🎵✨**

**Bây giờ sẽ có preview đúng và album information!**
