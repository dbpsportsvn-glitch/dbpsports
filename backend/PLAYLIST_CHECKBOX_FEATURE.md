# 🎵 **Đã Thêm Checkbox Import Playlist!**

## ✅ **Tính Năng Mới:**

### **Checkbox Import Playlist:**
- ✅ **Tick**: Import cả playlist (mặc định)
- ✅ **Bỏ tick**: Chỉ import video đơn lẻ
- ✅ **Smart Detection**: Tự động phát hiện và xử lý URL
- ✅ **Error Handling**: Thông báo lỗi rõ ràng

## 🔧 **Technical Changes:**

### **Frontend - Checkbox UI:**
```html
<label class="option-checkbox">
    <input type="checkbox" id="import-playlist" checked>
    <span class="checkmark"></span>
    Import cả playlist
</label>
<div class="option-hint">
    <i class="bi bi-info-circle"></i>
    Nếu bỏ tick: chỉ import video đơn lẻ, không import cả playlist
</div>
```

### **Frontend - JavaScript Logic:**
```javascript
const importPlaylistCheckbox = document.getElementById('import-playlist');

// Trong import function
const url = youtubeUrlInput.value.trim();
const playlistId = youtubePlaylistSelect.value || null;
const audioOnly = extractAudioOnlyCheckbox.checked;
const importPlaylist = importPlaylistCheckbox.checked;

// Gửi request
body: JSON.stringify({
    url: url,
    playlist_id: playlistId,
    extract_audio_only: audioOnly,
    import_playlist: importPlaylist
})
```

### **Backend - Smart URL Processing:**
```python
# Detect if it's a playlist URL
is_playlist = '?list=' in youtube_url or '/playlist' in youtube_url

# Xử lý logic import dựa trên checkbox
if is_playlist and not import_playlist:
    # URL là playlist nhưng user không muốn import playlist
    # Chuyển thành single video bằng cách loại bỏ playlist parameter
    if '?list=' in youtube_url:
        youtube_url = youtube_url.split('?list=')[0]
    elif '/playlist' in youtube_url:
        # Không thể chuyển playlist URL thành single video
        return JsonResponse({
            'success': False,
            'error': 'URL này là playlist. Vui lòng tick "Import cả playlist" hoặc sử dụng URL video đơn lẻ.'
        }, status=400)
    logger.info(f"Converted playlist URL to single video: {youtube_url}")
elif not is_playlist and import_playlist:
    # URL là single video nhưng user muốn import playlist
    return JsonResponse({
        'success': False,
        'error': 'URL này là video đơn lẻ. Bỏ tick "Import cả playlist" để import video này.'
    }, status=400)
```

### **Backend - Import Logic:**
```python
def _import_from_youtube(self, user, url, playlist_id, extract_audio_only, import_playlist=True):
    """Import audio từ YouTube URL"""
    
    # Xử lý single video hoặc playlist dựa trên import_playlist
    if 'entries' not in info or not import_playlist:
        return self._process_single_video(user, ydl, info, playlist_id, temp_dir)
    else:
        return self._process_playlist(user, ydl, info, playlist_id, temp_dir)
```

## 🎯 **User Experience:**

### **Scenario 1: Playlist URL + Tick Checkbox**
- ✅ Import cả playlist
- ✅ Tạo album với tên playlist
- ✅ Tất cả tracks trong playlist

### **Scenario 2: Playlist URL + Bỏ Tick Checkbox**
- ✅ Chỉ import video đầu tiên
- ✅ Loại bỏ `?list=` parameter
- ✅ Tạo album "Artist - Single"

### **Scenario 3: Single Video URL + Tick Checkbox**
- ❌ Error: "URL này là video đơn lẻ. Bỏ tick 'Import cả playlist' để import video này."

### **Scenario 4: Single Video URL + Bỏ Tick Checkbox**
- ✅ Import video đơn lẻ
- ✅ Tạo album "Artist - Single"

## 🚀 **Test Steps:**

### **1. Test Playlist Import (Tick Checkbox):**
- URL: `https://youtu.be/_DoOVy5BBNU?list=PL00KCN8NwzW6lP5tnY43YdH75xLLNs7aI`
- Checkbox: ✅ Import cả playlist
- Expected: Import cả playlist, tạo album "MV Nhạc Vàng Trữ Tình"

### **2. Test Playlist Import (Bỏ Tick Checkbox):**
- URL: `https://youtu.be/_DoOVy5BBNU?list=PL00KCN8NwzW6lP5tnY43YdH75xLLNs7aI`
- Checkbox: ❌ Import cả playlist
- Expected: Chỉ import video đầu tiên, tạo album "Artist - Single"

### **3. Test Single Video Import (Tick Checkbox):**
- URL: `https://www.youtube.com/watch?v=VIDEO_ID`
- Checkbox: ✅ Import cả playlist
- Expected: Error message

### **4. Test Single Video Import (Bỏ Tick Checkbox):**
- URL: `https://www.youtube.com/watch?v=VIDEO_ID`
- Checkbox: ❌ Import cả playlist
- Expected: Import video đơn lẻ

## 📋 **Requirements:**

### **Frontend:**
- Checkbox với default checked
- Gửi `import_playlist` parameter
- Reset checkbox khi reset modal

### **Backend:**
- Xử lý `import_playlist` parameter
- Smart URL processing
- Error handling cho các trường hợp không hợp lệ

---

## 🎵 **Expected Results:**

### **Playlist URL + Tick Checkbox:**
```
Console: "Detected playlist URL: https://youtu.be/_DoOVy5BBNU?list=..."
Console: "Created album: MV Nhạc Vàng Trữ Tình (ID: 123)"
Toast: "Import thành công 2/2 tracks từ playlist. Album "MV Nhạc Vàng Trữ Tình" đã được tạo..."
```

### **Playlist URL + Bỏ Tick Checkbox:**
```
Console: "Detected playlist URL: https://youtu.be/_DoOVy5BBNU?list=..."
Console: "Converted playlist URL to single video: https://youtu.be/_DoOVy5BBNU"
Console: "Created album for single video: Artist Name - Single (ID: 124)"
Toast: "Import thành công: Video Title. Album "Artist Name - Single" đã được tạo..."
```

### **Single Video URL + Tick Checkbox:**
```
Error: "URL này là video đơn lẻ. Bỏ tick 'Import cả playlist' để import video này."
```

### **Single Video URL + Bỏ Tick Checkbox:**
```
Console: "Detected single video URL: https://www.youtube.com/watch?v=..."
Console: "Created album for single video: Artist Name - Single (ID: 125)"
Toast: "Import thành công: Video Title. Album "Artist Name - Single" đã được tạo..."
```

**Checkbox Import Playlist đã hoàn thành - Test ngay! 🎵✨**

**Bây giờ có thể linh hoạt chọn import playlist hay video đơn lẻ!**
