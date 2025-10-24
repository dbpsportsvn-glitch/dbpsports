# Fix YouTube Import URL Detection - Radio Mode Issue

## Vấn đề
URL YouTube có chứa radio mode (`&list=RD...&start_radio=1`) không được xử lý đúng khi user chọn import file đơn lẻ (không tick "Import cả playlist").

**URL có vấn đề:**
```
https://www.youtube.com/watch?v=diIaUR4QcxQ&list=RDdiIaUR4QcxQ&start_radio=1
```

**Log lỗi:**
```
Opening YouTube Import modal
youtube_import.js?v=1.0.0:61 Preview clicked for URL: https://www.youtube.com/watch?v=diIaUR4QcxQ&list=RDdiIaUR4QcxQ&start_radio=1
youtube_import.js?v=1.0.0:81 Fetching YouTube info for: https://www.youtube.com/watch?v=diIaUR4QcxQ&list=RDdiIaUR4QcxQ&start_radio=1
youtube_import.js?v=1.0.0:83 Import playlist checkbox: false
```

## Nguyên nhân
1. **Logic detect playlist sai:** Code detect `&list=` và coi đây là playlist URL, nhưng thực tế đây chỉ là video với radio mode
2. **Logic chuyển đổi URL không đầy đủ:** Chỉ xử lý `?list=` mà không xử lý `&list=`
3. **Không phân biệt radio mode:** Radio mode (`RD...`) và playlist thực sự (`PL...`) bị xử lý giống nhau

## Giải pháp

### 1. Cải thiện logic detect playlist
**Trước:**
```python
is_playlist = '?list=' in youtube_url or '/playlist' in youtube_url
```

**Sau:**
```python
import re
has_list_param = bool(re.search(r'[?&]list=', youtube_url))
is_radio_mode = bool(re.search(r'[?&]list=RD', youtube_url))
is_playlist = '/playlist' in youtube_url or (has_list_param and not is_radio_mode)
```

### 2. Cải thiện logic chuyển đổi URL
**Thêm xử lý radio mode:**
```python
elif not is_playlist and '&list=' in youtube_url and not import_playlist:
    # URL có &list= (radio mode) nhưng user không muốn import playlist
    # Loại bỏ các parameter liên quan đến playlist/radio
    import re
    # Loại bỏ &list= và &start_radio= parameters
    youtube_url = re.sub(r'&list=[^&]*', '', youtube_url)
    youtube_url = re.sub(r'&start_radio=[^&]*', '', youtube_url)
    logger.info(f"Removed radio mode parameters: {youtube_url}")
```

### 3. Cập nhật JavaScript validation
**Cải thiện comment trong regex patterns:**
```javascript
const youtubePatterns = [
    /^https?:\/\/(www\.)?youtube\.com\/watch\?v=[\w-]+/,  // Single video (có thể có &list= cho radio mode)
    /^https?:\/\/(www\.)?youtube\.com\/playlist\?list=[\w-]+/,  // Playlist thực sự
    // ... other patterns
];
```

## Kết quả
- ✅ URL radio mode được detect đúng là single video
- ✅ Parameters `&list=RD...` và `&start_radio=1` được loại bỏ khi import single video
- ✅ Playlist thực sự (`PL...`) vẫn được detect đúng
- ✅ Tất cả test cases PASS

## Files đã sửa
1. `backend/music_player/youtube_import_views.py` - Logic backend
2. `backend/music_player/static/music_player/js/youtube_import.js` - Comments cải thiện

## Test Cases
- ✅ Single video: `https://www.youtube.com/watch?v=diIaUR4QcxQ`
- ✅ Single video with radio mode: `https://www.youtube.com/watch?v=diIaUR4QcxQ&list=RDdiIaUR4QcxQ&start_radio=1`
- ✅ Real playlist: `https://www.youtube.com/playlist?list=PLrAXtmRdnEQy6nuLMOV8V4qQ8Qz8v5bV`
- ✅ Video in playlist: `https://www.youtube.com/watch?v=abc123&list=PLrAXtmRdnEQy6nuLMOV8V4qQ8Qz8v5bV`

## Ngày sửa
2025-01-30

## Cập nhật thêm: Đổi mặc định Import Playlist
**Ngày:** 2025-01-30

### Thay đổi
Đổi mặc định checkbox "Import cả playlist" từ `checked` (true) sang `unchecked` (false) để mặc định import file đơn lẻ.

### Files đã sửa
1. `backend/music_player/templates/music_player/settings_modal.html` - Loại bỏ `checked` khỏi checkbox
2. `backend/music_player/static/music_player/js/youtube_import.js` - Cập nhật `resetYouTubeImportModal()` 
3. `backend/music_player/youtube_import_views.py` - Cập nhật default values từ `True` sang `False`

### Kết quả
- ✅ Mặc định: Import file đơn lẻ (checkbox không được tick)
- ✅ User có thể tick checkbox nếu muốn import cả playlist
- ✅ Đồng bộ giữa frontend và backend

## Cập nhật thêm: Sửa lỗi Toast và UI Refresh
**Ngày:** 2025-01-30

### Vấn đề
1. **Toast notification bị che:** Thông báo import thành công bị che bởi YouTube Import Modal
2. **UI không cập nhật:** Settings modal không refresh bài hát ngay sau khi import

### Giải pháp

#### 1. Sửa Z-Index Toast
- **Trước:** Toast có z-index `100002`, YouTube Modal có z-index `999999`
- **Sau:** Toast có z-index `1000000` (cao hơn tất cả modal)
- **Files:** `music_player.js`, `music_player.css`

#### 2. Cải thiện UI Refresh
- **Thêm comprehensive refresh:** Refresh playlists, user tracks, user playlists
- **Thêm event listener:** `youtubeImportCompleted` event để tự động refresh Settings modal
- **Async/await:** Đảm bảo refresh hoàn thành trước khi hiển thị toast
- **Files:** `youtube_import.js`, `user_music.js`

### Kết quả
- ✅ Toast notification hiển thị trên cùng, không bị che
- ✅ Settings modal tự động refresh ngay sau khi import
- ✅ Tất cả UI components được cập nhật đồng bộ
- ✅ Error handling robust cho refresh operations
