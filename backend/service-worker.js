/**
 * Service Worker cho DBP Sports Music Player
 * Cho phép offline playback TRONG APP (không cho download file ra ngoài)
 */

const CACHE_VERSION = 'dbp-music-v3-final';
const CACHE_LIMITS = {
  maxAge: 7 * 24 * 60 * 60 * 1000, // 7 days
  maxSize: 500 * 1024 * 1024 // 500MB max cache
};

// Install service worker
self.addEventListener('install', (event) => {
  console.log('[Service Worker] Installing...');
  self.skipWaiting();
});

// Force update version
const SW_VERSION = 'v2-fix-206';

// Activate service worker
self.addEventListener('activate', (event) => {
  console.log('[Service Worker] Activating...');
  event.waitUntil(
    Promise.all([
      // Clean old caches
      caches.keys().then((cacheNames) => {
        return Promise.all(
          cacheNames
            .filter((cacheName) => cacheName !== CACHE_VERSION)
            .map((cacheName) => caches.delete(cacheName))
        );
      }),
      // ✅ Claim all clients immediately
      clients.claim().then(() => {
        console.log('[Service Worker] Claimed all clients - ready to intercept!');
      })
    ])
  );
});

// Fetch strategy cho audio files
self.addEventListener('fetch', (event) => {
  const url = new URL(event.request.url);
  
  // Chỉ cache audio files
  if (url.pathname.includes('/media/music/')) {
    console.log('[Service Worker] 🎵 Intercepting audio request:', url.pathname);
    event.respondWith(handleAudioRequest(event.request));
  }
});

/**
 * Handle audio request với cache-first strategy
 * ✅ Cache trong app để offline playback
 * ❌ KHÔNG cho user download file ra ngoài
 * 🔧 FIX: Handle Range requests (HTTP 206) properly
 */
async function handleAudioRequest(request) {
  try {
    // 1. Thử lấy từ cache trước
    const cachedResponse = await caches.match(request);
    if (cachedResponse) {
      console.log('[Service Worker] Serving from cache:', request.url);
      return cachedResponse;
    }
    
    // 2. Nếu không có trong cache, fetch từ network
    console.log('[Service Worker] Fetching from network:', request.url);
    
    // 🔧 FIX: Check if this is a range request
    const hasRange = request.headers.get('range');
    
    if (hasRange) {
      // Range request - fetch full file for caching, return partial for playback
      console.log('[Service Worker] Range request detected, fetching full file...');
      
      // Fetch full file (no range header)
      const fullRequest = new Request(request.url, {
        method: 'GET',
        headers: new Headers()
      });
      
      const fullResponse = await fetch(fullRequest);
      
      if (fullResponse.ok) {
        // Cache the full file
        const cache = await caches.open(CACHE_VERSION);
        await cache.put(request.url, fullResponse.clone());
        console.log('[Service Worker] ✅ Cached full file:', request.url);
        
        // Notify main thread
        const trackId = extractTrackIdFromUrl(request.url);
        if (trackId) {
          console.log('[SW] Notifying clients about cached track:', trackId);
          self.clients.matchAll().then(clients => {
            clients.forEach(client => {
              client.postMessage({
                type: 'trackCached',
                trackId: trackId,
                url: request.url
              });
              console.log('[SW] Message sent to client:', client.id);
            });
          }).catch(error => {
            console.error('[SW] Error sending message:', error);
          });
        }
      }
      
      // Return original range request
      return fetch(request);
    } else {
      // Normal request - fetch and cache
      const networkResponse = await fetch(request);
      
      if (networkResponse.ok) {
        const cache = await caches.open(CACHE_VERSION);
        await cache.put(request.url, networkResponse.clone());
        console.log('[Service Worker] ✅ Cached:', request.url);
        
        // Notify main thread
        const trackId = extractTrackIdFromUrl(request.url);
        if (trackId) {
          console.log('[SW] Notifying clients about cached track:', trackId);
          self.clients.matchAll().then(clients => {
            clients.forEach(client => {
              client.postMessage({
                type: 'trackCached',
                trackId: trackId,
                url: request.url
              });
              console.log('[SW] Message sent to client:', client.id);
            });
          }).catch(error => {
            console.error('[SW] Error sending message:', error);
          });
        }
      }
      
      return networkResponse;
    }
    
  } catch (error) {
    console.error('[Service Worker] Fetch failed:', error);
    
    // Fallback: Trả về cached version nếu có
    const cachedResponse = await caches.match(request.url);
    if (cachedResponse) {
      console.log('[Service Worker] Serving cached fallback:', request.url);
      return cachedResponse;
    }
    
    // Trả về error response
    return new Response('Offline and no cache available', {
      status: 503,
      statusText: 'Service Unavailable'
    });
  }
}

/**
 * Extract track ID from URL
 */
function extractTrackIdFromUrl(url) {
  try {
    console.log('[SW] Extracting track ID from:', url);
    
    // Try different patterns - FIXED for actual URL format
    const patterns = [
      /(\d{3})\s*-\s*/,          // 001 - TITLE.mp3
      /(\d{3})%20-%20/,          // 001%20-%20TITLE.mp3 (URL encoded)
      /playlist\/(\d{3})/,       // playlist/001
      /track_(\d+)\./,           // track_123.mp3
      /\/(\d+)\.mp3/,            // /123.mp3
      /\/(\d+)\//,               // /123/
      /playlist\/(\d+)/          // playlist/123
    ];
    
    for (const pattern of patterns) {
      const match = url.match(pattern);
      if (match) {
        const trackId = parseInt(match[1]);
        console.log('[SW] Found track ID:', trackId);
        return trackId;
      }
    }
    
    console.log('[SW] No track ID found in URL');
    return null;
  } catch (error) {
    console.error('[SW] Error extracting track ID:', error);
    return null;
  }
}

/**
 * Message handler để quản lý cache từ main thread
 */
self.addEventListener('message', async (event) => {
  if (event.data.action === 'clearCache') {
    const cache = await caches.open(CACHE_VERSION);
    await cache.delete(event.data.url);
    event.ports[0].postMessage({ success: true });
  }
  
  if (event.data.action === 'getCacheSize') {
    const size = await getCacheSize();
    event.ports[0].postMessage({ size });
  }
  
  if (event.data.action === 'preloadTrack') {
    // Preload track vào cache
    const url = event.data.url;
    try {
      await fetch(url);
      event.ports[0].postMessage({ success: true });
    } catch (error) {
      event.ports[0].postMessage({ success: false, error: error.message });
    }
  }
});

/**
 * Tính tổng size của cache
 */
async function getCacheSize() {
  const cache = await caches.open(CACHE_VERSION);
  const requests = await cache.keys();
  let totalSize = 0;
  
  for (const request of requests) {
    const response = await cache.match(request);
    if (response) {
      const blob = await response.blob();
      totalSize += blob.size;
    }
  }
  
  return totalSize;
}

