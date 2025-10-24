/**
 * Service Worker cho DBP Sports Music Player
 * Cho phép offline playback TRONG APP (không cho download file ra ngoài)
 */

const CACHE_VERSION = 'dbp-music-v4-range-fix';
const CACHE_LIMITS = {
  maxAge: 7 * 24 * 60 * 60 * 1000, // 7 days
};

// ✅ Auto-cache setting (persistent across SW reloads)
let autoCacheEnabled = true; // Default: enabled

// ✅ User interaction tracking để chỉ cache khi user thực sự sử dụng music player
let userHasInteracted = false;

// ✅ Load auto-cache setting from storage ngay khi SW start
(async function initAutoCacheSetting() {
  try {
    const cache = await caches.open(CACHE_VERSION);
    const cachedSetting = await cache.match('/auto-cache-setting');
    if (cachedSetting) {
      const data = await cachedSetting.json();
      autoCacheEnabled = data.enabled;
      // Loaded auto-cache setting
    }
  } catch (e) {
    // Ignore - use default
  }
})();

// ✅ Load auto-cache setting from storage khi SW activate (backup)
async function loadAutoCacheSetting() {
  try {
    const cache = await caches.open(CACHE_VERSION);
    const cachedSetting = await cache.match('/auto-cache-setting');
    if (cachedSetting) {
      const data = await cachedSetting.json();
      autoCacheEnabled = data.enabled;
      // Loaded auto-cache setting
    }
  } catch (e) {
    // Ignore - use default
  }
}

// ✅ Save auto-cache setting to storage
async function saveAutoCacheSetting(enabled) {
  try {
    const cache = await caches.open(CACHE_VERSION);
    await cache.put('/auto-cache-setting', new Response(JSON.stringify({ enabled })));
  } catch (e) {
    console.error('[Service Worker] Failed to save auto-cache setting:', e);
  }
}

// Install service worker
self.addEventListener('install', (event) => {
  // console.log('[Service Worker] Installing...');
  self.skipWaiting();
});

// Force update version - Complete track deletion rewrite
const SW_VERSION = 'v17-complete-deletion-rewrite';

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
      // ✅ Load auto-cache setting
      loadAutoCacheSetting(),
      // ✅ Claim all clients immediately
      clients.claim().then(() => {
        // console.log('[Service Worker] Claimed all clients - ready to intercept!');
      })
    ])
  );
});

// Fetch strategy cho audio files
self.addEventListener('fetch', (event) => {
  try {
    const url = new URL(event.request.url);
    
    // Chỉ intercept audio files NẾU auto-cache enabled
    if (url.pathname.includes('/media/music/')) {
      // ✅ Chỉ intercept khi auto-cache enabled để tránh error
      if (autoCacheEnabled) {
        // console.log('[Service Worker] 🎵 Intercepting audio request:', url.pathname);
        event.respondWith(handleAudioRequest(event.request));
      }
      // Nếu auto-cache disabled, để browser fetch trực tiếp (default behavior)
    }
  } catch (error) {
    console.error('🚨 Service Worker URL Error:', error.message, 'URL:', event.request.url);
    // Ignore invalid URLs and let browser handle them
  }
});

/**
 * Handle audio request với cache-first strategy
 * ✅ Cache trong app để offline playback (nếu user bật auto-cache)
 * ❌ KHÔNG cho user download file ra ngoài
 * 🔧 FIX: Handle Range requests properly - serve Range responses from cached full file
 */
