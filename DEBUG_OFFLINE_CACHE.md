# 🔍 DEBUG: OFFLINE CACHE KHÔNG HOẠT ĐỘNG

## ❓ **VẤN ĐỀ:**
- Console log: "📥 Auto-caching track: ..."
- Nhưng cache size vẫn: 0.00MB / 500MB
- Files không được cache

---

## 🧪 **DEBUG STEPS:**

### **1. Kiểm tra Service Worker Status**

```
F12 → Application tab → Service Workers

✅ ĐÚNG:
- Status: "activated and is running" (màu xanh)
- Scope: http://127.0.0.1:8000/

❌ SAI:
- Status: "waiting to activate" (màu vàng)
- Status: "redundant" (màu xám)
- Không thấy Service Worker
```

**FIX nếu sai:**
```
→ Click "Unregister"
→ Hard refresh: Ctrl+Shift+R
```

---

### **2. Kiểm tra Network Interception**

```
F12 → Network tab → Play bài hát → Click vào request audio file

✅ ĐÚNG:
- Size column: Có icon ⚙️ (Service Worker icon)
- hoặc "ServiceWorker" trong "Initiator"

❌ SAI:
- Không có icon ⚙️
- Request đi thẳng đến server
```

**FIX nếu sai:**
```javascript
// Check SW scope trong console:
navigator.serviceWorker.ready.then(reg => {
    console.log('SW Scope:', reg.scope);
    console.log('SW Active:', reg.active);
});
```

---

### **3. Kiểm tra URL Pattern Match**

```javascript
// Trong console (F12):
console.log('Audio URL:', document.querySelector('audio').src);

// URL phải chứa: "/media/music/"
// Ví dụ: http://127.0.0.1:8000/media/music/playlist/song.mp3
```

**FIX nếu sai:**
```javascript
// Sửa Service Worker pattern trong service-worker.js line 37:
if (url.pathname.includes('/media/music/')) {  // ← Check này
```

---

### **4. Kiểm tra Cache Storage**

```
F12 → Application tab → Cache Storage → "dbp-music-v1"

✅ ĐÚNG:
- Thấy các files audio trong list

❌ SAI:
- Cache empty
- Không thấy "dbp-music-v1"
```

**FIX nếu sai:**
```javascript
// Manually test cache trong console:
caches.open('dbp-music-v1').then(cache => {
    cache.add('/media/music/test.mp3').then(() => {
        console.log('✅ Manual cache success');
    }).catch(err => {
        console.error('❌ Cache failed:', err);
    });
});
```

---

### **5. Check Service Worker Console**

```
F12 → Console → Filter: service-worker.js

✅ ĐÚNG:
- [Service Worker] Fetching from network: ...
- [Service Worker] Cached: ...

❌ SAI:
- Không thấy logs từ Service Worker
- Có error logs
```

**FIX nếu sai:**
```
F12 → Application → Service Workers → Click "service-worker.js" link
→ Mở Service Worker console riêng
→ Xem errors
```

---

## 🔧 **GIẢI PHÁP PHỔ BIẾN:**

### **Vấn đề 1: Service Worker chưa control page**

**Triệu chứng:**
- SW registered nhưng không intercept requests
- Page load trước khi SW active

**Fix:**
```javascript
// Thêm vào base.html sau registration:
navigator.serviceWorker.register('/service-worker.js').then(reg => {
    // Force claim clients
    if (reg.active) {
        reg.active.postMessage({action: 'skipWaiting'});
    }
});

// Thêm vào service-worker.js:
self.addEventListener('activate', (event) => {
    event.waitUntil(clients.claim()); // ← Thêm dòng này
});
```

---

### **Vấn đề 2: CORS issues**

**Triệu chứng:**
- Console error: "CORS policy"
- Requests bị block

**Fix:**
```python
# settings.py
CORS_ALLOW_ALL_ORIGINS = True  # Dev only

# hoặc
CORS_ALLOWED_ORIGINS = [
    "http://127.0.0.1:8000",
    "http://localhost:8000",
]
```

---

### **Vấn đề 3: Cache không được save**

**Triệu chứng:**
- SW fetch OK nhưng cache.put() fails
- Quota exceeded

**Fix:**
```javascript
// Check quota trong console:
navigator.storage.estimate().then(estimate => {
    console.log('Storage:', 
        Math.round(estimate.usage / 1024 / 1024) + 'MB used of',
        Math.round(estimate.quota / 1024 / 1024) + 'MB quota'
    );
});
```

---

### **Vấn đề 4: Response không cacheable**

**Triệu chứng:**
- Response headers có `Cache-Control: no-store`
- Response opaque (từ cross-origin)

