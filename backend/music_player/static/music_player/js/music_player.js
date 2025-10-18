class MusicPlayer {
    constructor() {
        this.audio = document.getElementById('audio-player');
        this.playlists = [];
        this.currentPlaylist = null;
        this.currentTrackIndex = 0;
        this.isPlaying = false;
        this.isShuffled = false;
        this.repeatMode = 'all'; // 'none', 'one', 'all'
        this.volume = 0.7;
        this.isMuted = false;
        this.lastRefreshTime = Date.now();
        this.settings = {
            auto_play: true,
            volume: 0.7,
            repeat_mode: 'all',
            shuffle: false
        };
        
        this.userInteracted = false; // Track user interaction for autoplay
        
        this.initializeElements();
        this.bindEvents();
        this.loadSettings();
        this.loadPlaylists();
        
        // Tự động phát khi load trang (sau khi có user interaction)
        setTimeout(() => {
            if (this.settings.auto_play && this.currentPlaylist && !this.isPlaying) {
                this.userInteracted = true;
                this.playTrack(this.currentTrackIndex);
            }
        }, 1000);
        
        // Auto refresh every 30 seconds
        this.autoRefreshInterval = setInterval(() => {
            this.checkForUpdates();
        }, 30000);
    }

    initializeElements() {
        // Main elements
        this.popup = document.getElementById('music-player-popup');
        this.miniPlayer = document.getElementById('mini-player');
        this.fullPlayer = document.getElementById('full-player');
        this.toggle = document.getElementById('music-player-toggle');
        
        // Mini player elements
        this.miniTrackTitle = document.getElementById('mini-track-title');
        this.miniTrackArtist = document.getElementById('mini-track-artist');
        this.miniPlayPause = document.getElementById('mini-play-pause');
        this.miniNext = document.getElementById('mini-next');
        this.miniExpand = document.getElementById('mini-expand');
        this.miniProgressFill = document.getElementById('mini-progress-fill');
        
        // Full player elements
        this.playlistSelect = document.getElementById('playlist-select');
        this.trackList = document.getElementById('track-list');
        this.currentTrackTitle = document.getElementById('current-track-title');
        this.currentTrackArtist = document.getElementById('current-track-artist');
        this.currentTime = document.getElementById('current-time');
        this.totalTime = document.getElementById('total-time');
        this.progressFill = document.getElementById('progress-fill');
        this.progressHandle = document.getElementById('progress-handle');
        this.playPauseBtn = document.getElementById('play-pause-btn');
        this.prevBtn = document.getElementById('prev-btn');
        this.nextBtn = document.getElementById('next-btn');
        this.shuffleBtn = document.getElementById('shuffle-btn');
        this.repeatBtn = document.getElementById('repeat-btn');
        this.muteBtn = document.getElementById('mute-btn');
        this.volumeFill = document.getElementById('volume-fill');
        this.volumeHandle = document.getElementById('volume-handle');
        this.closeBtn = document.getElementById('player-close');
    }

    bindEvents() {
        // Toggle events
        this.toggle.addEventListener('click', () => this.togglePlayer());
        this.miniExpand.addEventListener('click', () => this.expandPlayer());
        this.closeBtn.addEventListener('click', () => this.collapsePlayer());
        
        // Refresh button
        this.refreshBtn = document.getElementById('refresh-playlists');
        if (this.refreshBtn) {
            this.refreshBtn.addEventListener('click', () => this.refreshPlaylists());
        }
        
        // Playlist selection
        this.playlistSelect.addEventListener('change', (e) => this.selectPlaylist(e.target.value));
        
        // Control buttons
        this.miniPlayPause.addEventListener('click', () => this.togglePlayPause());
        this.miniNext.addEventListener('click', () => this.nextTrack());
        this.playPauseBtn.addEventListener('click', () => this.togglePlayPause());
        this.prevBtn.addEventListener('click', () => this.previousTrack());
        this.nextBtn.addEventListener('click', () => this.nextTrack());
        this.shuffleBtn.addEventListener('click', () => this.toggleShuffle());
        this.repeatBtn.addEventListener('click', () => this.toggleRepeat());
        this.muteBtn.addEventListener('click', () => this.toggleMute());
        
        // Progress bar
        this.progressFill.parentElement.addEventListener('click', (e) => this.seekTo(e));
        this.progressHandle.addEventListener('mousedown', (e) => this.startSeeking(e));
        
        // Volume control
        this.volumeFill.parentElement.addEventListener('click', (e) => this.setVolume(e));
        this.volumeHandle.addEventListener('mousedown', (e) => this.startVolumeSeeking(e));
        
        // Audio events
        this.audio.addEventListener('loadedmetadata', () => this.updateDuration());
        this.audio.addEventListener('timeupdate', () => this.updateProgress());
        this.audio.addEventListener('ended', () => this.onTrackEnd());
        this.audio.addEventListener('play', () => this.onPlay());
        this.audio.addEventListener('pause', () => this.onPause());
        
        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => this.handleKeyboard(e));
        
        // Prevent popup from closing when clicking inside
        this.popup.addEventListener('click', (e) => {
            e.stopPropagation();
            this.userInteracted = true;
            // Tự động phát khi click vào player
            if (this.settings.auto_play && this.currentPlaylist && !this.isPlaying) {
                console.log('Auto-playing after click on player');
                this.playTrack(this.currentTrackIndex);
            }
        });
        
        // Đánh dấu user interaction khi click vào controls
        this.playPauseBtn.addEventListener('click', () => {
            this.userInteracted = true;
        });
        
        this.nextBtn.addEventListener('click', () => {
            this.userInteracted = true;
        });
        
        this.prevBtn.addEventListener('click', () => {
            this.userInteracted = true;
        });
        
        // Tự động phát khi hover vào player
        this.popup.addEventListener('mouseenter', () => {
            this.userInteracted = true;
            // Tự động phát khi hover vào player
            if (this.settings.auto_play && this.currentPlaylist && !this.isPlaying) {
                console.log('Auto-playing after hover');
                this.playTrack(this.currentTrackIndex);
            }
        });
        
        // Tự động phát khi click vào player
        this.popup.addEventListener('click', (e) => {
            e.stopPropagation();
            this.userInteracted = true;
            // Tự động phát khi click vào player
            if (this.settings.auto_play && this.currentPlaylist && !this.isPlaying) {
                console.log('Auto-playing after click on player');
                this.playTrack(this.currentTrackIndex);
            }
        });
        
        // Thêm event listener cho document để đánh dấu user interaction
        document.addEventListener('click', (e) => {
            this.userInteracted = true;
            // Tự động phát nếu chưa phát và có playlist
            if (this.settings.auto_play && this.currentPlaylist && !this.isPlaying) {
                console.log('Auto-playing after user click');
                this.playTrack(this.currentTrackIndex);
            }
        }, { once: true });
        
        document.addEventListener('keydown', (e) => {
            this.userInteracted = true;
            // Tự động phát nếu chưa phát và có playlist
            if (this.settings.auto_play && this.currentPlaylist && !this.isPlaying) {
                console.log('Auto-playing after user keydown');
                this.playTrack(this.currentTrackIndex);
            }
        }, { once: true });
    }

    async loadPlaylists() {
        try {
            const response = await fetch('/music/api/');
            const data = await response.json();
            
            if (data.success) {
                this.playlists = data.playlists;
                this.populatePlaylistSelect();
                
                // Auto-select first playlist if available
                if (this.playlists.length > 0 && this.settings.default_playlist_id) {
                    const defaultPlaylist = this.playlists.find(p => p.id === this.settings.default_playlist_id);
                    if (defaultPlaylist) {
                        this.selectPlaylist(defaultPlaylist.id);
                    }
                } else if (this.playlists.length > 0) {
                    this.selectPlaylist(this.playlists[0].id);
                }
            }
        } catch (error) {
            console.error('Error loading playlists:', error);
        }
    }

    async refreshPlaylists() {
        // Refresh playlists from server
        try {
            const response = await fetch('/music/api/');
            const data = await response.json();
            
            if (data.success) {
                this.playlists = data.playlists;
                this.populatePlaylistSelect();
                
                // Keep current playlist if still exists
                if (this.currentPlaylist) {
                    const updatedPlaylist = this.playlists.find(p => p.id === this.currentPlaylist.id);
                    if (updatedPlaylist) {
                        this.currentPlaylist = updatedPlaylist;
                        this.populateTrackList();
                        this.updateCurrentTrack();
                    }
                }
                
                console.log('Playlists refreshed successfully');
            }
        } catch (error) {
            console.error('Error refreshing playlists:', error);
        }
    }

    async checkForUpdates() {
        // Check if there are new tracks without full refresh
        try {
            const response = await fetch('/music/api/');
            const data = await response.json();
            
            if (data.success && this.currentPlaylist) {
                const updatedPlaylist = data.playlists.find(p => p.id === this.currentPlaylist.id);
                if (updatedPlaylist && updatedPlaylist.tracks.length !== this.currentPlaylist.tracks.length) {
                    console.log('New tracks detected, refreshing playlist...');
                    this.refreshPlaylists();
                }
            }
        } catch (error) {
            console.error('Error checking for updates:', error);
        }
    }

    populatePlaylistSelect() {
        this.playlistSelect.innerHTML = '<option value="">Chọn playlist...</option>';
        this.playlists.forEach(playlist => {
            const option = document.createElement('option');
            option.value = playlist.id;
            option.textContent = playlist.name;
            this.playlistSelect.appendChild(option);
        });
    }

    selectPlaylist(playlistId) {
        const playlist = this.playlists.find(p => p.id === parseInt(playlistId));
        if (!playlist) return;
        
        console.log('Selecting playlist:', playlist);
        this.currentPlaylist = playlist;
        this.currentTrackIndex = 0;
        this.populateTrackList();
        this.updateCurrentTrack();
        
        // Auto-play if enabled
        if (this.settings.auto_play && playlist.tracks.length > 0) {
            console.log('Auto-playing track 0');
            // Đánh dấu user interaction TRƯỚC KHI phát nhạc
            this.userInteracted = true;
            // Delay một chút để đảm bảo user interaction được ghi nhận
            setTimeout(() => {
                this.playTrack(0);
            }, 100);
        }
    }

    populateTrackList() {
        if (!this.currentPlaylist) return;
        
        this.trackList.innerHTML = '';
        
        if (this.currentPlaylist.tracks.length === 0) {
            this.trackList.innerHTML = `
                <div class="empty-state">
                    <i class="bi bi-music-note"></i>
                    <p>Chưa có bài hát nào</p>
                </div>
            `;
            return;
        }
        
        this.currentPlaylist.tracks.forEach((track, index) => {
            const trackItem = document.createElement('div');
            trackItem.className = 'track-item';
            trackItem.innerHTML = `
                <div class="track-item-info">
                    <div class="track-item-title">${track.title}</div>
                    <div class="track-item-artist">${track.artist}</div>
                </div>
                <div class="track-item-duration">${track.duration_formatted}</div>
            `;
            
            trackItem.addEventListener('click', () => this.playTrack(index));
            this.trackList.appendChild(trackItem);
        });
    }

    showMessage(message, type = 'info') {
        // Tạo thông báo đơn giản
        console.log(`[${type.toUpperCase()}] ${message}`);
        
        // Có thể thêm toast notification sau này
        if (type === 'error') {
            alert('Lỗi: ' + message);
        } else if (type === 'info') {
            // Chỉ log, không hiển thị alert cho info
        }
    }
    
    playTrack(index) {
        if (!this.currentPlaylist || !this.currentPlaylist.tracks[index]) return;
        
        this.currentTrackIndex = index;
        const track = this.currentPlaylist.tracks[index];
        
        console.log('Playing track:', track);
        console.log('Current playlist:', this.currentPlaylist);
        
        // Kiểm tra dữ liệu trước khi tạo URL
        if (!this.currentPlaylist.folder_path || !track.file_path) {
            console.error('Missing folder_path or file_path:', {
                folder_path: this.currentPlaylist.folder_path,
                file_path: track.file_path
            });
            this.showMessage('Dữ liệu playlist không đầy đủ', 'error');
            return;
        }
        
        // Kiểm tra file có tồn tại không
        const fileUrl = `/media/music/playlist/${track.file_path}`;
        console.log('File URL:', fileUrl);
        
        try {
            // Kiểm tra file có tồn tại không trước khi load
            fetch(fileUrl, { method: 'HEAD' }).then(response => {
                if (!response.ok) {
                    console.error(`File not found: ${fileUrl}`);
                    this.showMessage('File nhạc không tồn tại: ' + track.title, 'error');
                    return;
                }
                
                this.audio.src = fileUrl;
                this.audio.load();
                
                this.updateCurrentTrack();
                this.updateTrackListSelection();
                
                if (this.settings.auto_play && this.userInteracted) {
                    this.audio.play().catch(e => console.log('Autoplay prevented:', e));
                } else if (this.settings.auto_play && !this.userInteracted) {
                    // Tự động phát ngay cả khi chưa có user interaction
                    this.audio.play().catch(e => {
                        console.log('Autoplay prevented, waiting for user interaction:', e);
                        this.showMessage('Click để bắt đầu phát nhạc', 'info');
                    });
                }
            }).catch(error => {
                console.error('File check failed:', error);
                this.showMessage('Không thể tải bài hát: ' + track.title, 'error');
            });
        } catch (error) {
            console.error('Play track failed:', error);
        }
    }

    updateCurrentTrack() {
        if (!this.currentPlaylist || !this.currentPlaylist.tracks[this.currentTrackIndex]) return;
        
        const track = this.currentPlaylist.tracks[this.currentTrackIndex];
        
        this.miniTrackTitle.textContent = track.title;
        this.miniTrackArtist.textContent = track.artist;
        this.currentTrackTitle.textContent = track.title;
        this.currentTrackArtist.textContent = track.artist;
    }

    updateTrackListSelection() {
        const trackItems = this.trackList.querySelectorAll('.track-item');
        trackItems.forEach((item, index) => {
            item.classList.toggle('active', index === this.currentTrackIndex);
        });
    }

    togglePlayPause() {
        if (this.isPlaying) {
            this.audio.pause();
        } else {
            // Đánh dấu user đã tương tác
            this.userInteracted = true;
            this.audio.play().catch(e => {
                console.log('Play failed:', e);
                this.showMessage('Không thể phát nhạc. Vui lòng thử lại.', 'error');
            });
        }
    }

    previousTrack() {
        if (!this.currentPlaylist) return;
        
        if (this.currentTrackIndex > 0) {
            this.playTrack(this.currentTrackIndex - 1);
        } else if (this.repeatMode === 'all') {
            this.playTrack(this.currentPlaylist.tracks.length - 1);
        }
    }

    nextTrack() {
        if (!this.currentPlaylist) return;
        
        if (this.currentTrackIndex < this.currentPlaylist.tracks.length - 1) {
            this.playTrack(this.currentTrackIndex + 1);
        } else if (this.repeatMode === 'all') {
            this.playTrack(0);
        }
    }

    onTrackEnd() {
        if (this.repeatMode === 'one') {
            this.audio.currentTime = 0;
            this.audio.play();
        } else {
            this.nextTrack();
        }
    }

    onPlay() {
        this.isPlaying = true;
        this.updatePlayPauseButtons();
    }

    onPause() {
        this.isPlaying = false;
        this.updatePlayPauseButtons();
    }

    updatePlayPauseButtons() {
        const icon = this.isPlaying ? 'bi-pause-fill' : 'bi-play-fill';
        this.miniPlayPause.innerHTML = `<i class="bi ${icon}"></i>`;
        this.playPauseBtn.innerHTML = `<i class="bi ${icon}"></i>`;
    }

    updateDuration() {
        const duration = this.audio.duration;
        this.totalTime.textContent = this.formatTime(duration);
    }

    updateProgress() {
        if (!this.audio.duration) return;
        
        const progress = (this.audio.currentTime / this.audio.duration) * 100;
        this.progressFill.style.width = `${progress}%`;
        this.miniProgressFill.style.width = `${progress}%`;
        this.progressHandle.style.left = `${progress}%`;
        
        this.currentTime.textContent = this.formatTime(this.audio.currentTime);
    }

    formatTime(seconds) {
        const mins = Math.floor(seconds / 60);
        const secs = Math.floor(seconds % 60);
        return `${mins}:${secs.toString().padStart(2, '0')}`;
    }

    seekTo(event) {
        if (!this.audio.duration) return;
        
        const rect = event.currentTarget.getBoundingClientRect();
        const percent = (event.clientX - rect.left) / rect.width;
        this.audio.currentTime = percent * this.audio.duration;
    }

    startSeeking(event) {
        event.preventDefault();
        const handleSeek = (e) => {
            if (!this.audio.duration) return;
            const rect = this.progressFill.parentElement.getBoundingClientRect();
            const percent = Math.max(0, Math.min(1, (e.clientX - rect.left) / rect.width));
            this.audio.currentTime = percent * this.audio.duration;
        };
        
        document.addEventListener('mousemove', handleSeek);
        document.addEventListener('mouseup', () => {
            document.removeEventListener('mousemove', handleSeek);
        });
    }

    setVolume(event) {
        const rect = event.currentTarget.getBoundingClientRect();
        const percent = Math.max(0, Math.min(1, (event.clientX - rect.left) / rect.width));
        this.volume = percent;
        this.audio.volume = this.isMuted ? 0 : this.volume;
        this.updateVolumeDisplay();
        this.saveSettings();
    }

    startVolumeSeeking(event) {
        event.preventDefault();
        const handleVolumeSeek = (e) => {
            const rect = this.volumeFill.parentElement.getBoundingClientRect();
            const percent = Math.max(0, Math.min(1, (e.clientX - rect.left) / rect.width));
            this.volume = percent;
            this.audio.volume = this.isMuted ? 0 : this.volume;
            this.updateVolumeDisplay();
        };
        
        document.addEventListener('mousemove', handleVolumeSeek);
        document.addEventListener('mouseup', () => {
            document.removeEventListener('mousemove', handleVolumeSeek);
            this.saveSettings();
        });
    }

    toggleMute() {
        this.isMuted = !this.isMuted;
        this.audio.volume = this.isMuted ? 0 : this.volume;
        this.updateVolumeDisplay();
    }

    updateVolumeDisplay() {
        const volumePercent = this.isMuted ? 0 : this.volume * 100;
        this.volumeFill.style.width = `${volumePercent}%`;
        this.volumeHandle.style.left = `${volumePercent}%`;
        
        const icon = this.isMuted ? 'bi-volume-mute-fill' : 
                    this.volume === 0 ? 'bi-volume-mute-fill' :
                    this.volume < 0.5 ? 'bi-volume-down-fill' : 'bi-volume-up-fill';
        this.muteBtn.innerHTML = `<i class="bi ${icon}"></i>`;
    }

    toggleShuffle() {
        this.isShuffled = !this.isShuffled;
        this.shuffleBtn.classList.toggle('active', this.isShuffled);
        this.saveSettings();
    }

    toggleRepeat() {
        const modes = ['none', 'one', 'all'];
        const currentIndex = modes.indexOf(this.repeatMode);
        this.repeatMode = modes[(currentIndex + 1) % modes.length];
        
        this.repeatBtn.classList.toggle('active', this.repeatMode !== 'none');
        this.saveSettings();
    }

    togglePlayer() {
        this.popup.classList.toggle('hidden');
        if (!this.popup.classList.contains('hidden')) {
            this.expandPlayer();
        }
    }

    expandPlayer() {
        this.miniPlayer.style.display = 'none';
        this.fullPlayer.style.display = 'block';
    }

    collapsePlayer() {
        this.fullPlayer.style.display = 'none';
        this.miniPlayer.style.display = 'block';
    }

    handleKeyboard(event) {
        if (event.target.tagName === 'INPUT' || event.target.tagName === 'TEXTAREA') return;
        
        switch(event.code) {
            case 'Space':
                event.preventDefault();
                this.togglePlayPause();
                break;
            case 'ArrowLeft':
                event.preventDefault();
                this.previousTrack();
                break;
            case 'ArrowRight':
                event.preventDefault();
                this.nextTrack();
                break;
            case 'KeyM':
                event.preventDefault();
                this.toggleMute();
                break;
        }
    }

    async loadSettings() {
        try {
            const response = await fetch('/music/api/settings/');
            const data = await response.json();
            
            if (data.success) {
                this.settings = data.settings;
                this.volume = this.settings.volume;
                this.repeatMode = this.settings.repeat_mode;
                this.isShuffled = this.settings.shuffle;
                
                this.audio.volume = this.volume;
                this.updateVolumeDisplay();
                this.repeatBtn.classList.toggle('active', this.repeatMode !== 'none');
                this.shuffleBtn.classList.toggle('active', this.isShuffled);
            }
        } catch (error) {
            console.error('Error loading settings:', error);
        }
    }

    async saveSettings() {
        try {
            await fetch('/music/api/settings/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: JSON.stringify({
                    auto_play: this.settings.auto_play,
                    volume: this.volume,
                    repeat_mode: this.repeatMode,
                    shuffle: this.isShuffled,
                    default_playlist_id: this.currentPlaylist ? this.currentPlaylist.id : null
                })
            });
        } catch (error) {
            console.error('Error saving settings:', error);
        }
    }

    getCSRFToken() {
        return document.querySelector('[name=csrfmiddlewaretoken]')?.value || 
               document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || '';
    }

    destroy() {
        // Cleanup intervals
        if (this.autoRefreshInterval) {
            clearInterval(this.autoRefreshInterval);
        }
    }
}

// Initialize music player when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.musicPlayer = new MusicPlayer();
});

// Cleanup when page unloads
window.addEventListener('beforeunload', () => {
    if (window.musicPlayer) {
        window.musicPlayer.destroy();
    }
});
