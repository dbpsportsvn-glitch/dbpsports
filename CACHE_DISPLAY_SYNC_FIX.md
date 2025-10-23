# Cache Display Sync Fix - Settings Modal

## Problem
Khi cache nhạc mới, danh sách trong settings modal không cập nhật ngay:
- Track đã cache nhưng không hiển thị trong settings
- Phải mở/đóng settings hoặc click "Refresh" mới thấy
- Không đồng bộ giữa player UI và settings modal

## Root Cause
1. Service Worker dispatch `trackCached` event khi cache xong
2. Music player nhận event và trigger `updateCacheStatus`
3. Settings modal chỉ refresh KHI đang mở
4. Nếu modal đóng, data không được update → stale data

## Solution Implemented

### 1. Always Trigger Cache Update Event
**File:** `music_player.js` (Lines 3600-3602)

```javascript
// ✅ CRITICAL FIX: Always trigger cache status update (not just when modal open)
// This ensures settings modal shows correct data when opened later
window.dispatchEvent(new CustomEvent('updateCacheStatus'));
```

**Before:**
```javascript
// Only update if modal is open
if (settingsModal && !settingsModal.classList.contains('hidden')) {
    window.dispatchEvent(new CustomEvent('updateCacheStatus'));
}
```

### 2. Background Refresh for Closed Modal
**File:** `user_music.js` (Lines 183-195)

```javascript
window.addEventListener('updateCacheStatus', async () => {
    // ✅ CRITICAL FIX: Always refresh cache status, even if modal is closed
    if (this.settingsModal && !this.settingsModal.classList.contains('hidden')) {
        await this.refreshCacheStatus();
    } else {
        // ✅ Silent refresh: Update offline manager cache data in background
        const offlineManager = this.musicPlayer?.offlineManager;
        if (offlineManager) {
            await offlineManager.updateCacheStatus();
        }
    }
});
```

**Before:**
```javascript
window.addEventListener('updateCacheStatus', () => {
    if (this.settingsModal && !this.settingsModal.classList.contains('hidden')) {
        this.refreshCacheStatus();
    }
});
```

## Behavior

### Before:
```
1. Track cached by Service Worker
2. Dispatch 'trackCached' event
3. Check if settings modal is open
4. If modal closed → NO UPDATE
5. User opens settings → Shows OLD data
6. User clicks "Refresh" → Shows NEW data
```

### After:
```
1. Track cached by Service Worker
2. Dispatch 'trackCached' event
3. ALWAYS trigger 'updateCacheStatus' event
4. If modal open → Refresh UI
5. If modal closed → Update cache data in background
6. User opens settings → Shows FRESH data immediately
```

## Key Changes

### `music_player.js`:
- ✅ Always dispatch `updateCacheStatus` event when track cached
- ✅ No longer checks if modal is open
- ✅ Ensures data is fresh when user opens settings

### `user_music.js`:
- ✅ Refresh UI if modal is open
- ✅ Silent background update if modal is closed
- ✅ Always keep cache data fresh

## Version
- **music_player.js:** v1.2.20
- **user_music.js:** (auto-updated)

## Testing
✅ Cache new track → Verify event dispatched
✅ Open settings → Verify track appears immediately
✅ Close settings, cache track, reopen → Verify track appears
✅ No need to click "Refresh" anymore

## Related Files
- `backend/music_player/static/music_player/js/music_player.js`
- `backend/music_player/static/music_player/js/user_music.js`
- `backend/static/js/offline-manager.js`
- `backend/service-worker.js`
