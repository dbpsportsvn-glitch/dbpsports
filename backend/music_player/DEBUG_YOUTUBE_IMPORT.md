# 🔍 Hướng Dẫn Debug YouTube Import

## Cách Kiểm Tra Logs

### 1. **Frontend Console (F12)**

Mở Developer Tools (F12) và xem tab **Console**. Bạn sẽ thấy các log với emoji:

```
🔍 [YouTube Import] Starting preview for URL: https://www.youtube.com/watch?v=...
✅ [YouTube Import] URL validation passed
📋 [YouTube Import] Request data: {url: "...", import_playlist: false}
🌐 [YouTube Import] Sending request to /music/youtube/info/
📡 [YouTube Import] Response received: {status: 200, ok: true}
📊 [YouTube Import] Response data: {success: true, info: {...}}
✅ [YouTube Import] Success! Info: {...}
🏁 [YouTube Import] Preview request completed
```

### 2. **Backend Logs**

Kiểm tra Django logs để xem backend processing:

```bash
# Trong terminal Django
tail -f logs/django.log | grep "YouTube"
```

Hoặc xem console Django server để thấy logs real-time.

## Các Trường Hợp Lỗi Thường Gặp

### ❌ **"xoay mãi không lấy được thông tin"**

**Nguyên nhân có thể:**

1. **yt-dlp timeout**: 
   - Log sẽ hiển thị: `Starting yt-dlp extraction for URL: ...`
   - Nhưng không có: `yt-dlp extraction completed`
   - **Giải pháp**: Tăng timeout hoặc kiểm tra cookie

2. **Cookie không hợp lệ**:
   - Log sẽ hiển thị: `Using cookie file: None` hoặc `Using cookie file: /path/to/invalid/cookie`
   - **Giải pháp**: Upload cookie mới từ trình duyệt

3. **Network issues**:
   - Log sẽ hiển thị: `💥 [YouTube Import] Network/JS Error`
   - **Giải pháp**: Kiểm tra kết nối internet

4. **YouTube blocking**:
   - Log sẽ hiển thị: `yt-dlp returned no info`
   - **Giải pháp**: Thử với cookie khác hoặc đợi một lúc

### 🔧 **Cách Debug Chi Tiết**

#### Bước 1: Kiểm tra Frontend
```javascript
// Mở Console và chạy:
console.log('Current URL:', document.getElementById('youtube-url').value);
console.log('CSRF Token:', document.querySelector('[name=csrfmiddlewaretoken]').value);
```

#### Bước 2: Test API trực tiếp
```javascript
// Test API endpoint
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
.then(response => response.json())
.then(data => console.log('API Response:', data));
```

#### Bước 3: Kiểm tra Cookie Status
```javascript
// Kiểm tra cookie
fetch('/music/youtube/cookie/status/', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
    }
})
.then(response => response.json())
.then(data => console.log('Cookie Status:', data));
```

## Các Log Patterns Cần Chú Ý

### ✅ **Success Pattern**
```
🔍 [YouTube Import] Starting preview for URL: ...
✅ [YouTube Import] URL validation passed
📋 [YouTube Import] Request data: ...
🌐 [YouTube Import] Sending request to /music/youtube/info/
📡 [YouTube Import] Response received: {status: 200, ok: true}
📊 [YouTube Import] Response data: {success: true, ...}
✅ [YouTube Import] Success! Info: ...
🏁 [YouTube Import] Preview request completed
```

### ❌ **Error Patterns**

#### Network Error
```
🔍 [YouTube Import] Starting preview for URL: ...
✅ [YouTube Import] URL validation passed
📋 [YouTube Import] Request data: ...
🌐 [YouTube Import] Sending request to /music/youtube/info/
💥 [YouTube Import] Network/JS Error: TypeError: Failed to fetch
🏁 [YouTube Import] Preview request completed
```

#### API Error
```
🔍 [YouTube Import] Starting preview for URL: ...
✅ [YouTube Import] URL validation passed
📋 [YouTube Import] Request data: ...
🌐 [YouTube Import] Sending request to /music/youtube/info/
📡 [YouTube Import] Response received: {status: 500, ok: false}
📊 [YouTube Import] Response data: {success: false, error: "..."}
❌ [YouTube Import] API Error: ...
🏁 [YouTube Import] Preview request completed
```

#### yt-dlp Timeout
```
🔍 [YouTube Import] Starting preview for URL: ...
✅ [YouTube Import] URL validation passed
📋 [YouTube Import] Request data: ...
🌐 [YouTube Import] Sending request to /music/youtube/info/
📡 [YouTube Import] Response received: {status: 200, ok: true}
📊 [YouTube Import] Response data: {success: false, error: "..."}
❌ [YouTube Import] API Error: ...
🏁 [YouTube Import] Preview request completed
```

## Troubleshooting Steps

### 1. **Kiểm tra URL**
- Đảm bảo URL YouTube hợp lệ
- Thử với video đơn giản trước (không playlist)

### 2. **Kiểm tra Cookie**
- Upload cookie mới từ trình duyệt
- Kiểm tra cookie status trong UI

### 3. **Kiểm tra Network**
- Thử với URL khác
- Kiểm tra kết nối internet

### 4. **Kiểm tra Server**
- Xem Django logs
- Kiểm tra yt-dlp có hoạt động không

### 5. **Test với URL đơn giản**
```
https://www.youtube.com/watch?v=dQw4w9WgXcQ
```

## Quick Fixes

### Tăng Timeout
Nếu thấy timeout, có thể tăng timeout trong code:
```python
'timeout': 30,  # Tăng từ 15 lên 30
```

### Disable Cookie
Nếu cookie gây vấn đề, có thể tạm thời disable:
```python
'cookiefile': None,  # Thay vì cookie_path
```

### Test với yt-dlp trực tiếp
```bash
yt-dlp --dump-json "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
```

## Liên Hệ Support

Nếu vẫn không giải quyết được, hãy cung cấp:
1. **Console logs** từ F12
2. **Django logs** từ server
3. **URL** bạn đang test
4. **Cookie status** (có/không có cookie)
5. **Error message** cụ thể
