# 🔧 Fix Windows SIGALRM Issue

## Vấn Đề Đã Được Sửa

**Lỗi gốc:**
```
Lỗi khởi tạo yt-dlp: module 'signal' has no attribute 'SIGALRM'
```

**Nguyên nhân:**
- `signal.SIGALRM` không có sẵn trên Windows
- Code cũ sử dụng Unix signal handling

**Giải pháp:**
- Thay thế `signal.SIGALRM` bằng `threading.Thread` với `join(timeout=25)`
- Tương thích với cả Windows và Unix

## Code Fix

### Trước (Unix only):
```python
import signal

def timeout_handler(signum, frame):
    raise TimeoutError("yt-dlp extraction timeout")

signal.signal(signal.SIGALRM, timeout_handler)
signal.alarm(25)
```

### Sau (Cross-platform):
```python
import threading

def extract_info():
    nonlocal info, error
    try:
        info = ydl.extract_info(url, download=False)
    except Exception as e:
        error = e

thread = threading.Thread(target=extract_info)
thread.daemon = True
thread.start()
thread.join(timeout=25)
```

## Test Ngay Bây Giờ

Bây giờ bạn có thể test lại với URL:

```javascript
fetch('/music/youtube/info/', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
    },
    body: JSON.stringify({
        url: 'https://youtu.be/_DoOVy5BBNU?list=PL00KCN8NwzW6lP5tnY43YdH75xLLNs7aI',
        import_playlist: false
    })
})
.then(response => response.json())
.then(data => console.log('Result:', data));
```

## Kết Quả Mong Đợi

Bây giờ bạn sẽ thấy:

1. **✅ Success**: Nếu yt-dlp hoạt động bình thường
2. **⏰ Timeout**: Nếu yt-dlp mất quá 25 giây
3. **❌ Error**: Nếu có lỗi khác (cookie, network, etc.)

## Logs Sẽ Hiển Thị

```
YouTube info request from user username: URL=https://youtu.be/..., import_playlist=False
URL analysis: has_list_param=True, is_radio_mode=False, is_playlist=False
Using cookie file: /path/to/cookie.txt
yt-dlp options: {...}
Starting yt-dlp extraction for URL: https://youtu.be/...
yt-dlp extraction completed. Info keys: ['id', 'title', 'uploader', ...]
Processing as single video
Video info: title=..., uploader=..., duration=...
```

## Next Steps

1. **Test lại** với URL bạn đã thử
2. **Kiểm tra logs** trong Django console
3. **Xem response** trong F12 console
4. **Báo cáo kết quả** nếu vẫn có vấn đề
