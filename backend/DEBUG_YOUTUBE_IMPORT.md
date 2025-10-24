# 🐛 Debug YouTube Import - "Đang tải" Issue

## ✅ **Đã Sửa:**

### **1. JavaScript Rewrite:**
- ✅ **Simplified approach**: Bỏ class-based, dùng function-based
- ✅ **Better error handling**: Console.log để debug
- ✅ **Element validation**: Kiểm tra elements tồn tại
- ✅ **Toast notifications**: Hiển thị lỗi rõ ràng

### **2. Debug Features:**
- ✅ **Console logging**: Log mọi bước để debug
- ✅ **Error messages**: Hiển thị lỗi cụ thể
- ✅ **Response logging**: Log API response
- ✅ **Element checking**: Kiểm tra DOM elements

## 🔍 **Debug Steps:**

### **1. Mở Browser Console:**
- Press **F12** để mở Developer Tools
- Chuyển sang tab **Console**
- Refresh page (Ctrl+F5)

### **2. Test YouTube Import:**
- Click **"Import từ YouTube"**
- Nhập URL: `https://www.youtube.com/watch?v=dQw4w9WgXcQ`
- Click **"Xem Trước"**
- **Xem Console** để check lỗi

### **3. Check Console Messages:**
```
YouTube Import Handler loaded
Opening YouTube Import modal
Preview clicked for URL: https://www.youtube.com/watch?v=dQw4w9WgXcQ
Fetching YouTube info for: https://www.youtube.com/watch?v=dQw4w9WgXcQ
Response status: 200
Response data: {success: true, info: {...}}
```

## 🚨 **Possible Issues:**

### **1. Server Not Running:**
- Check if Django server is running
- URL: http://127.0.0.1:8000

### **2. API Endpoint Error:**
- Check `/music/youtube/info/` endpoint
- Verify yt-dlp is installed
- Check server logs

### **3. CSRF Token Issue:**
- Check if CSRF token is available
- Verify form has csrfmiddlewaretoken

### **4. JavaScript Error:**
- Check console for JavaScript errors
- Verify all elements exist in DOM

## 🛠️ **Quick Fixes:**

### **1. Restart Server:**
```bash
cd backend
.\venv\Scripts\python.exe manage.py runserver
```

### **2. Check API Directly:**
```bash
curl -X POST http://127.0.0.1:8000/music/youtube/info/ \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"}'
```

### **3. Check Browser Console:**
- Look for error messages
- Check network tab for failed requests
- Verify JavaScript is loading

## 🎯 **Expected Console Output:**

```
YouTube Import Handler loaded
Opening YouTube Import modal
Preview clicked for URL: https://www.youtube.com/watch?v=dQw4w9WgXcQ
Fetching YouTube info for: https://www.youtube.com/watch?v=dQw4w9WgXcQ
Response status: 200
Response data: {success: true, type: "video", title: "Never Gonna Give You Up", ...}
Toast success: Đã tải thông tin thành công!
```

## 🚀 **Next Steps:**

1. **Hard refresh** browser (Ctrl+F5)
2. **Open Console** (F12)
3. **Test YouTube Import**
4. **Check console messages**
5. **Report any errors**

---

**JavaScript đã được rewrite với debug features - Hãy check console để xem lỗi gì! 🔍**
