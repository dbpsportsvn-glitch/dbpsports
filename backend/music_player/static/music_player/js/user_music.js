/**
 * User Music Management JavaScript
 * Handles Settings Modal, Upload, and User Tracks
 */

class UserMusicManager {
    constructor(musicPlayer) {
        this.musicPlayer = musicPlayer;
        this.settingsModal = document.getElementById('settings-modal');
        this.settingsBtn = document.getElementById('settings-btn');
        this.settingsCloseBtn = document.getElementById('settings-close-btn');
        this.uploadBtn = document.getElementById('upload-btn');
        this.fileInput = document.getElementById('file-input');
        this.uploadProgressOverlay = document.getElementById('upload-progress-overlay');
        this.uploadProgressList = document.getElementById('upload-progress-list');
        
        this.userSettings = null;
        this.userTracks = [];
        this.userPlaylists = [];
        
        this.initializeElements();
        this.bindEvents();
        // KHÔNG gọi loadUserSettings() ở đây vì user có thể chưa đăng nhập
        // Settings sẽ được load khi user click vào Settings button
    }
    
    initializeElements() {
        // Tab switching
        this.settingsTabHeaders = document.querySelectorAll('.settings-tab-header');
        this.settingsTabContents = document.querySelectorAll('.settings-tab-content');
        
        // Settings inputs
        this.autoPlayCheckbox = document.getElementById('setting-autoplay');
        this.volumeSlider = document.getElementById('setting-volume');
        this.volumeValue = document.getElementById('volume-value');
        this.repeatSelect = document.getElementById('setting-repeat');
        this.shuffleCheckbox = document.getElementById('setting-shuffle');
        this.saveSettingsBtn = document.getElementById('save-settings-btn');
        
        // Quota elements
        this.quotaUsed = document.getElementById('quota-used');
        this.quotaTotal = document.getElementById('quota-total');
        this.quotaRemaining = document.getElementById('quota-remaining');
        this.quotaFill = document.getElementById('quota-fill');
        this.tracksCount = document.getElementById('tracks-count');
        
        // Tracks list
        this.myTracksList = document.getElementById('my-tracks-list');
        
        // Playlists
        this.myPlaylistsList = document.getElementById('my-playlists-list');
        this.createPlaylistBtn = document.getElementById('create-playlist-btn');
    }
    
    bindEvents() {
        // Open/Close Settings Modal
        if (this.settingsBtn) {
            this.settingsBtn.addEventListener('click', () => this.openSettings());
        }
        
        if (this.settingsCloseBtn) {
            this.settingsCloseBtn.addEventListener('click', () => this.closeSettings());
        }
        
        // Close modal when clicking overlay
        if (this.settingsModal) {
            const overlay = this.settingsModal.querySelector('.settings-modal-overlay');
            if (overlay) {
                overlay.addEventListener('click', (e) => {
                    e.stopPropagation();
                    this.closeSettings();
                });
            }
        }
        
        // Prevent settings modal from closing music player
        if (this.settingsModal) {
            this.settingsModal.addEventListener('click', (e) => {
                e.stopPropagation();
            });
        }
        
        // Tab switching
        this.settingsTabHeaders.forEach(header => {
            header.addEventListener('click', () => {
                const tabName = header.getAttribute('data-tab');
                this.switchTab(tabName);
            });
        });
        
        // Volume slider
        if (this.volumeSlider) {
            this.volumeSlider.addEventListener('input', (e) => {
                this.volumeValue.textContent = e.target.value + '%';
            });
        }
        
        // Save Settings
        if (this.saveSettingsBtn) {
            this.saveSettingsBtn.addEventListener('click', () => this.saveSettings());
        }
        
        // Upload button
        if (this.uploadBtn) {
            this.uploadBtn.addEventListener('click', () => {
                this.fileInput.click();
            });
        }
        
        // File input change
        if (this.fileInput) {
            this.fileInput.addEventListener('change', (e) => {
                if (e.target.files.length > 0) {
                    this.handleFileUpload(e.target.files);
                }
            });
        }
        
        // Create Playlist
        if (this.createPlaylistBtn) {
            this.createPlaylistBtn.addEventListener('click', () => this.createPlaylist());
        }
    }
    
