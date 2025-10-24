# 🔧 Fix YouTube Playlist Import Issues

## ✅ **Đã Sửa:**

### **1. File Format Issue:**
- ✅ **Force MP3**: Sử dụng `postprocessors` để convert sang MP3
- ✅ **File priority**: Ưu tiên `.mp3` files trước `.webm`
- ✅ **FFmpeg conversion**: Convert audio sang MP3 với quality 192kbps

### **2. Encoding Issue:**
- ✅ **Multiple encodings**: Thử nhiều encoding cho info.json
- ✅ **Fallback encodings**: utf-8, utf-8-sig, latin-1, cp1252
- ✅ **Error handling**: Graceful fallback khi không đọc được

### **3. yt-dlp Configuration:**
- ✅ **Better format**: `bestaudio[ext=m4a]/bestaudio/best`
- ✅ **Post-processing**: FFmpegExtractAudio với MP3 codec
- ✅ **Quality control**: 192kbps MP3 quality

## 🔧 **Technical Changes:**

### **yt-dlp Options:**
```python
ydl_opts = {
    'format': 'bestaudio[ext=m4a]/bestaudio/best',
    'postprocessors': [{
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'mp3',
        'preferredquality': '192',
    }],
    'writethumbnail': True,
    'writedescription': True,
    'writeinfojson': True,
}
```

### **File Processing:**
```python
# Ưu tiên mp3 files
mp3_files = [f for f in all_files if f.endswith('.mp3')]
if mp3_files:
    downloaded_files = mp3_files
else:
    # Fallback to other audio formats
    downloaded_files = [f for f in all_files if f.endswith(('.webm', '.m4a', '.ogg'))]
```

### **Encoding Handling:**
```python
# Try different encodings
for encoding in ['utf-8', 'utf-8-sig', 'latin-1', 'cp1252']:
    try:
        with open(info_file, 'r', encoding=encoding) as f:
            video_info = json.load(f)
        break
    except UnicodeDecodeError:
        continue
```

## 🎯 **Expected Results:**

### **Before Fix:**
- ❌ Downloaded `.webm` files
- ❌ UTF-8 encoding errors
- ❌ 0/2 tracks imported

### **After Fix:**
- ✅ Downloaded `.mp3` files
- ✅ Proper encoding handling
- ✅ 2/2 tracks imported

## 🚀 **Test Steps:**

### **1. Hard Refresh:**
- Press **Ctrl+F5** để load changes

### **2. Test Playlist:**
- URL: `https://youtu.be/_DoOVy5BBNU?list=PL00KCN8NwzW6lP5tnY43YdH75xLLNs7aI`
- Expected: Download MP3 files thay vì WEBM

### **3. Check Console:**
```
Downloaded files: ["song1.mp3", "song2.mp3"]
Created tracks: 2
Errors: 0
```

## 📋 **Requirements:**

### **FFmpeg:**
- Cần FFmpeg để convert audio sang MP3
- yt-dlp sẽ tự động sử dụng FFmpeg

### **Dependencies:**
```bash
pip install yt-dlp
# FFmpeg cần được cài đặt riêng
```

---

## 🎵 **Expected Success:**

```
Import response: {
  success: true,
  message: "Import thành công 2/2 tracks từ playlist",
  tracks: [
    {id: 123, title: "ANH YÊU EM TRỌN ĐỜI", artist: "Bùi Thuý ft Trần Đức Thành", album: "Playlist Title"},
    {id: 124, title: "Về Với Biển Đi Anh", artist: "Bùi Thuý ft Trần Đức Thành", album: "Playlist Title"}
  ],
  errors: null,
  debug_info: {
    downloaded_files: ["song1.mp3", "song2.mp3"],
    created_count: 2,
    error_count: 0
  }
}
```

**File format và encoding issues đã được sửa - Test lại! 🎵✨**
