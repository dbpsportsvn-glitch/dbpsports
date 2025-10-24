# 🧪 Test YouTube Import Feature

## ✅ **Server Status: RUNNING**
Django server đã chạy thành công với YouTube Import feature!

## 🚀 **Cách Test:**

### 1. **Mở Browser**
```
http://localhost:8000
```

### 2. **Đăng Nhập**
- Đăng nhập với tài khoản có quyền sử dụng Music Player

### 3. **Mở Music Player**
- Click vào nút Music Player (icon nhạc)
- Click vào nút Settings (icon gear)

### 4. **Test YouTube Import**
- Chuyển sang tab **"Nhạc Của Tôi"**
- Click nút **"Import từ YouTube"** (màu đỏ với icon YouTube)

### 5. **Test URLs**
```
# Single Video
https://www.youtube.com/watch?v=dQw4w9WgXcQ

# Playlist
https://www.youtube.com/playlist?list=PLrAXtmRdnEQy6nuLMOV8z7jqVzqjJz

# Channel
https://www.youtube.com/channel/UCuAXFkgsw1L7xaCfnd5JJOw
```

## 🔍 **Test Cases:**

### **Test 1: Preview Function**
1. Nhập URL YouTube
2. Click "Xem Trước"
3. Kiểm tra thông tin hiển thị đúng

### **Test 2: Single Video Import**
1. Nhập URL video đơn lẻ
2. Chọn playlist (tùy chọn)
3. Click "Bắt Đầu Import"
4. Kiểm tra progress bar
5. Verify track được thêm vào library

### **Test 3: Playlist Import**
1. Nhập URL playlist
2. Click "Xem Trước" - verify hiển thị danh sách videos
3. Click "Bắt Đầu Import"
4. Kiểm tra progress và kết quả

### **Test 4: Error Handling**
1. Nhập URL không hợp lệ → Verify error message
2. Nhập URL private → Verify error handling
3. Test quota exceeded → Verify quota check

## 🎯 **Expected Results:**

### **✅ Success Cases:**
- Preview hiển thị đúng thông tin video/playlist
- Progress bar hoạt động mượt mà
- Audio được download và convert thành MP3
- Metadata được extract đúng (title, artist, album)
- Track được thêm vào playlist (nếu chọn)
- File size được tính đúng trong quota

### **❌ Error Cases:**
- URL không hợp lệ → Error message rõ ràng
- Network timeout → Graceful error handling
- Quota exceeded → Warning message
- Private video → Appropriate error

## 📊 **Performance Expectations:**

- **Single Video**: 10-30 giây
- **Playlist (5-10 videos)**: 1-3 phút
- **File Size**: ~1-5MB per 3-minute song
- **Quality**: 192kbps MP3

## 🐛 **Debug Info:**

### **Check Logs:**
```bash
# Terminal sẽ hiển thị logs của Django
# Tìm các log messages:
# - "YouTube import processing..."
# - "Successfully imported..."
# - "Error importing..."
```

### **Check Database:**
```python
# Trong Django shell
from music_player.models import UserTrack
UserTrack.objects.filter(user=request.user).count()
```

## 🎉 **Success Criteria:**

1. ✅ Server starts without errors
2. ✅ YouTube Import button appears
3. ✅ Modal opens correctly
4. ✅ Preview works for valid URLs
5. ✅ Import process completes successfully
6. ✅ Tracks appear in user library
7. ✅ Quota is updated correctly

---

## 🚨 **Troubleshooting:**

### **If Server Won't Start:**
```bash
# Check if yt-dlp is installed
venv\Scripts\python.exe -c "import yt_dlp; print('yt-dlp OK')"

# Check Django
venv\Scripts\python.exe manage.py check
```

### **If Import Fails:**
1. Check internet connection
2. Try different YouTube URL
3. Check server logs for errors
4. Verify user quota

### **If UI Issues:**
1. Hard refresh browser (Ctrl+F5)
2. Check browser console for JS errors
3. Verify static files are served correctly

---

**Happy Testing! 🎵✨**
