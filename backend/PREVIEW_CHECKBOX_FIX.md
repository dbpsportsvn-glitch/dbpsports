# 🎵 **Đã Sửa Logic Preview Checkbox!**

## ✅ **Vấn Đề Đã Sửa:**

### **Trước đây:**
- ❌ Checkbox "Import cả playlist" bỏ tick nhưng preview vẫn hiển thị cả playlist
- ❌ Thông báo "Tất cả bài hát sẽ được import với album" vẫn xuất hiện
- ❌ Logic preview không xử lý checkbox value

### **Bây giờ:**
- ✅ Preview API nhận `import_playlist` parameter từ frontend
- ✅ Backend xử lý URL dựa trên checkbox trước khi extract info
- ✅ Frontend hiển thị đúng chế độ import (single/playlist)
- ✅ Thông báo rõ ràng cho từng chế độ

## 🔧 **Technical Changes:**

### **Frontend - Preview Request:**
```javascript
// Gửi checkbox value trong preview request
const importPlaylist = importPlaylistCheckbox.checked;
console.log('Import playlist checkbox:', importPlaylist);

const response = await fetch('/music/youtube/info/', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': getCsrfToken()
    },
    body: JSON.stringify({ 
        url: url,
        import_playlist: importPlaylist  // ✅ Gửi checkbox value
    })
});
```

### **Backend - Preview API Logic:**
```python
@csrf_exempt
@require_POST
@login_required
def get_youtube_info(request):
    """Lấy thông tin video/playlist từ YouTube URL mà không download"""
    try:
        data = json.loads(request.body)
        url = data.get('url', '').strip()
        import_playlist = data.get('import_playlist', True)  # ✅ Nhận checkbox value
        
        # Detect if it's a playlist URL
        is_playlist = '?list=' in url or '/playlist' in url
        
        # ✅ Xử lý logic preview dựa trên checkbox
        if is_playlist and not import_playlist:
            # URL là playlist nhưng user không muốn import playlist
            # Chuyển thành single video bằng cách loại bỏ playlist parameter
            if '?list=' in url:
                url = url.split('?list=')[0]
            elif '/playlist' in url:
                return JsonResponse({
                    'success': False,
                    'error': 'URL này là playlist. Vui lòng tick "Import cả playlist" hoặc sử dụng URL video đơn lẻ.'
                }, status=400)
            logger.info(f"Converted playlist URL to single video for preview: {url}")
        elif not is_playlist and import_playlist:
            return JsonResponse({
                'success': False,
                'error': 'URL này là video đơn lẻ. Bỏ tick "Import cả playlist" để import video này.'
            }, status=400)
        
        # Extract info với URL đã được xử lý
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            # ✅ Xử lý single video hoặc playlist dựa trên import_playlist
            if 'entries' not in info or not import_playlist:
                # Single video hoặc không muốn import playlist
                return JsonResponse({
                    'success': True,
                    'info': {
                        'type': 'video',
                        'id': info.get('id'),
                        'title': info.get('title', 'Unknown'),
                        'uploader': info.get('uploader', 'Unknown'),
                        'duration': info.get('duration', 0),
                        'duration_formatted': get_duration_formatted(info.get('duration', 0)),
                        'thumbnail': info.get('thumbnail', ''),
                        'webpage_url': info.get('webpage_url', url),
                        'import_mode': 'single'  # ✅ Flag để frontend biết
                    }
                })
            else:
                # Playlist và muốn import playlist
                return JsonResponse({
                    'success': True,
                    'info': {
                        'type': 'playlist',
                        'id': info.get('id'),
                        'title': info.get('title', 'Unknown Playlist'),
                        'uploader': info.get('uploader', 'Unknown'),
                        'entry_count': len(entries),
                        'thumbnail': info.get('thumbnail', ''),
                        'webpage_url': info.get('webpage_url', url),
                        'entries': videos_info,
                        'import_mode': 'playlist'  # ✅ Flag để frontend biết
                    }
                })
```

### **Frontend - Preview Rendering:**
```javascript
function renderYouTubePreview(info) {
    youtubePreviewContent.innerHTML = '';
    
    if (info.type === 'video' || info.import_mode === 'single') {
        // ✅ Single video preview với thông báo rõ ràng
        youtubePreviewContent.innerHTML = `
            <div class="video-preview">
                <div class="preview-thumbnail">
                    <img src="${info.thumbnail}" alt="Thumbnail" width="120">
                </div>
                <div class="preview-info">
                    <h6 class="text-white">${info.title}</h6>
                    <div class="preview-meta">
                        <span class="meta-item"><i class="bi bi-person-fill"></i> ${info.uploader}</span>
                        <span class="meta-item"><i class="bi bi-clock-fill"></i> ${info.duration_formatted}</span>
                    </div>
                    <div class="single-video-note">
                        <i class="bi bi-info-circle"></i>
                        <small>Chỉ import video đơn lẻ này</small>
                    </div>
                </div>
            </div>
        `;
    } else if (info.type === 'playlist' && info.import_mode === 'playlist') {
        // ✅ Playlist preview với thông báo album
        youtubePreviewContent.innerHTML = `
            <div class="playlist-preview">
                <div class="playlist-header">
                    <h6 class="text-white">${info.title}</h6>
                    <div class="playlist-meta">
                        <span class="meta-item"><i class="bi bi-person-fill"></i> ${info.uploader}</span>
                        <span class="meta-item"><i class="bi bi-collection-play-fill"></i> ${info.entry_count} bài hát</span>
                    </div>
                    <div class="playlist-note">
                        <i class="bi bi-info-circle"></i>
                        <small>Tất cả bài hát sẽ được import với album: "${info.title}"</small>
                    </div>
                </div>
                <div class="playlist-videos">
                    ${entriesHtml}
                </div>
            </div>
        `;
    }
}
```