    async openSettings() {
        // Kiểm tra authentication trước khi mở modal
        try {
            const response = await fetch('/music/user/settings/');
            
            // Check nếu response là HTML (user chưa đăng nhập, Django redirect)
            const contentType = response.headers.get('content-type');
            if (!contentType || !contentType.includes('application/json')) {
                this.showNotification('⚠️ Vui lòng đăng nhập để sử dụng tính năng cá nhân!', 'info');
                setTimeout(() => {
                    window.location.href = '/accounts/login/?next=' + window.location.pathname;
                }, 1500);
                return;
            }
            
            if (!response.ok) {
                if (response.status === 302 || response.status === 401 || response.status === 403) {
                    this.showNotification('⚠️ Vui lòng đăng nhập để sử dụng tính năng cá nhân!', 'info');
                    setTimeout(() => {
                        window.location.href = '/accounts/login/?next=' + window.location.pathname;
                    }, 1500);
                    return;
                }
            }
            
            // Try to parse JSON
            const data = await response.json();
            
            if (!data.success) {
                this.showNotification('⚠️ Vui lòng đăng nhập để sử dụng tính năng cá nhân!', 'info');
                setTimeout(() => {
                    window.location.href = '/accounts/login/?next=' + window.location.pathname;
                }, 1500);
                return;
            }
            
            // Nếu authenticated, mở modal và load data
            this.settingsModal.classList.remove('hidden');
            this.loadUserSettings();
            this.loadUserTracks();
            this.loadUserPlaylists();
            
        } catch (error) {
            console.error('Error checking authentication:', error);
            this.showNotification('⚠️ Vui lòng đăng nhập để sử dụng tính năng cá nhân!', 'info');
            setTimeout(() => {
                window.location.href = '/accounts/login/?next=' + window.location.pathname;
            }, 1500);
        }
    }
    
    closeSettings() {
        // Chỉ đóng settings modal, KHÔNG đóng music player popup
        if (this.settingsModal) {
            this.settingsModal.classList.add('hidden');
        }
    }
    
    switchTab(tabName) {
        // Remove active class from all headers and contents
        this.settingsTabHeaders.forEach(h => h.classList.remove('active'));
        this.settingsTabContents.forEach(c => c.classList.remove('active'));
        
        // Add active class to selected
        const selectedHeader = document.querySelector(`.settings-tab-header[data-tab="${tabName}"]`);
        const selectedContent = document.getElementById(`settings-tab-${tabName}`);
        
        if (selectedHeader) selectedHeader.classList.add('active');
        if (selectedContent) selectedContent.classList.add('active');
        
        // Load data for specific tabs
        if (tabName === 'mymusic') {
            this.loadUserTracks();
        } else if (tabName === 'myplaylists') {
            this.loadUserPlaylists();
        }
    }
    
    async loadUserSettings(silent = false) {
        try {
            const response = await fetch('/music/user/settings/');
            
            if (!response.ok) {
                if (response.status === 302 || response.status === 401 || response.status === 403) {
                    // Chỉ show notification nếu không phải silent mode
                    if (!silent) {
                        this.showNotification('Vui lòng đăng nhập để sử dụng tính năng này!', 'info');
                    }
                    return;
                }
                throw new Error(`HTTP ${response.status}`);
            }
            
            const data = await response.json();
            
            if (data.success) {
                this.userSettings = data.settings;
                this.populateSettings(data.settings);
            }
        } catch (error) {
            // Chỉ log error, không show notification trong silent mode
            if (!silent) {
                console.error('Error loading user settings:', error);
                if (error.message.includes('Unexpected token')) {
                    this.showNotification('Vui lòng đăng nhập để sử dụng tính năng này!', 'info');
                } else {
                    this.showNotification('Lỗi khi tải cài đặt!', 'error');
                }
            }
        }
    }
    
    populateSettings(settings) {
        // Populate form with current settings
        if (this.autoPlayCheckbox) {
            this.autoPlayCheckbox.checked = settings.auto_play;
        }
        
        if (this.volumeSlider) {
            const volumePercent = Math.round(settings.volume * 100);
            this.volumeSlider.value = volumePercent;
            this.volumeValue.textContent = volumePercent + '%';
        }
        
        if (this.repeatSelect) {
            this.repeatSelect.value = settings.repeat_mode;
        }
        
        if (this.shuffleCheckbox) {
            this.shuffleCheckbox.checked = settings.shuffle;
        }
        
        // Update quota display
        this.updateQuotaDisplay(settings.upload_usage);
    }
    
