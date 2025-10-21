/**
 * Service Worker cho DBP Sports Music Player
 * Cho phép offline playback TRONG APP (không cho download file ra ngoài)
 */

const CACHE_VERSION = 'dbp-music-v4-range-fix';
const CACHE_LIMITS = {
  maxAge: 7 * 24 * 60 * 60 * 1000, // 7 days
  maxSize: 500 * 1024 * 1024 // 500MB max cache
};

// Install service worker
self.addEventListener('install', (event) => {
  // console.log('[Service Worker] Installing...');
  self.skipWaiting();
});

// Force update version - Production ready with URL encoding fix
const SW_VERSION = 'v11-production-clean';

// Activate service worker
self.addEventListener('activate', (event) => {
  // console.log('[Service Worker] Activating...');
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
      // ✅ Clean up small range request caches
      cleanupRangeRequests(),
      // ✅ Claim all clients immediately
      clients.claim().then(() => {
        // console.log('[Service Worker] Claimed all clients - ready to intercept!');
      })
    ])
  );
});

// Fetch strategy cho audio files
self.addEventListener('fetch', (event) => {
  const url = new URL(event.request.url);
  
  // Chỉ cache audio files
  if (url.pathname.includes('/media/music/')) {
    // console.log('[Service Worker] 🎵 Intercepting audio request:', url.pathname);
    event.respondWith(handleAudioRequest(event.request));
  }
});

/**
 * Handle audio request với cache-first strategy
 * ✅ Cache trong app để offline playback
 * ❌ KHÔNG cho user download file ra ngoài
 * 🔧 FIX: Handle Range requests properly - serve Range responses from cached full file
 */