### **CSS - Single Video Note:**
```css
/* Single video note */
.single-video-note {
    margin-top: 10px;
    padding: 8px 12px;
    background: rgba(255, 255, 255, 0.1);
    border-radius: 6px;
    border-left: 3px solid #28a745;
    font-size: 12px;
    color: rgba(255, 255, 255, 0.8);
}

.single-video-note i {
    color: #28a745;
    margin-right: 6px;
}
```

## 🎯 **User Experience:**

### **Scenario 1: Playlist URL + Tick Checkbox**
- ✅ Preview hiển thị: "Tất cả bài hát sẽ được import với album: [Playlist Name]"
- ✅ Hiển thị danh sách tất cả videos trong playlist
- ✅ Import sẽ tạo album với tên playlist

### **Scenario 2: Playlist URL + Bỏ Tick Checkbox**
- ✅ Preview hiển thị: "Chỉ import video đơn lẻ này"
- ✅ Chỉ hiển thị video đầu tiên (đã loại bỏ `?list=` parameter)
- ✅ Import sẽ tạo album "Artist - Single"

### **Scenario 3: Single Video URL + Tick Checkbox**
- ❌ Error: "URL này là video đơn lẻ. Bỏ tick 'Import cả playlist' để import video này."

### **Scenario 4: Single Video URL + Bỏ Tick Checkbox**
- ✅ Preview hiển thị: "Chỉ import video đơn lẻ này"
- ✅ Import sẽ tạo album "Artist - Single"

## 🚀 **Test Steps:**

### **1. Test Playlist Preview (Tick Checkbox):**
- URL: `https://youtu.be/_DoOVy5BBNU?list=PL00KCN8NwzW6lP5tnY43YdH75xLLNs7aI`
- Checkbox: ✅ Import cả playlist
- Expected Preview: "Tất cả bài hát sẽ được import với album: MV Nhạc Vàng Trữ Tình"

### **2. Test Playlist Preview (Bỏ Tick Checkbox):**
- URL: `https://youtu.be/_DoOVy5BBNU?list=PL00KCN8NwzW6lP5tnY43YdH75xLLNs7aI`
- Checkbox: ❌ Import cả playlist
- Expected Preview: "Chỉ import video đơn lẻ này" (chỉ video đầu tiên)

### **3. Test Single Video Preview (Tick Checkbox):**
- URL: `https://www.youtube.com/watch?v=VIDEO_ID`
- Checkbox: ✅ Import cả playlist
- Expected: Error message

### **4. Test Single Video Preview (Bỏ Tick Checkbox):**
- URL: `https://www.youtube.com/watch?v=VIDEO_ID`
- Checkbox: ❌ Import cả playlist
- Expected Preview: "Chỉ import video đơn lẻ này"

## 📋 **Console Logs:**

### **Playlist URL + Tick Checkbox:**
```
Console: "Fetching YouTube info for: https://youtu.be/_DoOVy5BBNU?list=..."
Console: "Import playlist checkbox: true"
Console: "Detected playlist URL: https://youtu.be/_DoOVy5BBNU?list=..."
Console: "Playlist info: MV Nhạc Vàng Trữ Tình with 2 entries"
```

### **Playlist URL + Bỏ Tick Checkbox:**
```
Console: "Fetching YouTube info for: https://youtu.be/_DoOVy5BBNU?list=..."
Console: "Import playlist checkbox: false"
Console: "Detected playlist URL: https://youtu.be/_DoOVy5BBNU?list=..."
Console: "Converted playlist URL to single video for preview: https://youtu.be/_DoOVy5BBNU"
```

### **Single Video URL + Bỏ Tick Checkbox:**
```
Console: "Fetching YouTube info for: https://www.youtube.com/watch?v=..."
Console: "Import playlist checkbox: false"
Console: "Detected single video URL: https://www.youtube.com/watch?v=..."
```

---

## 🎵 **Expected Results:**

### **Playlist URL + Tick Checkbox:**
- Preview: Hiển thị playlist với thông báo "Tất cả bài hát sẽ được import với album"
- Import: Tạo album với tên playlist

### **Playlist URL + Bỏ Tick Checkbox:**
- Preview: Hiển thị single video với thông báo "Chỉ import video đơn lẻ này"
- Import: Tạo album "Artist - Single"

### **Single Video URL + Bỏ Tick Checkbox:**
- Preview: Hiển thị single video với thông báo "Chỉ import video đơn lẻ này"
- Import: Tạo album "Artist - Single"

**Logic Preview Checkbox đã hoàn thành - Test ngay! 🎵✨**

**Bây giờ preview sẽ hiển thị đúng chế độ import dựa trên checkbox!**