    updateQuotaDisplay(usage) {
        if (!usage) return;
        
        // Update MB display
        this.quotaUsed.textContent = usage.used;
        this.quotaTotal.textContent = usage.total;
        this.quotaRemaining.textContent = usage.remaining;
        
        // Update tracks count
        if (this.tracksCount) {
            this.tracksCount.textContent = usage.tracks_count || 0;
        }
        
        const percentage = (usage.used / usage.total) * 100;
        this.quotaFill.style.width = percentage + '%';
        
        // Change color based on usage
        if (percentage >= 90) {
            this.quotaFill.setAttribute('data-level', 'full');
        } else if (percentage >= 70) {
            this.quotaFill.setAttribute('data-level', 'high');
        } else {
            this.quotaFill.removeAttribute('data-level');
        }
        
        // Disable upload if quota full
        if (usage.remaining <= 0) {
            this.uploadBtn.disabled = true;
            this.uploadBtn.innerHTML = '<i class="bi bi-x-circle"></i> Đã hết dung lượng';
        } else {
            this.uploadBtn.disabled = false;
            this.uploadBtn.innerHTML = '<i class="bi bi-cloud-arrow-up"></i> Upload Nhạc';
        }
    }
    
    async saveSettings() {
        const settings = {
            auto_play: this.autoPlayCheckbox.checked,
            volume: parseFloat(this.volumeSlider.value) / 100,
            repeat_mode: this.repeatSelect.value,
            shuffle: this.shuffleCheckbox.checked
        };
        
        try {
            const response = await fetch('/music/user/settings/update/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: JSON.stringify(settings)
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.showNotification('Đã lưu cài đặt thành công!', 'success');
                
                // Apply settings to music player
                if (this.musicPlayer) {
                    this.musicPlayer.volume = settings.volume;
                    this.musicPlayer.audio.volume = settings.volume;
                    this.musicPlayer.repeatMode = settings.repeat_mode;
                    this.musicPlayer.isShuffled = settings.shuffle;
                    
                    // Update UI buttons
                    if (this.musicPlayer.updateRepeatButton) {
                        this.musicPlayer.updateRepeatButton();
                    }
                    if (this.musicPlayer.shuffleBtn) {
                        this.musicPlayer.shuffleBtn.classList.toggle('active', settings.shuffle);
                    }
                    
                    // Update volume UI
                    if (this.musicPlayer.volumeFill) {
                        this.musicPlayer.volumeFill.style.width = (settings.volume * 100) + '%';
                    }
                    if (this.musicPlayer.volumeHandle) {
                        this.musicPlayer.volumeHandle.style.left = (settings.volume * 100) + '%';
                    }
                }
                
                // Đóng modal sau khi lưu thành công
                this.closeSettings();
            } else {
                this.showNotification('Lỗi khi lưu cài đặt!', 'error');
            }
        } catch (error) {
            console.error('Error saving settings:', error);
            this.showNotification('Lỗi khi lưu cài đặt!', 'error');
        }
    }
    
    async loadUserTracks() {
        try {
            // Add cache-busting parameter
            const response = await fetch(`/music/user/tracks/?t=${Date.now()}`);
            
            if (!response.ok) {
                if (response.status === 302 || response.status === 401) {
                    this.showNotification('Vui lòng đăng nhập để sử dụng tính năng này!', 'info');
                    return;
                }
                throw new Error(`HTTP ${response.status}`);
            }
            
            const data = await response.json();
            
            if (data.success) {
                this.userTracks = data.tracks;
                this.renderUserTracks(data.tracks);
                this.updateQuotaDisplay(data.usage);
            }
        } catch (error) {
            console.error('Error loading user tracks:', error);
            if (error.message.includes('Unexpected token')) {
                this.showNotification('Vui lòng đăng nhập để sử dụng tính năng này!', 'info');
            } else {
                this.showNotification('Lỗi khi tải danh sách nhạc!', 'error');
            }
        }
    }
    
