# 🔧 Offline Playback - Fixes & Testing Guide

## ✅ Lỗi Đã Fix

### 1. **Cache Version Mismatch** (CRITICAL BUG)
**Vấn đề:** 
- Service Worker dùng cache name: `'dbp-music-v3-final'`
- Offline Manager check cache với name: `'dbp-music-v1'`
- Kết quả: Không thể check được track nào đã cached!

**Fix:**
```javascript
// backend/static/js/offline-manager.js - Line 199
const cache = await caches.open('dbp-music-v3-final'); // ✅ Đã sửa
```

---

## 🔍 Các Vấn Đề Tiềm Ẩn Khác

### 2. **Service Worker Cache (Browser Cache Issue)**

Service Worker có thể bị cache trong browser và không update lên version mới!

**Cách Fix:**
1. Mở Chrome DevTools (F12)
2. Application tab → Service Workers
3. Check "Update on reload"
4. Nhấn "Unregister" để xóa Service Worker cũ
5. Hard refresh (Ctrl + Shift + R hoặc Cmd + Shift + R)

**Hoặc dùng command:**
```javascript
// Paste vào Console để unregister toàn bộ Service Workers
navigator.serviceWorker.getRegistrations().then(function(registrations) {
  for(let registration of registrations) {
    registration.unregister()
  }
})
```

---

### 3. **HTTPS Requirement**

Service Workers **CHỈ hoạt động trên:**
- ✅ `https://` (production)
- ✅ `localhost` hoặc `127.0.0.1` (development)
- ❌ `http://` (production) - KHÔNG HOẠT ĐỘNG!

**Nếu đang test trên production HTTP:**
→ Cần setup HTTPS để Service Worker hoạt động!

---

## 🧪 Cách Test Tính Năng

### Bước 1: Clear Service Worker (Bắt buộc!)
```javascript
// Chạy trong Console
navigator.serviceWorker.getRegistrations().then(function(registrations) {
  for(let registration of registrations) {
    registration.unregister()
  }
})
```

### Bước 2: Hard Refresh
- Chrome: `Ctrl + Shift + R` (Windows) hoặc `Cmd + Shift + R` (Mac)
- Hoặc: DevTools → Right click refresh button → "Empty Cache and Hard Reload"

### Bước 3: Check Service Worker Registration
```javascript
// Chạy trong Console
navigator.serviceWorker.getRegistrations().then(regs => {
  console.log('Service Workers:', regs);
  regs.forEach(reg => {
    console.log('- Scope:', reg.scope);
    console.log('- Active:', reg.active);
  });
})
```

**Expected Output:**
```
Service Workers: [ServiceWorkerRegistration]
- Scope: http://localhost:8000/ (hoặc https://yourdomain.com/)
- Active: ServiceWorker
```

### Bước 4: Test Offline Playback

1. **Mở Music Player** → Chọn playlist → Phát 1 bài nhạc
2. **Kiểm tra Console logs:**
   ```
   ✅ Service Worker registered successfully
   ✅ Offline Manager initialized
   🎵 Intercepting audio request: /media/music/001-track.mp3
   ✅ Cached: /media/music/001-track.mp3
   ```

3. **Check cache trong DevTools:**
   - Application tab → Cache Storage
   - Mở cache `dbp-music-v3-final`
   - Xem các audio files đã cached

4. **Test offline:**
   - DevTools → Network tab → Check "Offline"
   - Phát lại bài nhạc vừa nghe
   - Nếu phát được → Offline playback hoạt động! ✅

---

## 🐛 Debug Common Errors

### Lỗi: "Service Worker not supported"
**Nguyên nhân:** 
- Browser cũ không hỗ trợ Service Worker
- Đang dùng HTTP (không phải HTTPS hoặc localhost)

**Fix:** 
- Update browser mới
- Dùng HTTPS hoặc localhost

---

### Lỗi: "ServiceWorker registration failed"
**Nguyên nhân:** 
- File `service-worker.js` không tồn tại hoặc không accessible
- Scope không đúng

**Check:**
```bash
# Kiểm tra file có tồn tại không
ls -la backend/service-worker.js

# Kiểm tra URL có accessible không
curl http://localhost:8000/service-worker.js
```

**Fix trong Django:**
Đảm bảo `urls.py` có route cho Service Worker:
```python
path('service-worker.js', service_worker, name='service_worker'),
```

---

### Lỗi: "Track không hiện icon cached"
**Nguyên nhân:** 
- Track chưa thực sự được cache
- Message từ Service Worker → Music Player bị miss
- localStorage không sync với thực tế

**Debug:**
```javascript
// Check cached tracks trong localStorage
JSON.parse(localStorage.getItem('dbp_cached_tracks'))

// Check cache thực tế trong Service Worker
caches.open('dbp-music-v3-final').then(cache => {
  cache.keys().then(requests => {
    console.log('Cached files:', requests.map(r => r.url));
  });
})
```

**Fix:**
- Xóa localStorage: `localStorage.removeItem('dbp_cached_tracks')`
- Refresh page
- Phát lại track để cache lại

---

## 🎯 Checklist Hoàn Chỉnh

### Before Testing:
- [ ] Clear Service Worker cache (Unregister old ones)
- [ ] Hard refresh browser (Ctrl + Shift + R)
- [ ] Check HTTPS/localhost requirement
- [ ] Mở DevTools Console để monitor logs

### Testing Flow:
- [ ] Service Worker registered successfully? (Check console)
- [ ] Offline Manager initialized? (Check console)
- [ ] Phát 1 bài nhạc → Check console for "Cached" message
- [ ] Check Cache Storage trong DevTools → có file audio?
- [ ] Enable Offline mode → Phát lại bài → Có chạy được không?
- [ ] Icon cached có hiện trong track list không?

### Settings Modal:
- [ ] Cache status có hiện không? (số MB/MB)
- [ ] Progress bar có đúng không?
- [ ] "Clear Cache" button hoạt động?
- [ ] "Refresh" button hoạt động?

---

## 📝 Console Logs Quan Trọng

**Khi mọi thứ hoạt động ĐÚNG, bạn sẽ thấy:**

```
✅ Service Worker registered successfully: http://localhost:8000/
✅ Offline Manager initialized
✅ Service Worker Installing...
✅ Service Worker Activating...
✅ Service Worker Claimed all clients - ready to intercept!
🎵 Intercepting audio request: /media/music/001-track.mp3
✅ Cached full file: /media/music/001-track.mp3
✅ Track 1 cached - UI updated
📦 Cache: 5.2MB / 500MB (1%)
```

**Nếu có LỖI, bạn sẽ thấy:**

```
❌ Service Worker registration failed: [error details]
⚠️ Service Worker not supported
⚠️ OfflineManager not loaded. Offline features disabled.
❌ Failed to initialize Offline Manager: [error]
```

---

## 🚀 Next Steps

1. **Clear Service Worker** (bắt buộc!)
2. **Hard refresh browser**
3. **Test theo checklist**
4. **Check console logs**
5. **Report back kết quả!**

---

## 📞 Nếu Vẫn Lỗi?

Gửi cho mình:
1. Screenshot console logs (đầy đủ)
2. Screenshot Application → Service Workers
3. Screenshot Application → Cache Storage
4. URL đang test (localhost hay production?)
5. Browser name + version

Good luck! 🎉

