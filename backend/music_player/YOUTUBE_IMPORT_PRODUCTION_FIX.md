# YouTube Import Production Fix - Không Cần FFmpeg

## Vấn Đề
- Tính năng import YouTube chạy tốt trên local với FFmpeg
- Trên production không có FFmpeg → lỗi khi import
- Thiếu logging để debug khi có lỗi

## Giải Pháp

### 1. Tối Ưu Backend (youtube_import_views.py)

#### Thay Đổi Chính:
- **Kiểm tra FFmpeg một lần** và quyết định strategy:
  - ✅ **Local (có FFmpeg)**: Sử dụng postprocessors để convert sang MP3
  - ✅ **Production (không FFmpeg)**: Download trực tiếp audio-only streams

#### Code Changes:
```python
# Line 491-528: Kiểm tra FFmpeg và configure yt-dlp
ffmpeg_available = self._check_ffmpeg()

if ffmpeg_available:
    # Local - dùng FFmpeg postprocessors
    ydl_opts['postprocessors'] = [{
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'mp3',
        'preferredquality': '192',
    }]
else:
    # Production - download trực tiếp audio streams
    ydl_opts.pop('audioformat', None)
    ydl_opts.pop('audioquality', None)
    ydl_opts.pop('extractaudio', None)
    ydl_opts.pop('postprocessors', None)
    ydl_opts['format'] = 'bestaudio[ext=m4a]/bestaudio[ext=webm]/bestaudio[ext=mp3]/bestaudio[ext=ogg]/bestaudio/best'
```

#### Logging Đã Thêm:
- 🔍 FFmpeg availability check
- 🚀 Download start/completion
- 📁 Files in temp directory
- 🎵 Audio files found
- 📄 File validation (size, extension)
- 🎵 Track creation progress
- ✅ Success/failure messages

### 2. Tối Ưu Frontend (youtube_import.js)

#### Logging Đã Thêm:
- 📋 Request parameters
- 🌐 HTTP request details
- 📡 Response status
- 📊 Response data parsing
- ✅ Success details (track, album info)
- ❌ Error details (full error object)
- 💥 Exception details (name, message, stack)

#### Console Log Format:
```
🚀 [YouTube Import] Starting import request...
📋 [YouTube Import] Request parameters: {...}
🌐 [YouTube Import] Sending POST request to /music/youtube/import/
📡 [YouTube Import] Import response received: {...}
📊 [YouTube Import] Parsing JSON response...
✅ [YouTube Import] Import successful!
```

## Format Support

### Khi Không Có FFmpeg (Production):
- ✅ M4A (AAC audio)
- ✅ WebM (Opus audio)
- ✅ MP3 (nếu có sẵn)
- ✅ OGG (Vorbis audio)

### Khi Có FFmpeg (Local):
- ✅ Convert tất cả formats sang MP3

## Cách Kiểm Tra

### 1. Kiểm Tra FFmpeg Availability
```bash
# Trên production server
ffmpeg -version
```

### 2. Test Import
1. Mở F12 Console
2. Import một video YouTube
3. Theo dõi logs ở console:
   - 🔍 FFmpeg check result
   - 🚀 Download progress
   - 📁 Files processed
   - ✅ Success hoặc ❌ Error

### 3. Kiểm Tra Logs Backend
```bash
# Trên production server - check Django logs
tail -f /path/to/logs/django.log
```

## Lưu Ý

1. **Format Priority**: Production sẽ download format tốt nhất có sẵn không cần convert
2. **File Size**: Validate file size sau khi download
3. **Error Handling**: Tất cả errors đều được log chi tiết
4. **Progress Tracking**: User có thể theo dõi progress qua console logs

## Kết Quả Mong Đợi

- ✅ Import YouTube hoạt động trên production không cần FFmpeg
- ✅ Logging chi tiết để debug khi có lỗi
- ✅ Support nhiều audio formats (M4A, WebM, MP3, OGG)
- ✅ User có thể theo dõi quá trình import qua F12 console

## Update - Extended Logging

### Thêm Extensive Logging (2025-01-11 Update)

1. **Available Formats Logging**:
   - Log số lượng formats có sẵn
   - Log 5 formats đầu tiên với thông tin chi tiết (format_id, ext, acodec, vcodec)

2. **Download Process Logging**:
   - Log từng bước download
   - Log format đang được sử dụng
   - Log error type và message
   - Log file size và extension

3. **Fallback Strategies**:
   - Thử nhiều formats khác nhau
   - Log từng strategy được thử
   - Log thành công/thất bại của mỗi strategy

4. **Error Detection**:
   - Detect khi chỉ có .info.json được download
   - Hiển thị error message rõ ràng hơn

### Cách Debug Từ Logs

Khi import fails, logs sẽ hiển thị:
```
🔍 [Extract Info] Extracting info from URL: ...
✅ [Extract Info] Info extracted successfully. Title: ...
📊 [Extract Info] Available formats count: X
📊 [Extract Info] First 5 formats:
  - Format 140: ext=m4a, acodec=mp4a.40.2, vcodec=none
  - Format 251: ext=webm, acodec=opus, vcodec=none
  ...
📥 [Download] Attempting download with current format...
✅ [Download] Download completed successfully
📁 [Files] All files in temp directory (2): [...]
  - Video Title.info.json: 1234 bytes
  - Video Title.m4a: 567890 bytes
🎵 [Files] Audio files found: ['Video Title.m4a']
```

Nếu chỉ có .info.json:
```
⚠️ [Files] Only .info.json files were downloaded. This usually means yt-dlp couldn't download the audio stream.
```

## Date
2025-01-11
Updated: 2025-01-11 (Extended Logging)