    renderUserTracks(tracks) {
        if (!this.myTracksList) return;
        
        if (tracks.length === 0) {
            this.myTracksList.innerHTML = `
                <div class="empty-state">
                    <i class="bi bi-music-note"></i>
                    <p>Chưa có bài hát nào. Hãy upload nhạc của bạn!</p>
                </div>
            `;
            return;
        }
        
        this.myTracksList.innerHTML = tracks.map(track => `
            <div class="track-card" data-track-id="${track.id}">
                <div class="track-card-icon">
                    <i class="bi bi-music-note-beamed"></i>
                </div>
                <div class="track-card-info">
                    <h6 class="track-card-title">${track.title}</h6>
                    <p class="track-card-details">
                        ${track.artist || 'Unknown Artist'} • ${track.duration_formatted} • ${track.file_size_formatted}
                    </p>
                </div>
                <div class="track-card-actions">
                    <button class="track-action-btn play" title="Phát" onclick="userMusicManager.playUserTrack(${track.id})">
                        <i class="bi bi-play-fill"></i>
                    </button>
                    <button class="track-action-btn add-playlist" title="Thêm vào Playlist" onclick="userMusicManager.showAddToPlaylistMenu(${track.id}, event)">
                        <i class="bi bi-plus-circle"></i>
                    </button>
                    <button class="track-action-btn delete" title="Xóa" onclick="userMusicManager.deleteUserTrack(${track.id})">
                        <i class="bi bi-trash"></i>
                    </button>
                </div>
            </div>
        `).join('');
    }
    
    async handleFileUpload(files) {
        if (files.length === 0) return;
        
        // Show upload progress overlay
        this.uploadProgressOverlay.classList.remove('hidden');
        this.uploadProgressList.innerHTML = '';
        
        for (let file of files) {
            await this.uploadFile(file);
        }
        
        // Reload tracks after upload
        await this.loadUserTracks();
        
        // Reload playlists để cập nhật số lượng bài hát
        await this.loadUserPlaylists();
        
        // LUÔN cập nhật user playlists trong main player (dù đang ẩn hay không)
        // Vì user có thể sẽ mở ra sau, và cần thấy data mới nhất
        if (this.musicPlayer && this.musicPlayer.loadUserPlaylistsInMainPlayer) {
            await this.musicPlayer.loadUserPlaylistsInMainPlayer();
        }
        
        // Hide overlay after 2 seconds
        setTimeout(() => {
            this.uploadProgressOverlay.classList.add('hidden');
            this.fileInput.value = ''; // Reset file input
        }, 2000);
    }
    
