# 🎵 YouTube Import Feature - DBP Sports Music Player

## 📋 Tổng Quan

Tính năng **YouTube Import** cho phép người dùng import audio từ YouTube videos và playlists trực tiếp vào Music Player của DBP Sports. Tính năng này sử dụng `yt-dlp` để download và convert video thành audio MP3 với chất lượng cao.

## ✨ Tính Năng

### 🎯 **Hỗ Trợ Import:**
- ✅ **Single Video**: Import một video YouTube đơn lẻ
- ✅ **Playlist**: Import toàn bộ playlist YouTube
- ✅ **Channel Videos**: Import videos từ channel
- ✅ **Auto Metadata**: Tự động extract title, artist, album, duration
- ✅ **Playlist Integration**: Tự động thêm vào playlist cá nhân

### 🔧 **Tùy Chọn Import:**
- ✅ **Audio Only**: Chỉ download audio (khuyến nghị)
- ✅ **Quality Control**: 192kbps MP3 quality
- ✅ **Quota Management**: Kiểm tra quota trước khi import
- ✅ **Preview**: Xem trước thông tin trước khi import

### 🎨 **Giao Diện:**
- ✅ **Modern Modal**: Giao diện đẹp mắt với gradient theme
- ✅ **Preview Section**: Hiển thị thumbnail, title, artist, duration
- ✅ **Progress Bar**: Theo dõi tiến trình import
- ✅ **Error Handling**: Xử lý lỗi thân thiện với người dùng

## 🚀 Cách Sử Dụng

### 1. **Mở Music Player Settings**
- Click vào nút Settings trong Music Player
- Chuyển sang tab "Nhạc Của Tôi"

### 2. **Import từ YouTube**
- Click nút **"Import từ YouTube"** (màu đỏ với icon YouTube)
- Nhập URL YouTube vào ô input:
  ```
  https://www.youtube.com/watch?v=VIDEO_ID
  https://www.youtube.com/playlist?list=PLAYLIST_ID
  https://www.youtube.com/channel/CHANNEL_ID
  ```

### 3. **Cấu Hình Import**
- **Chọn Playlist**: Tùy chọn thêm vào playlist cá nhân
- **Tùy chọn**: Chỉ lấy âm thanh (khuyến nghị)
- Click **"Xem Trước"** để kiểm tra thông tin

### 4. **Bắt Đầu Import**
- Xem trước thông tin video/playlist
- Click **"Bắt Đầu Import"** để download
- Theo dõi tiến trình trong progress bar

## 🔧 Cài Đặt Kỹ Thuật

### **Dependencies:**
```bash
pip install yt-dlp
```

### **Files Đã Thêm/Sửa:**
```
backend/music_player/
├── youtube_import_views.py          # API endpoints
├── static/music_player/js/
│   └── youtube_import.js           # Frontend JavaScript
├── templates/music_player/
│   └── settings_modal.html         # UI modal
└── static/music_player/css/
    └── music_player.css            # Styling
```

### **URL Endpoints:**
```
/music/youtube/import/               # POST - Import từ YouTube
/music/youtube/info/                # POST - Lấy thông tin preview
```

## 📊 API Reference

### **POST /music/youtube/import/**
Import audio từ YouTube URL

**Request:**
```json
{
    "url": "https://www.youtube.com/watch?v=VIDEO_ID",
    "playlist_id": 123,  // Optional
    "extract_audio_only": true
}
```

**Response:**
```json
{
    "success": true,
    "message": "Import thành công: Song Title",
    "track": {
        "id": 456,
        "title": "Song Title",
        "artist": "Artist Name",
        "album": "Album Name",
        "duration": 180,
        "file_size": 5242880
    }
}
```

### **POST /music/youtube/info/**
Lấy thông tin preview từ YouTube URL

**Request:**
```json
{
    "url": "https://www.youtube.com/watch?v=VIDEO_ID"
}
```

