# Production Timeout Fix - Music Player

## Problem
Trên production (dbpsports.com), tracks bị timeout và audio error:
- Track load timeout sau 15s
- Multiple consecutive errors
- Service Worker fetch không thành công
- Network chậm hơn production

## Root Cause
1. Timeout quá ngắn (15s) cho production
2. Network latency cao trên production
3. Không có timeout cho Service Worker fetch
4. Error counter không được increment trong timeout handler

## Solution Implemented

### 1. Increase Player Timeout
**File:** `music_player.js` (Lines 1653-1682)

```javascript
// ✅ Increase to 30 seconds for production
const loadTimeout = setTimeout(() => {
    if (this.isLoadingTrack) {
        this.isLoadingTrack = false;
        console.error('🚨 Track load timeout:', track.title);
        console.error('🚨 URL:', fileUrl);
        
        // ✅ Increment error counter
        this.consecutiveErrors++;
        if (this.consecutiveErrors >= this.maxConsecutiveErrors) {
            console.error('❌ Too many consecutive errors, stopping playback');
            this.showMessage('Không thể tải bài hát. Có thể playlist có vấn đề.', 'error');
            return;
        }
        
        // Auto-skip to next track
        setTimeout(() => {
            this.nextTrack();
        }, 2000);
    }
}, 30000); // ✅ Increased from 15s to 30s
```

### 2. Add URL Encoding
**File:** `music_player.js` (Lines 1645-1651)

```javascript
// ✅ CRITICAL FIX: Ensure URL is properly encoded for production
const encodedUrl = encodeURI(fileUrl);
console.log('🎵 Loading track:', track.title);
console.log('📂 URL:', encodedUrl);

this.audio.src = encodedUrl;
this.audio.load();
```

### 3. Service Worker Network Timeout
**File:** `service-worker.js` (Lines 167-178)

```javascript
// ✅ CRITICAL FIX: Add timeout for production network issues
const fetchTimeout = new Promise((_, reject) => {
  setTimeout(() => reject(new Error('Fetch timeout')), 30000); // 30s timeout
});

const fullResponse = await Promise.race([
  fetch(fullRequest),
  fetchTimeout
]).catch(error => {
  console.error('[Service Worker] Network fetch failed:', error.message);
  throw error;
});
```

## Behavior

### Before:
```
1. Track starts loading
2. 15s timeout → Error
3. Error counter not incremented
4. Skip to next track
5. Repeat until max errors
6. Stop playback
```

### After:
```
1. Track starts loading
2. 30s timeout → Error with counter increment
3. Error counter incremented
4. Skip to next track if < max errors
5. Stop playback if max errors reached
6. Better error logging with URL
```

## Key Changes

### Timeout Duration:
- **Before:** 15 seconds
- **After:** 30 seconds

### Error Handling:
- ✅ Increment error counter in timeout handler
- ✅ Stop playback after max errors
- ✅ Better logging with URL

### Service Worker:
- ✅ Network fetch timeout (30s)
- ✅ Proper error handling and logging

## Version
- **music_player.js:** v1.2.21
- **service-worker.js:** v15-network-timeout-fix

## Testing
✅ Test on production with slow network
✅ Verify timeout is now 30s
✅ Verify error counter increments
✅ Verify stops after 3 errors
✅ Check console logs for URL

## Related Files
- `backend/music_player/static/music_player/js/music_player.js`
- `backend/service-worker.js`
- `backend/templates/base.html`