    async uploadFile(file) {
        const uploadItem = this.createUploadItem(file.name);
        this.uploadProgressList.appendChild(uploadItem);
        
        const formData = new FormData();
        formData.append('file', file);
        
        try {
            const response = await fetch('/music/user/tracks/upload/', {
                method: 'POST',
                headers: {
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: formData
            });
            
            if (!response.ok) {
                if (response.status === 302 || response.status === 401) {
                    this.updateUploadItem(uploadItem, 'error', 'Vui lòng đăng nhập để upload nhạc!');
                    return;
                }
                throw new Error(`HTTP ${response.status}`);
            }
            
            const data = await response.json();
            
            if (data.success) {
                this.updateUploadItem(uploadItem, 'success', 'Upload thành công!');
                this.updateQuotaDisplay(data.usage);
                // Note: loadUserTracks() sẽ được gọi trong handleFileUpload() sau khi upload xong tất cả
            } else {
                this.updateUploadItem(uploadItem, 'error', data.error || 'Upload thất bại!');
            }
        } catch (error) {
            console.error('Error uploading file:', error);
            if (error.message.includes('Unexpected token')) {
                this.updateUploadItem(uploadItem, 'error', 'Vui lòng đăng nhập để upload nhạc!');
            } else {
                this.updateUploadItem(uploadItem, 'error', 'Lỗi khi upload!');
            }
        }
    }
    
    createUploadItem(filename) {
        const item = document.createElement('div');
        item.className = 'upload-item';
        item.innerHTML = `
            <div class="upload-item-name">${filename}</div>
            <div class="upload-item-progress">
                <div class="upload-item-progress-fill" style="width: 0%"></div>
            </div>
            <div class="upload-item-status">Đang upload...</div>
        `;
        return item;
    }
    
    updateUploadItem(item, status, message) {
        item.classList.add(status);
        const progressFill = item.querySelector('.upload-item-progress-fill');
        const statusText = item.querySelector('.upload-item-status');
        
        progressFill.style.width = '100%';
        statusText.textContent = message;
    }
    
    async deleteUserTrack(trackId) {
        if (!confirm('Bạn có chắc muốn xóa bài hát này?')) {
            return;
        }
        
        try {
            const response = await fetch(`/music/user/tracks/${trackId}/delete/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': this.getCSRFToken()
                }
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.showNotification('Đã xóa bài hát thành công!', 'success');
                await this.loadUserTracks();
                
                // Reload playlists để cập nhật số lượng bài hát
                await this.loadUserPlaylists();
                
                // LUÔN cập nhật user playlists trong main player
                if (this.musicPlayer && this.musicPlayer.loadUserPlaylistsInMainPlayer) {
                    await this.musicPlayer.loadUserPlaylistsInMainPlayer();
                }
            } else {
                this.showNotification('Lỗi khi xóa bài hát!', 'error');
            }
        } catch (error) {
            console.error('Error deleting track:', error);
            this.showNotification('Lỗi khi xóa bài hát!', 'error');
        }
    }
    
    playUserTrack(trackId) {
        const track = this.userTracks.find(t => t.id === trackId);
        if (!track || !this.musicPlayer) return;
        
        // Convert user track to player format
        const playerTrack = {
            id: track.id,
            title: track.title,
            artist: track.artist || 'Unknown Artist',
            file_url: track.file_url,
            duration: track.duration
        };
        
        // Set current playlist với bài này
        this.musicPlayer.currentPlaylist = {
            id: 'user-track-' + track.id,
            name: 'Nhạc của tôi',
            tracks: [playerTrack]
        };
        this.musicPlayer.currentTrackIndex = 0;
        
        // ✅ Đảm bảo mini player được mở (remove hidden class)
        const popup = this.musicPlayer.popup;
        if (popup && popup.classList.contains('hidden')) {
            popup.classList.remove('hidden');
        }
        
        // ✅ Populate track list để hiển thị bài đang phát
        this.musicPlayer.populateTrackList();
        
        // ✅ Đánh dấu user đã tương tác (để autoplay được phép)
        this.musicPlayer.userInteracted = true;
        
        // ✅ Phát bài hát (truyền index 0, không phải object)
        this.musicPlayer.playTrack(0);
        
        // ✅ Đảm bảo phát luôn (nếu auto_play tắt)
        setTimeout(() => {
            if (!this.musicPlayer.isPlaying) {
                this.musicPlayer.audio.play().catch(e => {
                    console.log('User track play failed:', e);
                });
            }
        }, 100);
        
        // Đóng Settings modal
        this.closeSettings();
    }
    
    async loadUserPlaylists() {
        try {
            // Add cache-busting parameter
            const response = await fetch(`/music/user/playlists/?t=${Date.now()}`);
            
            if (!response.ok) {
                if (response.status === 302 || response.status === 401) {
                    this.showNotification('Vui lòng đăng nhập để sử dụng tính năng này!', 'info');
                    return;
                }
                throw new Error(`HTTP ${response.status}`);
            }
            
            const data = await response.json();
            
            if (data.success) {
                this.userPlaylists = data.playlists;
                this.renderUserPlaylists(data.playlists);
            }
        } catch (error) {
            console.error('Error loading user playlists:', error);
            if (error.message.includes('Unexpected token')) {
                this.showNotification('Vui lòng đăng nhập để sử dụng tính năng này!', 'info');
            } else {
                this.showNotification('Lỗi khi tải danh sách playlist!', 'error');
            }
        }
    }
    
    renderUserPlaylists(playlists) {
        if (!this.myPlaylistsList) return;
        
        if (playlists.length === 0) {
            this.myPlaylistsList.innerHTML = `
                <div class="empty-state">
                    <i class="bi bi-collection-play"></i>
                    <p>Chưa có playlist nào. Tạo playlist đầu tiên!</p>
                </div>
            `;
            return;
        }
        
        this.myPlaylistsList.innerHTML = playlists.map(playlist => `
            <div class="user-playlist-card">
                <div class="user-playlist-info" onclick="userMusicManager.openPlaylist(${playlist.id})">
                    <div class="user-playlist-icon">
                        <i class="bi bi-vinyl-fill"></i>
                    </div>
                    <div class="user-playlist-details">
                        <h6 class="user-playlist-name">${playlist.name}</h6>
                        <p class="user-playlist-count">${playlist.tracks_count} bài hát</p>
                    </div>
                </div>
                <button class="playlist-delete-btn" title="Xóa playlist" onclick="event.stopPropagation(); userMusicManager.deletePlaylist(${playlist.id})">
                    <i class="bi bi-trash"></i>
                </button>
            </div>
        `).join('');
    }
    
    async createPlaylist() {
        const name = prompt('Tên playlist:');
        if (!name || name.trim() === '') return;
        
        try {
            const response = await fetch('/music/user/playlists/create/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: JSON.stringify({ name: name.trim() })
            });
            
            if (!response.ok) {
                if (response.status === 302 || response.status === 401 || response.status === 403) {
                    this.showNotification('⚠️ Vui lòng đăng nhập để tạo playlist!', 'info');
                    setTimeout(() => {
                        window.location.href = '/accounts/login/?next=' + window.location.pathname;
                    }, 1500);
                    return;
                }
                throw new Error(`HTTP ${response.status}`);
            }
            
            const data = await response.json();
            
            if (data.success) {
                this.showNotification('Đã tạo playlist "' + data.playlist.name + '" thành công!', 'success');
                // Reload playlists to show new one
                await this.loadUserPlaylists();
            } else {
                this.showNotification(data.error || 'Lỗi khi tạo playlist!', 'error');
            }
        } catch (error) {
            console.error('Error creating playlist:', error);
            if (error.message.includes('Unexpected token')) {
                this.showNotification('⚠️ Vui lòng đăng nhập để tạo playlist!', 'info');
            } else {
                this.showNotification('Lỗi khi tạo playlist!', 'error');
            }
        }
    }
    
    async showAddToPlaylistMenu(trackId, event) {
        event.stopPropagation();
        
        console.log('Available playlists:', this.userPlaylists);
        
        if (this.userPlaylists.length === 0) {
            this.showNotification('Bạn chưa có playlist nào. Hãy tạo playlist trước!', 'info');
            return;
        }
        
        // Create simple menu
        const playlistNames = this.userPlaylists.map((p, i) => `${i+1}. ${p.name}`).join('\n');
        const choice = prompt(`Chọn playlist (nhập số):\n${playlistNames}`);
        
        if (!choice) return;
        
        const index = parseInt(choice) - 1;
        if (index >= 0 && index < this.userPlaylists.length) {
            const playlist = this.userPlaylists[index];
            console.log(`Selected playlist: ${playlist.name} (ID: ${playlist.id})`);
            await this.addTrackToPlaylist(playlist.id, trackId);
        } else {
            this.showNotification('Lựa chọn không hợp lệ!', 'error');
        }
    }
    
    async addTrackToPlaylist(playlistId, trackId) {
        try {
            console.log(`Adding track ${trackId} to playlist ${playlistId}`);
            
            const response = await fetch(`/music/user/playlists/${playlistId}/add-track/${trackId}/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': this.getCSRFToken()
                }
            });
            
            console.log('Response status:', response.status);
            
            if (!response.ok) {
                const errorData = await response.json();
                console.error('API Error:', errorData);
                this.showNotification(errorData.error || 'Lỗi khi thêm bài hát vào playlist!', 'error');
                return;
            }
            
            const data = await response.json();
            console.log('Response data:', data);
            
            if (data.success) {
                this.showNotification(data.message, 'success');
                
                // Reload playlists để cập nhật số lượng bài hát
                await this.loadUserPlaylists();
                
                // Nếu đang ở tab playlists trong main player, reload luôn
                const userGrid = document.getElementById('user-playlist-grid');
                if (userGrid && !userGrid.classList.contains('hidden')) {
                    if (this.musicPlayer && this.musicPlayer.loadUserPlaylistsInMainPlayer) {
                        await this.musicPlayer.loadUserPlaylistsInMainPlayer();
                    }
                }
            } else {
                this.showNotification(data.error, 'error');
            }
        } catch (error) {
            console.error('Error adding track to playlist:', error);
            this.showNotification('Lỗi khi thêm bài hát vào playlist!', 'error');
        }
    }
    
    async deletePlaylist(playlistId) {
        if (!confirm('Bạn có chắc muốn xóa playlist này?')) {
            return;
        }
        
        try {
            const response = await fetch(`/music/user/playlists/${playlistId}/delete/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': this.getCSRFToken()
                }
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.showNotification(data.message, 'success');
                await this.loadUserPlaylists();
            } else {
                this.showNotification(data.error, 'error');
            }
        } catch (error) {
            console.error('Error deleting playlist:', error);
            this.showNotification('Lỗi khi xóa playlist!', 'error');
        }
    }
    
    openPlaylist(playlistId) {
        // Load and play playlist in main player
        const playlist = this.userPlaylists.find(p => p.id === playlistId);
        if (!playlist) return;
        
        // Load tracks from this playlist
        this.loadAndPlayUserPlaylist(playlistId);
        this.closeSettings();
    }
    
    async loadAndPlayUserPlaylist(playlistId) {
        try {
            const response = await fetch(`/music/user/playlists/${playlistId}/tracks/`);
            
            if (!response.ok) {
                if (response.status === 302 || response.status === 401 || response.status === 403) {
                    this.showNotification('⚠️ Vui lòng đăng nhập để sử dụng tính năng này!', 'info');
                    setTimeout(() => {
                        window.location.href = '/accounts/login/?next=' + window.location.pathname;
                    }, 1500);
                    return;
                }
                throw new Error(`HTTP ${response.status}`);
            }
            
            const data = await response.json();
            
            if (data.success && data.tracks.length > 0) {
                // Convert to music player format
                const playerPlaylist = {
                    id: 'user-playlist-' + data.playlist.id,
                    name: data.playlist.name,
                    tracks: data.tracks.map(track => ({
                        id: track.id,
                        title: track.title,
                        artist: track.artist || 'Unknown Artist',
                        file_url: track.file_url,
                        duration: track.duration
                    }))
                };
                
                // Set as current playlist in music player
                this.musicPlayer.currentPlaylist = playerPlaylist;
                this.musicPlayer.currentTrackIndex = 0;
                
                // ✅ Đảm bảo mini player được mở (remove hidden class)
                const popup = this.musicPlayer.popup;
                if (popup && popup.classList.contains('hidden')) {
                    popup.classList.remove('hidden');
                }
                
                // ✅ Populate track list để hiển thị playlist
                this.musicPlayer.populateTrackList();
                
                // ✅ Đánh dấu user đã tương tác (để autoplay được phép)
                this.musicPlayer.userInteracted = true;
                
                // ✅ Phát bài đầu tiên (truyền index 0, không phải object)
                this.musicPlayer.playTrack(0);
                
                // ✅ Đảm bảo phát luôn (nếu auto_play tắt)
                setTimeout(() => {
                    if (!this.musicPlayer.isPlaying) {
                        this.musicPlayer.audio.play().catch(e => {
                            console.log('Playlist play failed:', e);
                        });
                    }
                }, 100);
                
                this.showNotification(`Đang phát playlist "${data.playlist.name}"`, 'success');
            } else {
                this.showNotification('Playlist chưa có bài hát nào!', 'info');
            }
        } catch (error) {
            console.error('Error loading playlist tracks:', error);
            if (error.message.includes('Unexpected token')) {
                this.showNotification('⚠️ Vui lòng đăng nhập để sử dụng tính năng này!', 'info');
            } else {
                this.showNotification('Lỗi khi load playlist!', 'error');
            }
        }
    }
    
    getCSRFToken() {
        const name = 'csrftoken';
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
    
    showNotification(message, type = 'info') {
        // Simple notification - you can enhance this with better UI
        const color = type === 'success' ? '#28a745' : type === 'error' ? '#dc3545' : '#17a2b8';
        const notification = document.createElement('div');
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: ${color};
            color: white;
            padding: 16px 24px;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.3);
            z-index: 10003;
            font-weight: 600;
            animation: slideInRight 0.3s ease;
        `;
        notification.textContent = message;
        document.body.appendChild(notification);
        
        setTimeout(() => {
            notification.style.animation = 'slideOutRight 0.3s ease';
            setTimeout(() => notification.remove(), 300);
        }, 3000);
    }
}

// Initialize User Music Manager when music player is ready
document.addEventListener('DOMContentLoaded', () => {
    // Wait for music player to initialize
    setTimeout(() => {
        if (window.musicPlayer) {
            window.userMusicManager = new UserMusicManager(window.musicPlayer);
            console.log('✅ User Music Manager initialized');
        }
    }, 500);
});

