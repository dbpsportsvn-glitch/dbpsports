# 🚀 Hướng Dẫn Test Nhanh - Offline Playback

## ⚡ Quick Fix (BẮT BUỘC CHẠY TRƯỚC!)

### Bước 1: Clear Service Worker Cache
Mở **DevTools Console** (F12) và paste:

```javascript
navigator.serviceWorker.getRegistrations().then(function(registrations) {
  for(let registration of registrations) {
    registration.unregister()
  }
  console.log('✅ Đã xóa toàn bộ Service Workers cũ');
  console.log('➡️ Bây giờ Hard Refresh (Ctrl + Shift + R)');
})
```

### Bước 2: Hard Refresh
- **Windows/Linux:** Ctrl + Shift + R
- **Mac:** Cmd + Shift + R

---

## 🧪 Test Script - Chạy Ngay!

Paste vào Console:

```javascript
(async function quickTest() {
    console.log('🧪 Quick Test cho Offline Playback\n');
    
    // Test 1: Browser Support
    if ('serviceWorker' in navigator) {
        console.log('✅ Service Worker supported');
    } else {
        console.error('❌ Browser không hỗ trợ Service Worker!');
        return;
    }
    
    // Test 2: Secure Context
    if (window.isSecureContext) {
        console.log(`✅ Secure context: ${location.protocol}//${location.hostname}`);
    } else {
        console.error('❌ KHÔNG secure! Cần HTTPS hoặc localhost');
        return;
    }
    
    // Test 3: Service Worker Status
    const regs = await navigator.serviceWorker.getRegistrations();
    if (regs.length === 0) {
        console.log('⏳ Service Worker chưa register. Đợi 2s...');
        await new Promise(r => setTimeout(r, 2000));
        const regs2 = await navigator.serviceWorker.getRegistrations();
        if (regs2.length > 0) {
            console.log('✅ Service Worker registered!');
            regs2.forEach(reg => {
                console.log(`   Scope: ${reg.scope}`);
                console.log(`   Active: ${reg.active ? 'YES ✅' : 'NO ❌'}`);
            });
        } else {
            console.error('❌ Service Worker không register được!');
            console.log('➡️ Check console cho lỗi từ service-worker.js');
        }
    } else {
        console.log(`✅ Found ${regs.length} Service Worker(s)`);
        regs.forEach(reg => {
            console.log(`   Scope: ${reg.scope}`);
            console.log(`   Active: ${reg.active ? 'YES ✅' : 'NO ❌'}`);
        });
    }
    
    // Test 4: Offline Manager
    if (typeof OfflineManager !== 'undefined') {
        console.log('✅ OfflineManager loaded');
    } else {
        console.error('❌ OfflineManager KHÔNG load được!');
        console.log('➡️ Check xem /static/js/offline-manager.js có accessible không');
    }
    
    // Test 5: Cache Check
    const cacheNames = await caches.keys();
    if (cacheNames.length === 0) {
        console.log('⚠️ Chưa có cache. Sẽ tạo khi bạn phát nhạc');
    } else {
        console.log(`✅ Found ${cacheNames.length} cache(s):`);
        for (const name of cacheNames) {
            const cache = await caches.open(name);
            const keys = await cache.keys();
            console.log(`   ${name}: ${keys.length} files`);
            
            if (name === 'dbp-music-v3-final') {
                console.log('   ✅ Correct cache version!');
            }
        }
    }
    
    console.log('\n📝 Next Steps:');
    console.log('1. Mở Music Player');
    console.log('2. Phát 1 bài nhạc');
    console.log('3. Check console cho log "Cached: ..."');
    console.log('4. Enable Offline (Network tab)');
    console.log('5. Phát lại bài → Nếu chạy được = SUCCESS! 🎉');
})()
```

---

## ✅ Expected Results

Nếu **MỌI THỨ OK**, bạn sẽ thấy:

```
🧪 Quick Test cho Offline Playback

