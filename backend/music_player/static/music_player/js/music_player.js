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
        this.isRestoringState = false; // Flag để tránh lưu state khi đang restore
        
        this.initializeElements();
        this.bindEvents();
        this.loadSettings();
        this.loadPlaylists();
        
        // Auto refresh every 30 seconds
        this.autoRefreshInterval = setInterval(() => {
            this.checkForUpdates();
        }, 30000);
        
        // Lưu state trước khi chuyển trang
        window.addEventListener('beforeunload', () => {
            this.savePlayerState();
        });
        
        // Lưu state định kỳ mỗi 2 giây
        this.saveStateInterval = setInterval(() => {
            if (this.isPlaying) {
                this.savePlayerState();
            }
        }, 2000);
    }

    initializeElements() {
        // Main elements
        this.popup = document.getElementById('music-player-popup');
        this.fullPlayer = document.getElementById('full-player');
        this.toggle = document.getElementById('music-player-toggle');
        
        // Player elements
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
        this.closeBtn.addEventListener('click', () => this.togglePlayer());
        
        // Refresh button
        this.refreshBtn = document.getElementById('refresh-playlists');
        if (this.refreshBtn) {
            this.refreshBtn.addEventListener('click', () => this.refreshPlaylists());
        }
        
        // Playlist selection
        this.playlistSelect.addEventListener('change', (e) => this.selectPlaylist(e.target.value));
        
        // Control buttons
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
            // Tự động phát khi click vào player (NHƯNG chỉ khi chưa phát)
            if (this.settings.auto_play && this.currentPlaylist && !this.isPlaying) {
                console.log('Auto-playing after click on player');
                this.playTrack(this.currentTrackIndex);
            }
        });
        
        // Tự động phát khi hover vào player (NHƯNG chỉ khi chưa phát)
        this.popup.addEventListener('mouseenter', () => {
            this.userInteracted = true;
            if (this.settings.auto_play && this.currentPlaylist && !this.isPlaying) {
                console.log('Auto-playing after hover');
                this.playTrack(this.currentTrackIndex);
            }
        });
        
        // Đánh dấu user interaction khi click vào document (chỉ một lần)
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
                
                // Thử restore state trước
                const restored = this.restorePlayerState();
                
                if (!restored) {
                    // Nếu không có state để restore, auto-select first playlist
                    if (this.playlists.length > 0 && this.settings.default_playlist_id) {
                        const defaultPlaylist = this.playlists.find(p => p.id === this.settings.default_playlist_id);
                        if (defaultPlaylist) {
                            this.selectPlaylist(defaultPlaylist.id);
                        }
                    } else if (this.playlists.length > 0) {
                        this.selectPlaylist(this.playlists[0].id);
                    }
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
        
        // Lưu state khi chọn playlist mới
        if (!this.isRestoringState) {
            this.savePlayerState();
        }
        
<<<<<<< HEAD
        // Auto-play if enabled (nhưng không auto-play khi đang restore)
        if (this.settings.auto_play && playlist.tracks.length > 0 && !this.isRestoringState) {
=======
        // Auto-play if enabled (nhưng không auto-play khi đang restore hoặc đang phát)
        if (this.settings.auto_play && playlist.tracks.length > 0 && !this.isRestoringState && !this.isPlaying) {
>>>>>>> 029f4c7 (Music 3)
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
        
        const track = this.currentPlaylist.tracks[index];
        const fileUrl = `/media/music/playlist/${track.file_path}`;
        
        // Kiểm tra xem có đang phát cùng track này không
        if (this.currentTrackIndex === index && this.audio.src.endsWith(track.file_path)) {
            console.log('Track already loaded, just resume if paused');
            // Nếu đang tạm dừng thì tiếp tục phát, không load lại
            if (!this.isPlaying) {
                this.audio.play().catch(e => console.log('Play failed:', e));
            }
            return;
        }
        
        this.currentTrackIndex = index;
        
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
                
                // Lưu state khi bắt đầu phát track mới
                if (!this.isRestoringState) {
                    this.savePlayerState();
                }
                
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
        // Lưu state khi bắt đầu phát
        if (!this.isRestoringState) {
            this.savePlayerState();
        }
    }

    onPause() {
        this.isPlaying = false;
        this.updatePlayPauseButtons();
        // Lưu state khi tạm dừng
        if (!this.isRestoringState) {
            this.savePlayerState();
        }
    }

    updatePlayPauseButtons() {
        const icon = this.isPlaying ? 'bi-pause-fill' : 'bi-play-fill';
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

    savePlayerState() {
        if (this.isRestoringState) return; // Không lưu khi đang restore
        
        const state = {
            playlistId: this.currentPlaylist ? this.currentPlaylist.id : null,
            trackIndex: this.currentTrackIndex,
            currentTime: this.audio.currentTime || 0,
            isPlaying: this.isPlaying,
            timestamp: Date.now()
        };
        
        try {
            localStorage.setItem('musicPlayerState', JSON.stringify(state));
        } catch (error) {
            console.error('Error saving player state:', error);
        }
    }

    restorePlayerState() {
        try {
            const stateStr = localStorage.getItem('musicPlayerState');
            if (!stateStr) return false;
            
            const state = JSON.parse(stateStr);
            
            // Chỉ restore nếu state không quá cũ (trong vòng 1 giờ)
            const maxAge = 60 * 60 * 1000; // 1 giờ
            if (Date.now() - state.timestamp > maxAge) {
                localStorage.removeItem('musicPlayerState');
                return false;
            }
            
            // Tìm playlist
            const playlist = this.playlists.find(p => p.id === state.playlistId);
            if (!playlist) return false;
            
            // Set flag để tránh lưu state khi đang restore
            this.isRestoringState = true;
            
            // Restore playlist và track
            this.currentPlaylist = playlist;
            this.playlistSelect.value = playlist.id;
            this.populateTrackList();
            
            // Restore track index
            this.currentTrackIndex = state.trackIndex || 0;
            
            // Load track
            if (playlist.tracks && playlist.tracks[this.currentTrackIndex]) {
                const track = playlist.tracks[this.currentTrackIndex];
                const fileUrl = `/media/music/playlist/${track.file_path}`;
                
                this.audio.src = fileUrl;
                
                // Update UI ngay
                this.updateCurrentTrack();
                this.updateTrackListSelection();
                
                // Sử dụng Promise để đảm bảo thứ tự load -> set time -> play
                const restoreAudio = async () => {
                    try {
                        // Load audio
                        this.audio.load();
                        
                        // Đợi metadata load xong
                        await new Promise((resolve) => {
                            this.audio.addEventListener('loadedmetadata', resolve, { once: true });
                        });
                        
                        // Set thời gian nếu có
                        if (state.currentTime && state.currentTime > 0 && state.currentTime < this.audio.duration) {
                            this.audio.currentTime = state.currentTime;
                            console.log('Restored playback position to:', state.currentTime);
                            
                            // Đợi seek hoàn tất
                            await new Promise((resolve) => {
                                this.audio.addEventListener('seeked', resolve, { once: true });
                            });
                        }
                        
                        // Tự động phát lại nếu đang phát trước đó
                        if (state.isPlaying) {
                            this.userInteracted = true;
                            await this.audio.play().catch(e => {
                                console.log('Autoplay prevented after restore:', e);
                            });
                        }
                        
                        console.log('Player state restored successfully');
                    } catch (error) {
                        console.error('Error restoring audio:', error);
                    } finally {
                        // Xong rồi, bỏ flag
                        this.isRestoringState = false;
                    }
                };
                
                restoreAudio();
                return true;
            }
            
            this.isRestoringState = false;
            return false;
            
        } catch (error) {
            console.error('Error restoring player state:', error);
            this.isRestoringState = false;
            return false;
        }
    }

    destroy() {
        // Save state trước khi destroy
        this.savePlayerState();
        
        // Cleanup intervals
        if (this.autoRefreshInterval) {
            clearInterval(this.autoRefreshInterval);
        }
        if (this.saveStateInterval) {
            clearInterval(this.saveStateInterval);
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
