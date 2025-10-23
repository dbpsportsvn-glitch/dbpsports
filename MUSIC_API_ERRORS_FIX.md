# Fix Music API Errors & Upload Enhancement

## Thay Đổi Upload Quota

### **Tăng Dung Lượng Upload Tối Đa Theo Quota**
**Trước đây:**
- Giới hạn cứng 50MB/file
- Không linh hoạt với quota của user

**Giải pháp:**
- ✅ Loại bỏ giới hạn 50MB cố định
- ✅ Max file size = remaining quota của user
- ✅ Nếu user còn 200MB quota → có thể upload file 200MB
- ✅ Nếu user còn 50MB quota → chỉ upload được file ≤ 50MB
- ✅ Error message chi tiết hiển thị quota còn lại và size file

**Code Changes:**
```python
# Check storage quota before validating file size
usage = user_settings.get_upload_usage()
remaining_bytes = usage['remaining'] * 1024 * 1024

if uploaded_file.size > remaining_bytes:
    max_size_mb = round(remaining_bytes / (1024 * 1024), 1)
    return JsonResponse({
        'success': False,
        'error': f'File quá lớn. Bạn còn {max_size_mb}MB quota. File của bạn là {round(uploaded_file.size / (1024 * 1024), 1)}MB.'
    }, status=400)
```

## Các Lỗi Gặp Phải

### 1. **500 Internal Server Error** tại `/music/stats/record-play/`
**Nguyên nhân:**
- JSON parsing error không được xử lý đúng cách
- Exception handling không đầy đủ
- Thiếu logging để debug

**Giải pháp đã áp dụng:**
- ✅ Thêm try-catch riêng cho JSON parsing
- ✅ Thêm logging chi tiết với `logger.error()` và `exc_info=True`
- ✅ Cải thiện error messages cho các trường hợp lỗi cụ thể

### 2. **400 Bad Request** tại `/music/user/tracks/upload/`
**Nguyên nhân:**
- Validation error khi upload file
- Có thể do file không hợp lệ hoặc thiếu thông tin

**Giải pháp đã áp dụng:**
- ✅ Thêm logging chi tiết để debug validation errors
- ✅ Cải thiện error handling trong upload function

### 3. **429 Too Many Requests** tại `/music/user/tracks/upload/`
**Nguyên nhân:**
- Rate limiting quá chặt (10 requests/phút)
- Người dùng upload nhiều file cùng lúc

**Giải pháp đã áp dụng:**
- ✅ Tăng rate limit từ 10 lên 20 requests/phút
- Rate limit giờ: **Max 20 uploads per minute**

## Chi Tiết Code Changes

### `backend/music_player/stats_views.py`
```python
# Thêm logging
import logging
logger = logging.getLogger(__name__)

# Improve JSON parsing với try-catch riêng
try:
    data = json.loads(request.body)
except json.JSONDecodeError as e:
    return JsonResponse({
        'success': False,
        'error': f'Invalid JSON: {str(e)}'
    }, status=400)

# Improve exception handling với logging
except Exception as e:
    logger.error(f"Error recording track play: {str(e)}", exc_info=True)
    return JsonResponse({
        'success': False,
        'error': str(e)
    }, status=500)
```

### `backend/music_player/user_music_views.py`
```python
# Thêm logging
import logging
logger = logging.getLogger(__name__)

# Tăng rate limit
@rate_limit(max_requests=20, window=60)  # Max 20 uploads per minute

# Improve exception handling với logging
except Exception as e:
    logger.error(f"Error uploading track: {str(e)}", exc_info=True)
    return JsonResponse({
        'success': False,
        'error': str(e)
    }, status=500)
```

## Kết Quả

✅ **Upload Enhancement:** Max file size theo quota (linh hoạt, không còn giới hạn 50MB)  
✅ **500 Error:** Đã fix với improved error handling và logging  
✅ **400 Error:** Đã thêm logging để debug  
✅ **429 Error:** Đã tăng rate limit lên 20 requests/phút  

## Testing

Sau khi deploy, kiểm tra:
1. **Upload Enhancement:** User có thể upload file lớn đến bằng quota còn lại
2. **Tracking play:** Hoạt động không còn 500 error
3. **Upload file:** Hoạt động bình thường
4. **Rate limiting:** Không còn quá chặt (20 requests/phút)
5. **Error messages:** Hiển thị chi tiết quota còn lại và size file

## Logging

Giờ có thể check logs trong Django console để debug:
- `Error recording track play:` - Lỗi tracking
- `Error uploading track:` - Lỗi upload