✅ Service Worker supported
✅ Secure context: http://localhost:8000
✅ Found 1 Service Worker(s)
   Scope: http://localhost:8000/
   Active: YES ✅
✅ OfflineManager loaded
⚠️ Chưa có cache. Sẽ tạo khi bạn phát nhạc

📝 Next Steps:
...
```

---

## 🎵 Test Playback

### Step 1: Phát Nhạc
1. Click vào **Music** button (góc dưới)
2. Chọn playlist bất kỳ
3. Click phát 1 bài nhạc

### Step 2: Check Console
Khi phát nhạc, console phải hiện:

```
[Service Worker] 🎵 Intercepting audio request: /media/music/001-track.mp3
[Service Worker] Fetching from network: /media/music/001-track.mp3
[Service Worker] ✅ Cached: /media/music/001-track.mp3
✅ Track 1 cached - UI updated
```

### Step 3: Check Cache
DevTools → **Application** → **Cache Storage**
- Mở `dbp-music-v3-final`
- Phải thấy audio file vừa nghe

### Step 4: Test Offline
1. DevTools → **Network tab**
2. Check **"Offline"** checkbox
3. Phát lại bài vừa nghe
4. **Nếu phát được → THÀNH CÔNG! 🎉**

---

## ❌ Troubleshooting

### Lỗi: "Service Worker không register"

**Check 1:** File có accessible không?
```bash
curl http://localhost:8000/service-worker.js
```
Nên trả về JavaScript code.

**Check 2:** Console có lỗi không?
Xem tab Console, tìm lỗi màu đỏ liên quan đến Service Worker.

**Check 3:** Có phải HTTPS/localhost không?
Service Worker chỉ chạy trên:
- ✅ `https://`
- ✅ `localhost` hoặc `127.0.0.1`
- ❌ `http://other-domain.com`

---

### Lỗi: "OfflineManager not loaded"

**Fix:**
```bash
# Collect static files
cd backend
python manage.py collectstatic --noinput
```

Check file tồn tại:
```bash
curl http://localhost:8000/static/js/offline-manager.js
```

---

### Lỗi: "Không thấy cached icon trên track list"

**Debug:**
```javascript
// Check localStorage
JSON.parse(localStorage.getItem('dbp_cached_tracks'))

// Clear và test lại
localStorage.removeItem('dbp_cached_tracks')
location.reload()
```

---

## 📊 Full Test Script

Muốn test đầy đủ hơn? Load file test:

**Option 1: Load từ Console**
```javascript
// Fetch và run test script
fetch('/static/js/offline-test.js')
  .then(r => r.text())
  .then(code => eval(code))
```

**Option 2: Thêm vào base.html tạm thời**
```html
<!-- Thêm trước </body> -->
<script src="{% static 'js/offline-test.js' %}"></script>
```

---

## 🎯 Success Checklist

- [ ] Quick test script passed (không có ❌)
- [ ] Service Worker registered và active
- [ ] OfflineManager loaded
- [ ] Phát nhạc → Console hiện "Cached"
- [ ] Cache Storage có audio files
- [ ] Offline mode → Phát được nhạc cached
- [ ] Track list có icon cached (cloud-check màu xanh)
- [ ] Settings → Offline section hiện cache status

**Nếu TẤT CẢ ✅ → Tính năng hoạt động hoàn hảo!** 🎉

---

## 💡 Tips

1. **Luôn hard refresh** sau khi update code Service Worker
2. **Check Application tab** thường xuyên để monitor Service Worker
3. **Clear cache** khi debug: Application → Storage → Clear site data
4. **Monitor Network tab** để thấy requests từ cache

---

Có vấn đề? Gửi mình:
1. Screenshot console logs
2. Screenshot Application → Service Workers
3. URL đang test (localhost/production)
4. Browser name + version

Good luck! 🚀

