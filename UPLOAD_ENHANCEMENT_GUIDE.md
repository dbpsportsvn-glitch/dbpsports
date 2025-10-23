# Upload Enhancement Guide

## Tính Năng Mới

### 1. **Chọn Playlist Trước Khi Upload**
**Mô tả:** User có thể chọn playlist từ dropdown trước khi upload, files sẽ tự động được thêm vào playlist đó sau khi upload thành công.

**UI:**
```html
<select id="upload-playlist-select">
    <option value="">-- Không thêm vào playlist --</option>
    <!-- Playlists sẽ được load vào đây -->
</select>
```

**Flow:**
1. User chọn playlist từ dropdown
2. User chọn files và upload
3. Files được upload thành công
4. Files tự động được add vào playlist đã chọn (silent mode, không show notification)

### 2. **Add Files Vào Playlist**
**Mô tả:** Button "Add files" (bi-plus-circle) trên mỗi playlist card cho phép chọn nhiều file và upload/add vào playlist đó ngay lập tức.

**Flow:**
1. User click button "Add files" trên playlist card
2. File picker mở ra (multiple selection)
3. User chọn nhiều files
4. Files được upload và tự động add vào playlist đó

## Code Changes

### Frontend Changes

#### `backend/music_player/templates/music_player/settings_modal.html`
- ✅ Thêm dropdown playlist selector vào upload section
- ✅ Update hint text: "Tối đa theo quota còn lại"

#### `backend/music_player/static/music_player/css/music_player.css`
- ✅ **Upload Playlist Selector Styling:**
  - `.upload-playlist-selector` - Container với spacing và layout
  - `.upload-playlist-selector label` - Label styling với icon
  - `.upload-playlist-selector .form-select` - Dropdown custom styling
  - Hover effect với purple border
  - Focus effect với box-shadow
  - Option styling với purple background
  
- ✅ **Playlist Add Button Styling:**
  - `.playlist-add-btn` - Button xanh lá (green)
  - Hover effect với scale transform
  - Size 36x36px giống các button khác

#### `backend/music_player/static/music_player/js/user_music.js`

**New Functions:**
```javascript
// Populate upload playlist dropdown
populateUploadPlaylistDropdown(playlists) {
    if (!this.uploadPlaylistSelect) return;
    this.uploadPlaylistSelect.innerHTML = '<option value="">-- Không thêm vào playlist --</option>';
    playlists.forEach(playlist => {
        const option = document.createElement('option');
        option.value = playlist.id;
        option.textContent = playlist.name;
        this.uploadPlaylistSelect.appendChild(option);
    });
}

// Add files to playlist from file picker
addFilesToPlaylist(playlistId) {
    if (!this.fileInput) return;
    this.tempPlaylistId = playlistId;
    this.fileInput.click();
    this.fileInput.onchange = async (e) => {
        const files = e.target.files;
        if (files.length === 0) return;
        await this.handleFileUpload(files, playlistId);
        this.fileInput.value = '';
        this.tempPlaylistId = null;
    };
}
```

**Updated Functions:**
```javascript
// Update handleFileUpload to accept playlistId
async handleFileUpload(files, playlistId = null) {
    // ...existing code...
    for (let file of files) {
        await this.uploadFile(file, playlistId);
    }
}

// Update uploadFile to accept playlistId
async uploadFile(file, playlistId = null) {
    // ...existing code...
    if (data.success) {
        // Auto-add to playlist (from dropdown or parameter)
        const selectedPlaylistId = playlistId || (this.uploadPlaylistSelect ? this.uploadPlaylistSelect.value : null);
        if (selectedPlaylistId && data.track) {
            await this.addTrackToPlaylist(selectedPlaylistId, data.track.id, true); // silent = true
        }
    }
}

// Update addTrackToPlaylist to support silent mode
async addTrackToPlaylist(playlistId, trackId, silent = false) {
    // ...existing code...
    if (data.success) {
        if (!silent) {
            this.showNotification(data.message, 'success');
        }
    }
}
```

**UI Updates:**
```javascript
// Add "Add files" button to playlist card
renderUserPlaylists(playlists) {
    // ...existing code...
    `
    <div class="playlist-actions">
        <button class="playlist-add-btn" title="Thêm nhạc vào playlist" 
                onclick="event.stopPropagation(); userMusicManager.addFilesToPlaylist(${playlist.id})">
            <i class="bi bi-plus-circle"></i>
        </button>
        <!-- other buttons -->
    </div>
    `
}
```

## Benefits

✅ **Better UX:** User có thể upload và organize nhạc nhanh hơn  
✅ **Multi-file Upload:** Upload nhiều file vào playlist một lúc  
✅ **Silent Mode:** Không spam notifications khi auto-add vào playlist  
✅ **Flexible:** Có thể upload vào playlist ngay hoặc upload rồi add sau  

## Usage

### Cách 1: Upload và tự động add vào playlist
1. Mở Settings > My Music
2. Chọn playlist từ dropdown "Chọn Playlist"
3. Click "Upload Nhạc"
4. Chọn files
5. Files sẽ tự động được thêm vào playlist đã chọn

### Cách 2: Add files vào playlist từ playlist card
1. Mở Settings > My Music
2. Scroll xuống phần "My Playlists"
3. Click button "Add files" (bi-plus-circle) trên playlist muốn thêm
4. Chọn nhiều files trong file picker
5. Files sẽ được upload và add vào playlist đó

## Technical Notes

- `silent = true` parameter để tránh spam notifications khi auto-add
- Playlist dropdown được populate khi load user playlists
- File input được reuse cho cả upload và add-to-playlist
- `playlistId` parameter được truyền qua uploadFile → handleFileUpload để support cả 2 flows