**Fix:**
```javascript
// Service Worker - thêm vào handleAudioRequest:
if (networkResponse.ok && networkResponse.headers.get('content-type')?.includes('audio')) {
    // Force cache despite headers
    const newHeaders = new Headers(networkResponse.headers);
    newHeaders.delete('cache-control');
    
    const cacheableResponse = new Response(networkResponse.body, {
        status: networkResponse.status,
        statusText: networkResponse.statusText,
        headers: newHeaders
    });
    
    await cache.put(request, cacheableResponse);
}
```

---

## 🚀 **QUICK FIX - THỬ NGAY:**

### **Step 1: Clear Everything**
```
1. F12 → Application
2. Clear storage → "Clear site data"
3. Ctrl+Shift+R (hard refresh)
```

### **Step 2: Verify SW**
```javascript
// Console:
navigator.serviceWorker.getRegistrations().then(regs => {
    console.log('Registrations:', regs.length);
    regs.forEach(reg => {
        console.log('  Scope:', reg.scope);
        console.log('  Active:', reg.active?.state);
    });
});
```

### **Step 3: Test Cache Manually**
```javascript
// Console - test cache functionality:
async function testCache() {
    try {
        const cache = await caches.open('test-cache');
        const response = new Response('test data');
        await cache.put('/test', response);
        const cached = await cache.match('/test');
        console.log('✅ Cache works:', await cached.text());
        await caches.delete('test-cache');
    } catch (err) {
        console.error('❌ Cache failed:', err);
    }
}
testCache();
```

### **Step 4: Force Fetch Through SW**
```javascript
// Thêm log vào service-worker.js line 33:
self.addEventListener('fetch', (event) => {
  console.log('[SW] Fetch event:', event.request.url); // ← ADD THIS
  const url = new URL(event.request.url);
  
  if (url.pathname.includes('/media/music/')) {
    console.log('[SW] Intercepting audio:', url.pathname); // ← ADD THIS
    event.respondWith(handleAudioRequest(event.request));
  }
});
```

---

## 📊 **EXPECTED BEHAVIOR:**

### **Lần đầu play bài:**
```
Console:
[SW] Fetch event: http://127.0.0.1:8000/media/music/...
[SW] Intercepting audio: /media/music/...
[Service Worker] Fetching from network: ...
[Service Worker] Cached: ...
📥 Auto-caching track: [Tên bài]
```

### **Play lại bài đã cache:**
```
Console:
[SW] Fetch event: http://127.0.0.1:8000/media/music/...
[Service Worker] Serving from cache: ...

Network tab:
Size: (from ServiceWorker)
```

### **Cache Status Update:**
```
Settings → Offline Playback:
📦 45.2MB / 500MB (9%)
▓▓░░░░░░░░

Track list:
♪ Bài hát ☁️✅  03:45
```

---

## 💡 **NẾU VẪN KHÔNG HOẠT ĐỘNG:**

### **Debug với detailed logs:**

Thêm vào `service-worker.js`:

```javascript
// Top of file
console.log('[SW] Service Worker script loaded');

self.addEventListener('install', (event) => {
  console.log('[SW] Installing...');
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  console.log('[SW] Activating...');
  event.waitUntil(
    clients.claim().then(() => {
      console.log('[SW] Claimed all clients');
    })
  );
});

self.addEventListener('fetch', (event) => {
  const url = new URL(event.request.url);
  console.log('[SW] Fetch:', url.pathname);
  
  if (url.pathname.includes('/media/music/')) {
    console.log('[SW] ✅ Audio request intercepted');
    event.respondWith(handleAudioRequest(event.request));
  } else {
    console.log('[SW] ➡️ Passing through');
  }
});

async function handleAudioRequest(request) {
  console.log('[SW] Handling audio:', request.url);
  
  try {
    const cachedResponse = await caches.match(request);
    if (cachedResponse) {
      console.log('[SW] ✅ Cache HIT');
      return cachedResponse;
    }
    
    console.log('[SW] ❌ Cache MISS - fetching...');
    const networkResponse = await fetch(request);
    
    if (networkResponse.ok) {
      const cache = await caches.open('dbp-music-v1');
      await cache.put(request, networkResponse.clone());
      console.log('[SW] ✅ Cached successfully');
    }
    
    return networkResponse;
  } catch (error) {
    console.error('[SW] ❌ Error:', error);
    throw error;
  }
}
```

Sau đó:
1. Save file
2. F12 → Application → Service Workers → Unregister
3. Hard refresh (Ctrl+Shift+R)
4. Play bài hát
5. Xem console logs chi tiết

---

## 📞 **SUPPORT:**

Nếu vẫn không được, gửi cho mình:
1. Full console logs
2. Network tab screenshot (filter: music)
3. Application → Service Workers screenshot
4. Application → Cache Storage screenshot

Mình sẽ debug chi tiết hơn! 🔧