async function handleAudioRequest(request) {
  try {
    const requestUrl = request.url.split('?')[0]; // Remove query params for cache matching
    const rangeHeader = request.headers.get('range');
    
    // ✅ Validate request URL
    if (!requestUrl || !requestUrl.startsWith('http')) {
      console.error('[Service Worker] Invalid request URL:', requestUrl);
      throw new Error('Invalid request URL');
    }
    
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
      // ✅ Validate cached response: check if it's valid
      if (cachedResponse.ok && cachedResponse.status === 200) {
        // console.log('[Service Worker] ✅ Serving from cache:', requestUrl);
        
        // Nếu request có Range header, tạo Range response từ cached full file
        if (rangeHeader) {
          return createRangeResponse(cachedResponse, rangeHeader);
        }
        
        // Không có Range header, return full cached file
        return cachedResponse;
      } else {
        // ✅ Cache hit nhưng response invalid, delete và fetch from network
        // Invalid cached response, fetching from network
        await cache.delete(requestUrl);
        // Continue to network fetch below
      }
    }
    
    // 2. Không có trong cache, fetch từ network
    // console.log('[Service Worker] Fetching from network:', requestUrl);
    
    // Luôn fetch FULL file để cache (bỏ range header)
    let fullRequest;
    try {
      fullRequest = new Request(requestUrl, {
        method: 'GET',
        headers: new Headers()
      });
    } catch (error) {
      console.error('[Service Worker] Invalid request URL for fetch:', requestUrl, error.message);
      throw new Error('Invalid request URL for fetch');
    }
    
    // ✅ CRITICAL FIX: Add timeout for production network issues
    // Reduce timeout để tránh conflict với player timeout (25s)
    const fetchTimeout = new Promise((_, reject) => {
      setTimeout(() => reject(new Error('Fetch timeout')), 20000); // 20s timeout
    });
    
    const fullResponse = await Promise.race([
      fetch(fullRequest),
      fetchTimeout
    ]).catch(error => {
      console.error('[Service Worker] Network fetch failed:', error.message);
      throw error;
    });
    
    if (fullResponse.ok) {
      // ✅ Cache full file CHỈ KHI auto-cache enabled VÀ là playback request
      if (autoCacheEnabled) {
        // ✅ CHỈ cache nếu có Range header (playback) hoặc referrer là from music player page
        // Preload requests: NO range header, NO specific referrer
        // Playback requests: HAS range header OR from music player
        const hasRangeHeader = rangeHeader !== null;
        const fromMusicPlayer = request.referrer && request.referrer.includes('/music/');
        
        // Cache nếu:
        // 1. Có Range header (đang seek/play) HOẶC
        // 2. Referrer từ music player page (user đang nghe thật)
        // 3. User đã tương tác với music player
        if ((hasRangeHeader || fromMusicPlayer) && userHasInteracted) {
          await cache.put(requestUrl, fullResponse.clone());
          // console.log('[Service Worker] ✅ Cached full file:', requestUrl);
          
          // ✅ Chỉ notify main thread KHI cache thành công
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
        }
        // ✅ Loại bỏ log "Skipping cache" để giảm spam
      }
      // ✅ Loại bỏ log "Auto-cache disabled" để giảm spam
      
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
    
    // Fallback: Trả về cached version nếu có và valid
    const requestUrl = request.url.split('?')[0];
    const cache = await caches.open(CACHE_VERSION);
    const cachedResponse = await cache.match(requestUrl);
    
    if (cachedResponse && cachedResponse.ok && cachedResponse.status === 200) {
      // Serving from cache (fallback mode)
      const rangeHeader = request.headers.get('range');
      
      if (rangeHeader) {
        return createRangeResponse(cachedResponse, rangeHeader);
      }
      
      return cachedResponse;
    }
    
    // ✅ Try fetch from network one more time if available
    if (navigator.onLine) {
      // Retrying network fetch after error
      try {
        // ✅ Validate requestUrl before creating Request
        if (!requestUrl || !requestUrl.startsWith('http')) {
          console.error('[Service Worker] Invalid requestUrl for retry:', requestUrl);
          throw new Error('Invalid requestUrl for retry');
        }
        
        const fullRequest = new Request(requestUrl, {
          method: 'GET',
          headers: new Headers()
        });
        
        // ✅ CRITICAL FIX: Add timeout cho retry để tránh hang indefinitely
        const retryTimeout = new Promise((_, reject) => {
          setTimeout(() => reject(new Error('Retry timeout')), 15000); // 15s timeout cho retry
        });
        
        const retryResponse = await Promise.race([
          fetch(fullRequest),
          retryTimeout
        ]);
        
        if (retryResponse.ok) {
          // Retry successful from network
          return retryResponse;
        }
      } catch (retryError) {
        console.error('🚨 Retry failed:', retryError.message);
      }
    }
    
    // Trả về error response
    return new Response('Service unavailable', {
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
  
  if (event.data.action === 'deleteCache') {
    console.log('[Service Worker] 🗑️ Deleting cache:', event.data.url);
    
    try {
      const cache = await caches.open(CACHE_VERSION);
      
      // ✅ Bước 1: Try direct match first
      const deleted = await cache.delete(event.data.url);
      console.log('[Service Worker] ✅ Cache deleted (direct match):', deleted);
      
      // ✅ Bước 2: If direct match failed, try pattern matching
      if (!deleted) {
        const requests = await cache.keys();
        console.log('[Service Worker] 📋 All cache keys:', requests.map(r => r.url));
        
        for (const request of requests) {
          try {
            // ✅ Validate request.url before using it
            if (!request.url || typeof request.url !== 'string') {
              console.warn('[Service Worker] Invalid request.url:', request.url);
              continue;
            }
            
            // ✅ Multiple pattern matching strategies
            const urlToDelete = event.data.url;
            const requestUrl = request.url;
            
            // Strategy 1: Exact match
            if (requestUrl === urlToDelete) {
              await cache.delete(request);
              console.log('[Service Worker] ✅ Cache deleted (exact match):', requestUrl);
              break;
            }
            
            // Strategy 2: Contains match
            if (requestUrl.includes(urlToDelete)) {
              await cache.delete(request);
              console.log('[Service Worker] ✅ Cache deleted (contains match):', requestUrl);
              break;
            }
            
            // Strategy 3: Filename match (extract filename from URL)
            const urlFilename = urlToDelete.split('/').pop();
            const requestFilename = requestUrl.split('/').pop();
            if (urlFilename && requestFilename && urlFilename === requestFilename) {
              await cache.delete(request);
              console.log('[Service Worker] ✅ Cache deleted (filename match):', requestUrl);
              break;
            }
            
            // Strategy 4: Decoded URL match
            try {
              const decodedUrl = decodeURIComponent(urlToDelete);
              if (requestUrl.includes(decodedUrl)) {
                await cache.delete(request);
                console.log('[Service Worker] ✅ Cache deleted (decoded URL match):', requestUrl);
                break;
              }
            } catch (decodeError) {
              // Ignore decode errors
            }
            
          } catch (error) {
            console.error('[Service Worker] ❌ Pattern match error:', error.message, 'URL:', request.url);
          }
        }
      }
      
      // ✅ Bước 3: Verify deletion
      const verifyDeleted = await cache.match(event.data.url);
      if (!verifyDeleted) {
        console.log('[Service Worker] ✅ Verification: Cache successfully deleted');
      } else {
        console.warn('[Service Worker] ⚠️ Verification: Cache still exists after deletion');
      }
      
    } catch (error) {
      console.error('[Service Worker] ❌ Cache deletion error:', error.message, error.stack);
    }
    // Note: postMessage without ports - main thread doesn't wait for response
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
    // Preload track vào cache (LUÔN cache khi manual preload)
    const url = event.data.url;
    try {
      await fetch(url);
      event.ports[0].postMessage({ success: true });
    } catch (error) {
      event.ports[0].postMessage({ success: false, error: error.message });
    }
  }
  
  // ✅ Update auto-cache setting
  if (event.data.action === 'setAutoCacheEnabled') {
    autoCacheEnabled = event.data.enabled;
    console.log(`[Service Worker] Auto-cache ${autoCacheEnabled ? 'enabled' : 'disabled'}`);
    // ✅ Save to storage để persist across SW reloads
    saveAutoCacheSetting(autoCacheEnabled);
    if (event.ports && event.ports[0]) {
      event.ports[0].postMessage({ success: true });
    }
  }
  
  // ✅ Track user interaction với music player
  if (event.data.action === 'userInteracted') {
    userHasInteracted = true;
    // console.log('[Service Worker] User interaction detected - caching enabled');
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
    try {
      const url = request.url;
      
      // ✅ Validate URL
      if (!url || !url.startsWith('http')) {
        console.warn('[Service Worker] Skipping invalid URL in size calculation:', url);
        continue;
      }
      
      const response = await cache.match(request);
      if (response) {
        const blob = await response.blob();
        totalSize += blob.size;
      }
    } catch (error) {
      console.error('[Service Worker] Error processing request in size calculation:', error.message, 'URL:', request.url);
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
      try {
        const url = request.url;
        
        // ✅ Validate URL
        if (!url || !url.startsWith('http')) {
          console.warn('[Service Worker] Skipping invalid URL in cleanup:', url);
          continue;
        }
      
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
    } catch (error) {
      console.error('[Service Worker] Error processing request in cleanup:', error.message, 'URL:', request.url);
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
    try {
      const url = request.url;
      
      // ✅ Validate URL
      if (!url || !url.startsWith('http')) {
        console.warn('[Service Worker] Skipping invalid URL:', url);
        continue;
      }
      
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
          let filename;
          try {
            filename = decodeURIComponent(urlParts[urlParts.length - 1]);
          } catch (e) {
            // Fallback to raw filename if decode fails
            filename = urlParts[urlParts.length - 1];
          }
          
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
    } catch (error) {
      console.error('[Service Worker] Error processing cached track:', error.message, 'URL:', request.url);
    }
  }
  
  // Sort by filename
  tracks.sort((a, b) => a.filename.localeCompare(b.filename));
  
  return tracks;
}

