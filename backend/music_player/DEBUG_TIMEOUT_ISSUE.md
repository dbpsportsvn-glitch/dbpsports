# 🚨 Debug YouTube Import - Vấn Đề "Xoay Mãi"

## Vấn Đề Hiện Tại

Từ logs bạn cung cấp, tôi thấy:
```
🌐 [YouTube Import] Sending request to /music/youtube/info/
```

Nhưng không có response trả về. Điều này có nghĩa là **backend đang bị treo** hoặc **yt-dlp timeout**.

## 🔧 Các Bước Debug

### Bước 1: Test Endpoint Cơ Bản

Mở Console F12 và chạy:

```javascript
// Test endpoint cơ bản
fetch('/music/youtube/test/', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
    }
})
.then(response => response.json())
.then(data => console.log('Test endpoint:', data));
```

**Kết quả mong đợi:**
```json
{
    "success": true,
    "message": "Test endpoint hoạt động bình thường",
    "timestamp": "2025-10-25T...",
    "user": "username"
}
```

### Bước 2: Test với URL Đơn Giản

```javascript
// Test với URL đơn giản
fetch('/music/youtube/info/', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
    },
    body: JSON.stringify({
        url: 'https://www.youtube.com/watch?v=dQw4w9WgXcQ',
        import_playlist: false
    })
})
.then(response => {
    console.log('Response status:', response.status);
    return response.json();
})
.then(data => console.log('YouTube info:', data))
.catch(error => console.error('Error:', error));
```

### Bước 3: Kiểm Tra Django Logs

Trong terminal Django server, bạn sẽ thấy:

```
YouTube info request from user username: URL=https://..., import_playlist=False
URL analysis: has_list_param=False, is_radio_mode=False, is_playlist=False
Using cookie file: /path/to/cookie.txt
yt-dlp options: {...}
Starting yt-dlp extraction for URL: https://...
```

**Nếu dừng ở đây** → yt-dlp bị treo

**Nếu có lỗi** → sẽ thấy error message

## 🚨 Các Vấn Đề Có Thể Xảy Ra

### 1. **yt-dlp Timeout**
- **Triệu chứng**: Request gửi đi nhưng không có response
- **Nguyên nhân**: yt-dlp bị treo khi extract info
- **Giải pháp**: Đã thêm timeout 25s, sẽ trả về error 408

### 2. **Cookie Invalid**
- **Triệu chứng**: yt-dlp không thể authenticate
- **Nguyên nhân**: Cookie hết hạn hoặc không hợp lệ
- **Giải pháp**: Upload cookie mới

### 3. **Network Issues**
- **Triệu chứng**: Connection timeout
- **Nguyên nhân**: Firewall hoặc network blocking
- **Giải pháp**: Kiểm tra network

### 4. **YouTube Blocking**
- **Triệu chứng**: yt-dlp trả về empty result
- **Nguyên nhân**: YouTube detect bot
- **Giải pháp**: Thử với cookie khác

## 🔧 Quick Fixes

### Fix 1: Tăng Timeout
Nếu vẫn timeout, có thể tăng timeout trong code:

```python
# Trong youtube_import_views.py
signal.alarm(60)  # Tăng từ 25 lên 60 giây
```

### Fix 2: Disable Cookie Tạm Thời
```python
# Trong youtube_import_views.py
'cookiefile': None,  # Thay vì cookie_path
```

### Fix 3: Test với yt-dlp Trực Tiếp
```bash
# Trong terminal
yt-dlp --dump-json "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
```

## 📋 Checklist Debug

- [ ] Test endpoint cơ bản hoạt động
- [ ] Cookie status hiển thị đúng
- [ ] Django logs hiển thị request
- [ ] yt-dlp extraction bắt đầu
- [ ] yt-dlp extraction hoàn thành
- [ ] Response trả về frontend

## 🎯 Next Steps

1. **Chạy test endpoint** để xác nhận server hoạt động
2. **Kiểm tra Django logs** để xem backend processing
3. **Thử với URL đơn giản** trước
4. **Kiểm tra cookie** có hợp lệ không
5. **Test yt-dlp trực tiếp** nếu cần

## 📞 Support

Nếu vẫn không giải quyết được, hãy cung cấp:
1. **Kết quả test endpoint**
2. **Django logs** từ server
3. **Console logs** từ F12
4. **URL** bạn đang test
5. **Cookie status** hiện tại