**Response:**
```json
{
    "success": true,
    "type": "video",
    "title": "Song Title",
    "uploader": "Artist Name",
    "duration": 180,
    "view_count": 1000000,
    "upload_date": "20240101",
    "thumbnail": "https://..."
}
```

## ⚙️ Cấu Hình

### **yt-dlp Options:**
```python
ydl_opts = {
    'format': 'bestaudio/best',
    'extractaudio': True,
    'audioformat': 'mp3',
    'audioquality': '192',  # 192kbps
    'writethumbnail': True,
    'writedescription': True,
    'writeinfojson': True,
    'ignoreerrors': True,
    'no_warnings': True,
}
```

### **File Processing:**
- **Filename Sanitization**: Loại bỏ ký tự đặc biệt
- **Duration Extraction**: Sử dụng mutagen + fallback
- **Metadata Extraction**: Title, artist, album từ YouTube info
- **Quota Check**: Kiểm tra dung lượng trước khi import

## 🛡️ Bảo Mật & Giới Hạn

### **Quota Management:**
- Mỗi user có quota 369MB mặc định
- Kiểm tra quota trước khi import
- Hiển thị dung lượng còn lại

### **Error Handling:**
- URL validation
- Network timeout (25s)
- File processing errors
- Quota exceeded errors

### **Rate Limiting:**
- Không có rate limit đặc biệt
- Phụ thuộc vào yt-dlp và YouTube

## 🐛 Troubleshooting

### **Lỗi Thường Gặp:**

1. **"URL không hợp lệ"**
   - Kiểm tra URL có đúng format YouTube không
   - Đảm bảo video/playlist không bị private

2. **"File quá lớn"**
   - Kiểm tra quota còn lại
   - Liên hệ admin để mở rộng quota

3. **"Không thể lấy thông tin"**
   - Kiểm tra kết nối internet
   - Thử lại sau vài phút

4. **"Import thất bại"**
   - Kiểm tra log server
   - Thử với video khác

### **Debug Mode:**
```python
# Trong youtube_import_views.py
logger.setLevel(logging.DEBUG)
```

## 📈 Performance

### **Optimizations:**
- **Temp Directory**: Sử dụng tempfile cho download
- **Batch Processing**: Xử lý playlist hiệu quả
- **Error Recovery**: Continue on errors
- **Memory Management**: Cleanup temp files

### **Expected Performance:**
- **Single Video**: 10-30 giây (tùy độ dài)
- **Playlist (10 videos)**: 2-5 phút
- **File Size**: ~1-5MB per 3-minute song

## 🔮 Tính Năng Tương Lai

### **Planned Features:**
- [ ] **Batch Import**: Import nhiều URL cùng lúc
- [ ] **Quality Selection**: Chọn chất lượng audio
- [ ] **Format Options**: MP3, M4A, FLAC
- [ ] **Scheduled Import**: Import theo lịch
- [ ] **Import History**: Lịch sử import
- [ ] **Favorites**: Lưu URL yêu thích

### **Advanced Features:**
- [ ] **Auto Playlist**: Tự động tạo playlist từ channel
- [ ] **Metadata Enhancement**: Cải thiện metadata
- [ ] **Duplicate Detection**: Phát hiện bài hát trùng
- [ ] **Smart Naming**: Đặt tên file thông minh

## 📝 Changelog

### **v1.0.0** (2025-01-25)
- ✅ Initial release
- ✅ Single video import
- ✅ Playlist import
- ✅ Preview functionality
- ✅ Progress tracking
- ✅ Error handling
- ✅ Quota management

---

## 🎉 Kết Luận

Tính năng **YouTube Import** đã được tích hợp hoàn chỉnh vào DBP Sports Music Player, mang lại trải nghiệm import audio từ YouTube một cách chuyên nghiệp và dễ sử dụng. Người dùng có thể dễ dàng mở rộng thư viện nhạc của mình với chất lượng cao và metadata đầy đủ.

**Happy Importing! 🎵✨**
