# 🔍 Debug YouTube Playlist Import - Chi Tiết

## ✅ **Đã Thêm Debug Info:**

### **1. Backend Debug:**
- ✅ **Debug info**: Trả về thông tin chi tiết về files và errors
- ✅ **File tracking**: Log từng file được download và xử lý
- ✅ **Error details**: Log chi tiết lỗi cho từng file

### **2. Frontend Debug:**
- ✅ **Console logging**: Log errors và debug info
- ✅ **Error display**: Hiển thị từng lỗi cụ thể
- ✅ **Debug info**: Hiển thị thông tin files và counts

## 🔍 **Cách Debug:**

### **1. Hard Refresh Browser:**
- Press **Ctrl+F5** để load JavaScript mới
- Open **Console** (F12) → Console tab

### **2. Test Playlist Import:**
- Click **"Import từ YouTube"**
- Nhập URL: `https://youtu.be/_DoOVy5BBNU?list=PL00KCN8NwzW6lP5tnY43YdH75xLLNs7aI`
- Click **"Xem Trước"** → **"Bắt Đầu Import"**

### **3. Check Console Output:**
```
Import response: {
  success: true,
  message: "Import thành công 0/2 tracks từ playlist",
  tracks: [],
  errors: ["Lỗi với file file1.mp3: ...", "Lỗi với file file2.mp3: ..."],
  debug_info: {
    downloaded_files: ["file1.mp3", "file2.mp3"],
    created_count: 0,
    error_count: 2
  }
}

Import errors: ["Lỗi với file file1.mp3: ...", "Lỗi với file file2.mp3: ..."]
Error: Lỗi với file file1.mp3: ...
Error: Lỗi với file file2.mp3: ...

Debug info: {downloaded_files: [...], created_count: 0, error_count: 2}
Downloaded files: ["file1.mp3", "file2.mp3"]
Created tracks: 0
Errors: 2
```

## 🚨 **Common Issues:**

### **1. Quota Exceeded:**
```
Error: Lỗi với file song1.mp3: File quá lớn (5.2MB). Quota còn lại: 2.1MB
```
**Solution**: Tăng quota hoặc import ít videos hơn

### **2. File Format Issues:**
```
Error: Lỗi với file song1.webm: Không thể tạo track cho song1.webm
```
**Solution**: yt-dlp download `.webm` thay vì `.mp3`

### **3. Missing Metadata:**
```
Error: Lỗi với file song1.mp3: 'NoneType' object has no attribute 'get'
```
**Solution**: Không có video info từ info.json

### **4. Database Constraint:**
```
Error: Lỗi với file song1.mp3: UNIQUE constraint failed
```
**Solution**: Track đã tồn tại với cùng title/artist

## 🛠️ **Quick Fixes:**

### **1. Check File Extensions:**
- yt-dlp có thể download `.webm`, `.m4a` thay vì `.mp3`
- Check `downloaded_files` trong debug info

### **2. Check Quota:**
- Mỗi file ~3-5MB
- Playlist 2 videos = ~6-10MB
- Cần quota đủ

### **3. Check Metadata:**
- yt-dlp có thể không tạo `.info.json`
- Cần fallback metadata

## 🎯 **Expected Success Output:**

```
Import response: {
  success: true,
  message: "Import thành công 2/2 tracks từ playlist",
  tracks: [
    {id: 123, title: "Song 1", artist: "Artist", album: "Playlist Title"},
    {id: 124, title: "Song 2", artist: "Artist", album: "Playlist Title"}
  ],
  errors: null,
  debug_info: {
    downloaded_files: ["song1.mp3", "song2.mp3"],
    created_count: 2,
    error_count: 0
  }
}

Debug info: {downloaded_files: [...], created_count: 2, error_count: 0}
Downloaded files: ["song1.mp3", "song2.mp3"]
Created tracks: 2
Errors: 0
```

---

## 🚀 **Next Steps:**

1. **Hard refresh** browser (Ctrl+F5)
2. **Test playlist import** với URL nhỏ
3. **Check console** cho errors cụ thể
4. **Report specific errors** từ console

**Debug info đã được thêm - Hãy test lại và cho tôi biết errors cụ thể từ console! 🔍**
