# Cache Delete Sync Fix - Music Player

## Problem
Khi xóa cache offline, player vẫn hiển thị "✅ Track already cached" nhưng file đã bị xóa từ Service Worker cache. Điều này gây ra:
- Audio error khi load track (file không tồn tại)
- UI vẫn hiển thị cached indicator (misleading)
- localStorage và Service Worker cache không đồng bộ

## Root Cause
1. `localStorage` (`dbp_cached_tracks`) chứa track IDs
2. Service Worker cache chứa actual files
3. Khi xóa cache, chỉ xóa files, không update localStorage
4. Player load localStorage và nghĩ tracks vẫn cached

## Solution Implemented

### 1. Verify Before Showing Cached Indicator
**File:** `music_player.js` (Lines 3687-3708)

```javascript
// ✅ CRITICAL FIX: Verify ALL tracks before adding to cachedTracks
const verifiedCached = new Set();

for (const track of this.currentPlaylist.tracks) {
    // ✅ Only add if ACTUALLY cached in Service Worker
    const isCached = await this.offlineManager.isTrackCached(track.file_url);
    if (isCached) {
        verifiedCached.add(track.id);
    }
}

// ✅ CRITICAL: Only keep tracks that are actually cached
this.cachedTracks = verifiedCached;

// ✅ Update localStorage to match actual cache
this.saveCachedTracksToStorage();
```

### 2. Error Handling in `preloadTrackForOffline()`
**File:** `music_player.js` (Lines 3853-3857)

```javascript
} catch (error) {
    console.error('Error checking cache status:', error);
    // ✅ FIX: Remove from cachedTracks if check fails (might be deleted)
    this.cachedTracks.delete(track.id);
}
```

### 3. Async Handler for `preloadTrackForOffline()`
**File:** `music_player.js` (Lines 1648-1651)

```javascript
// ✅ Preload track for offline (Service Worker will auto-cache)
this.preloadTrackForOffline(track).catch(err => {
    console.error('Error preloading track:', err);
});
```

## Behavior

### Before:
```
1. User clears cache
2. Service Worker deletes files
3. localStorage still has track IDs
4. Player loads localStorage
5. Shows "✅ Track already cached"
6. Audio error (file not found)
```

### After:
```
1. User clears cache
2. Service Worker deletes files
3. Player checks ACTUAL cache status
4. Removes from localStorage if not cached
5. Shows correct status
6. No audio error
```

## Key Changes

### `updateCachedTracksStatus()`:
- ✅ Only checks Service Worker cache
- ✅ Ignores localStorage (no longer trusted)
- ✅ Updates localStorage to match reality

### `preloadTrackForOffline()`:
- ✅ Async/await properly handled
- ✅ Error handling removes track from cache if check fails
- ✅ Always checks actual cache status

## Version
- **music_player.js:** v1.2.19
- **service-worker.js:** v14-smart-cache-only

## Testing
✅ Clear cache → Verify tracks removed from localStorage
✅ Load page → Verify no "already cached" for deleted tracks
✅ Play track → Verify no audio error
✅ Cache new track → Verify added to localStorage

## Related Files
- `backend/music_player/static/music_player/js/music_player.js`
- `backend/static/js/offline-manager.js`
- `backend/service-worker.js`
