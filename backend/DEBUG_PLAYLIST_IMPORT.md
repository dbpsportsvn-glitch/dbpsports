# 🐛 Debug YouTube Playlist Import Issues

## ✅ **Đã Sửa:**

### **1. JavaScript Error:**
- ✅ **Function check**: Kiểm tra function tồn tại trước khi gọi
- ✅ **Fallback methods**: Sử dụng `loadUserMusic` nếu `loadUserTracks` không có
- ✅ **Error handling**: Log thông báo nếu không có function

### **2. Backend Logging:**
- ✅ **Detailed logging**: Log mọi bước trong playlist processing
- ✅ **File processing**: Log từng file được xử lý
- ✅ **Error tracking**: Log chi tiết lỗi cho từng file
- ✅ **Quota checking**: Log quota và file size

## 🔍 **Debug Steps:**

### **1. Check Server Logs:**
- Mở terminal với Django server
- Xem logs khi import playlist
- Tìm các log messages:
  ```
  Processing 2 downloaded files: ['file1.mp3', 'file2.mp3']
  Processing file 1/2: file1.mp3
  Creating UserTrack for file: /tmp/.../file1.mp3
  Video metadata - Title: Song Title, Uploader: Artist
  File size: 5.2MB
  Quota check passed. Creating track...
  Successfully created UserTrack: Song Title (ID: 123)
  ```

### **2. Check Browser Console:**
- Press **F12** → Console tab
- Xem error messages:
  ```
  Music player refresh functions not available
  ```

### **3. Check Import Response:**
- Xem response từ API:
  ```json
  {
    "success": true,
    "message": "Import thành công 0/2 tracks từ playlist",
    "tracks": [],
    "errors": ["Lỗi với file file1.mp3: ..."]
  }
  ```

## 🚨 **Possible Issues:**

### **1. Quota Exceeded:**
- **Error**: `File quá lớn (5.2MB). Quota còn lại: 2.1MB`
- **Solution**: Tăng quota hoặc import ít videos hơn

### **2. File Processing Error:**
- **Error**: `Lỗi với file file1.mp3: ...`
- **Solution**: Check server logs for details

### **3. Missing Info Files:**
- **Warning**: `No info.json found for file1.mp3`
- **Solution**: yt-dlp không tạo metadata file

### **4. Database Error:**
- **Error**: Database constraint violation
- **Solution**: Check unique constraints

## 🛠️ **Quick Fixes:**

### **1. Check Quota:**
```python
# Trong Django shell
from music_player.models import MusicPlayerSettings
user_settings = MusicPlayerSettings.objects.get(user=user)
print(f"Quota: {user_settings.storage_quota_mb}MB")
print(f"Used: {user_settings.get_upload_usage()['used']:.2f}MB")
print(f"Remaining: {user_settings.get_upload_usage()['remaining']:.2f}MB")
```

### **2. Test Single Video:**
- Thử import single video trước
- Nếu OK → vấn đề ở playlist processing
- Nếu lỗi → vấn đề ở track creation

### **3. Check File Extensions:**
- yt-dlp có thể download `.webm` thay vì `.mp3`
- Check `downloaded_files` trong logs

## 🎯 **Expected Log Output:**

```
Processing 2 downloaded files: ['song1.mp3', 'song2.mp3']
Processing file 1/2: song1.mp3
Loaded video info for song1.mp3: Song Title 1
Creating UserTrack for file: /tmp/.../song1.mp3
Video metadata - Title: Song Title 1, Uploader: Artist 1, Date: 20240101
Using playlist as album: Best Songs 2024
File size: 4.8MB
Quota check passed. Creating track...
Successfully created UserTrack: Song Title 1 (ID: 123)
Processing file 2/2: song2.mp3
...
Import thành công 2/2 tracks từ playlist
```

---

## 🚀 **Next Steps:**

1. **Hard refresh** browser (Ctrl+F5)
2. **Test playlist import** với URL nhỏ
3. **Check server logs** trong terminal
4. **Report specific errors** từ logs

**Debug logging đã được thêm - Hãy check server logs để xem lỗi gì! 🔍**
