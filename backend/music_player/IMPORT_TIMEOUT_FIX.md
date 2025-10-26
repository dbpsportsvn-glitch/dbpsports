# 🚨 Fix Import Timeout Issue

## Vấn Đề Đã Được Sửa

**Vấn đề gốc:** Import treo ở 50% và không tiến thêm

**Nguyên nhân:**
1. **Progress tracking giả** - API `/music/youtube/progress/` chỉ trả về 50% cố định
2. **Không có timeout** - Request có thể treo vô thời hạn
3. **Không có cách hủy** - User không thể cancel khi bị treo

## ✅ **Các Fix Đã Áp Dụng:**

### 1. **Timeout Handling**
- **Frontend timeout**: 5 phút (300 giây)
- **Backend timeout**: 25 giây cho yt-dlp extraction
- **Auto cancel**: Tự động hủy khi timeout

### 2. **Progress Simulation**
- **Realistic progress**: Tăng dần từ 0% đến 90%
- **Smooth animation**: Cập nhật mỗi giây
- **Accurate completion**: Chỉ 100% khi thực sự hoàn thành

### 3. **Cancel Button**
- **Manual cancel**: User có thể hủy bất kỳ lúc nào
- **Confirmation dialog**: Xác nhận trước khi hủy
- **Clean cleanup**: Dọn dẹp resources khi hủy

### 4. **Better Error Handling**
- **Timeout errors**: Phân biệt timeout vs network errors
- **User-friendly messages**: Thông báo lỗi rõ ràng
- **Recovery options**: Hướng dẫn user thử lại

## 🔧 **Code Changes:**

### Frontend (youtube_import.js):
```javascript
// Timeout handling
const importController = new AbortController();
window.importController = importController;
const importTimeoutId = setTimeout(() => {
    importController.abort();
    showToast('Import timeout! File có thể quá lớn hoặc network chậm.', 'error');
}, 300000); // 5 minutes

// Progress simulation
let progressValue = 0;
const progressInterval = setInterval(() => {
    progressValue += Math.random() * 10;
    if (progressValue > 90) progressValue = 90;
    youtubeProgressFill.style.width = `${progressValue}%`;
}, 1000);

// Cancel button
cancelImportBtn.addEventListener('click', () => {
    if (confirm('Bạn có chắc chắn muốn hủy import?')) {
        if (window.importController) {
            window.importController.abort();
        }
        showToast('Import đã được hủy', 'warning');
    }
});
```

### Backend (youtube_import_views.py):
```python
# Windows-compatible timeout
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
thread.join(timeout=25)  # 25 seconds timeout
```

## 🎯 **Bây Giờ Bạn Sẽ Thấy:**

### ✅ **Success Case:**
- Progress tăng dần từ 0% → 90% → 100%
- Thông báo "Import thành công!"
- File xuất hiện trong playlist

### ⏰ **Timeout Case:**
- Progress dừng ở 90%
- Thông báo "Import timeout! File có thể quá lớn hoặc network chậm."
- Nút "Hủy Import" để cancel

### 🚫 **Cancel Case:**
- User click "Hủy Import"
- Confirmation dialog
- Progress dừng và cleanup

## 📊 **Debug Tips:**

### 1. **Kiểm Tra Console:**
```javascript
// Mở F12 Console để xem logs
🚀 [YouTube Import] Starting import request...
⏰ [YouTube Import] Import timeout after 5 minutes
💥 [YouTube Import] Import Error: AbortError
```

### 2. **Kiểm Tra Network:**
- Tab Network trong F12
- Xem request `/music/youtube/import/` có timeout không
- Kiểm tra response status

### 3. **Kiểm Tra Backend:**
- Django console logs
- Xem yt-dlp có hoạt động không
- Kiểm tra file download progress

## 🚀 **Test Ngay Bây Giờ:**

1. **Thử import** một video ngắn (< 5 phút)
2. **Xem progress** có tăng dần không
3. **Test cancel** bằng nút "Hủy Import"
4. **Test timeout** với video dài (> 5 phút)

## 📋 **Next Steps:**

Nếu vẫn có vấn đề:
1. **Kiểm tra console logs** trong F12
2. **Kiểm tra Django logs** trong terminal
3. **Test với video khác** (ngắn hơn)
4. **Kiểm tra cookie** có hợp lệ không
5. **Thử với URL đơn giản** trước