async function handleAudioRequest(request) {
  try {
    const requestUrl = request.url.split('?')[0]; // Remove query params for cache matching
    const rangeHeader = request.headers.get('range');
    
    // 1. Thử lấy từ cache trước (IGNORE range header khi match)
    const cache = await caches.open(CACHE_VERSION);
    let cachedResponse = await cache.match(requestUrl);
    
    // Fallback: Try matching with decoded URL if first match fails
    if (!cachedResponse) {
      try {
        const decodedUrl = decodeURIComponent(requestUrl);
        cachedResponse = await cache.match(decodedUrl);
      } catch (e) {
        // Ignore decode errors
      }
    }
    
    // Fallback: Try matching with encoded URL if first match fails
    if (!cachedResponse) {
      try {
        const encodedUrl = encodeURI(requestUrl);
        cachedResponse = await cache.match(encodedUrl);
      } catch (e) {
        // Ignore encode errors
      }
    }
    
    if (cachedResponse) {
      // console.log('[Service Worker] ✅ Serving from cache:', requestUrl);
      
      // Nếu request có Range header, tạo Range response từ cached full file
      if (rangeHeader) {
        return createRangeResponse(cachedResponse, rangeHeader);
      }
      
      // Không có Range header, return full cached file
      return cachedResponse;
    }
    
    // 2. Không có trong cache, fetch từ network
    console.log('[Service Worker] Fetching from network:', requestUrl);
    
    // Luôn fetch FULL file để cache (bỏ range header)
    const fullRequest = new Request(requestUrl, {
      method: 'GET',
      headers: new Headers()
    });
    
    const fullResponse = await fetch(fullRequest);
    
    if (fullResponse.ok) {
      // Cache full file
      await cache.put(requestUrl, fullResponse.clone());
      // console.log('[Service Worker] ✅ Cached full file:', requestUrl);
      
      // Notify main thread
      const trackId = extractTrackIdFromUrl(requestUrl);
      if (trackId) {
        // console.log('[SW] Notifying clients about cached track:', trackId);
        self.clients.matchAll().then(clients => {
          clients.forEach(client => {
            client.postMessage({
              type: 'trackCached',
              trackId: trackId,
              url: requestUrl
            });
            // console.log('[SW] Message sent to client:', client.id);
          });
        }).catch(error => {
          console.error('[SW] Error sending message:', error);
        });
      }
      
      // Nếu original request có Range header, tạo Range response
      if (rangeHeader) {
        // console.log('[Service Worker] Creating Range response for new fetch:', rangeHeader);
        return createRangeResponse(fullResponse, rangeHeader);
      }
      
      // Return full response
      return fullResponse;
    }
    
    throw new Error('Network request failed');
    
  } catch (error) {
    console.error('🚨 Service Worker Error:', error.message);
    
    // Fallback: Trả về cached version nếu có
    const requestUrl = request.url.split('?')[0];
    const cache = await caches.open(CACHE_VERSION);
    const cachedResponse = await cache.match(requestUrl);
    
    if (cachedResponse) {
      console.log('📦 Serving from cache (offline mode)');
      const rangeHeader = request.headers.get('range');
      
      if (rangeHeader) {
        return createRangeResponse(cachedResponse, rangeHeader);
      }
      
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
 * Tạo Range response từ full cached response
 * Hỗ trợ browser seeking trong audio player
 */
async function createRangeResponse(response, rangeHeader) {
  try {
    const arrayBuffer = await response.clone().arrayBuffer();
    const totalLength = arrayBuffer.byteLength;
    
    // Parse Range header (format: "bytes=start-end")
    const rangeMatch = rangeHeader.match(/bytes=(\d+)-(\d*)/);
    if (!rangeMatch) {
      // Invalid range header, return full file
      return response;
    }
    
    const start = parseInt(rangeMatch[1], 10);
    const end = rangeMatch[2] ? parseInt(rangeMatch[2], 10) : totalLength - 1;
    
    // Validate range
    if (start >= totalLength || end >= totalLength || start > end) {
      console.error('[Service Worker] Range Not Satisfiable:', start, '-', end, '/', totalLength);
      return new Response('Range Not Satisfiable', { status: 416 });
    }
    
    // Extract requested byte range
    const rangeData = arrayBuffer.slice(start, end + 1);
    
    // Create Range response với proper headers
    const rangeResponse = new Response(rangeData, {
      status: 206, // Partial Content
      statusText: 'Partial Content',
      headers: new Headers({
        'Content-Type': response.headers.get('Content-Type') || 'audio/mpeg',
        'Content-Length': rangeData.byteLength.toString(),
        'Content-Range': `bytes ${start}-${end}/${totalLength}`,
        'Accept-Ranges': 'bytes'
      })
    });
    
    return rangeResponse;
    
  } catch (error) {
    console.error('🚨 Range Response Error:', error.message);
    // Fallback: return full response
    return response;
  }
}

/**
 * Extract track ID from URL
 */
function extractTrackIdFromUrl(url) {
  try {
    // console.log('[SW] Extracting track ID from:', url);
    
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
        // console.log('[SW] Found track ID:', trackId);
        return trackId;
      }
    }
    
    // console.log('[SW] No track ID found in URL');
    return null;
  } catch (error) {
    console.error('🚨 Track ID Extraction Error:', error.message);
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
  
  if (event.data.action === 'getCachedTracks') {
    const tracks = await getCachedTracks();
    event.ports[0].postMessage({ tracks });
  }
  
  if (event.data.action === 'cleanupRangeRequests') {
    await cleanupRangeRequests();
    event.ports[0].postMessage({ success: true });
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

/**
 * Cleanup range request caches (các file nhỏ < 500KB)
 * Chạy khi activate Service Worker
 */
async function cleanupRangeRequests() {
  try {
    const cache = await caches.open(CACHE_VERSION);
    const requests = await cache.keys();
    let deletedCount = 0;
    
    for (const request of requests) {
      const url = request.url;
      
      if (url.includes('/media/music/')) {
        const response = await cache.match(request);
        if (response) {
          const blob = await response.blob();
          const size = blob.size;
          
          // Xóa files nhỏ hơn 500KB (range requests)
          if (size < 500 * 1024) {
            await cache.delete(request);
            deletedCount++;
            // console.log(`[Service Worker] Deleted range request: ${url} (${(size / 1024).toFixed(2)} KB)`);
          }
        }
      }
    }
    
    if (deletedCount > 0) {
      // console.log(`[Service Worker] ✅ Cleaned up ${deletedCount} range request caches`);
    }
  } catch (error) {
    console.error('🚨 Cache Cleanup Error:', error.message);
  }
}

/**
 * Lấy danh sách các tracks đã cache với thông tin chi tiết
 */
async function getCachedTracks() {
  const cache = await caches.open(CACHE_VERSION);
  const requests = await cache.keys();
  const tracks = [];
  const seenUrls = new Set(); // Deduplicate by base URL
  
  for (const request of requests) {
    const url = request.url;
    
    // Chỉ lấy audio files
    if (url.includes('/media/music/')) {
      // Skip range requests - chỉ lấy full files
      // Range requests thường có URL base giống nhau
      const baseUrl = url.split('?')[0]; // Remove query params
      
      if (seenUrls.has(baseUrl)) {
        continue; // Skip duplicates
      }
      
      const response = await cache.match(request);
      if (response) {
        const blob = await response.blob();
        const size = blob.size;
        
        // Chỉ lấy files lớn hơn 500KB (bỏ qua range requests nhỏ)
        if (size < 500 * 1024) {
          continue;
        }
        
        const trackId = extractTrackIdFromUrl(url);
        
        // Extract filename from URL
        const urlParts = baseUrl.split('/');
        const filename = decodeURIComponent(urlParts[urlParts.length - 1]);
        
        seenUrls.add(baseUrl);
        tracks.push({
          url: baseUrl,
          filename: filename,
          size: size,
          sizeMB: (size / (1024 * 1024)).toFixed(2),
          trackId: trackId
        });
      }
    }
  }
  
  // Sort by filename
  tracks.sort((a, b) => a.filename.localeCompare(b.filename));
  
  return tracks;
}

