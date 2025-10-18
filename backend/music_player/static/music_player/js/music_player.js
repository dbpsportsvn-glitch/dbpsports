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
        this.isLoadingTrack = false; // Flag để tránh load track nhiều lần cùng lúc
        this.hasAutoPlayed = false; // Flag để track đã auto-play chưa
        this.restoreAttempted = false; // Flag để chỉ restore 1 lần duy nhất
        
        // Drag and drop variables
        this.isDragging = false;
        this.dragOffset = { x: 0, y: 0 };
        
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
            if (!this.isRestoringState) {
                this.savePlayerState();
            }
        });
        
        // Lưu state định kỳ mỗi 3 giây (chỉ khi đang phát)
        this.saveStateInterval = setInterval(() => {
            if (this.isPlaying && !this.isRestoringState && this.currentPlaylist) {
                this.savePlayerState();
            }
        }, 3000);
    }

    initializeElements() {
        // Main elements
        this.popup = document.getElementById('music-player-popup');
        this.fullPlayer = document.getElementById('full-player');
        this.toggle = document.getElementById('music-player-toggle');
        this.playerHeader = this.fullPlayer?.querySelector('.player-header');
        
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
        
        // Debug: Kiểm tra các elements quan trọng (chỉ log khi có lỗi)
        const elementsStatus = {
            currentTime: !!this.currentTime,
            totalTime: !!this.totalTime,
            progressFill: !!this.progressFill,
            progressHandle: !!this.progressHandle,
            audio: !!this.audio
        };
        
        // Chỉ log nếu có elements bị thiếu
        const missingElements = Object.entries(elementsStatus).filter(([key, exists]) => !exists);
        if (missingElements.length > 0) {
            console.warn('Missing elements:', missingElements.map(([key]) => key));
        }
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
        
        // Progress bar - improved seeking
        this.progressBar = this.progressFill.parentElement;
        if (this.progressBar) {
            // Click to seek
            this.progressBar.addEventListener('click', (e) => {
                this.seekTo(e);
            });
            // Touch support for mobile
            this.progressBar.addEventListener('touchstart', (e) => {
                e.preventDefault();
                this.seekTo(e.touches[0]);
            });
        }
        if (this.progressHandle) {
            // Mouse drag
            this.progressHandle.addEventListener('mousedown', (e) => {
                e.stopPropagation(); // Prevent click event on bar
                this.startSeeking(e);
            });
            // Touch drag for mobile
            this.progressHandle.addEventListener('touchstart', (e) => {
                e.stopPropagation();
                e.preventDefault();
                this.startSeeking(e.touches[0]);
            });
        }
        
        // Volume control
        this.volumeFill.parentElement.addEventListener('click', (e) => this.setVolume(e));
        this.volumeHandle.addEventListener('mousedown', (e) => this.startVolumeSeeking(e));
        
        // Audio events
        this.audio.addEventListener('loadedmetadata', () => {
            this.updateDuration();
        });
        this.audio.addEventListener('timeupdate', () => this.updateProgress());
        this.audio.addEventListener('ended', () => this.onTrackEnd());
        this.audio.addEventListener('play', () => this.onPlay());
        this.audio.addEventListener('pause', () => this.onPause());
        this.audio.addEventListener('error', (e) => {
            console.error('Audio error:', e);
        });
        
        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => this.handleKeyboard(e));
        
        // Drag and drop for player header (Desktop)
        if (this.playerHeader) {
            this.playerHeader.addEventListener('mousedown', (e) => this.startDragging(e));
            // Touch events for mobile
            this.playerHeader.addEventListener('touchstart', (e) => this.startDragging(e), { passive: false });
        }
        document.addEventListener('mousemove', (e) => this.drag(e));
        document.addEventListener('mouseup', () => this.stopDragging());
        // Touch events for mobile
        document.addEventListener('touchmove', (e) => this.drag(e), { passive: false });
        document.addEventListener('touchend', () => this.stopDragging());
        document.addEventListener('touchcancel', () => this.stopDragging());
        
        // Prevent popup from closing when clicking inside
        this.popup.addEventListener('click', (e) => {
            e.stopPropagation();
            this.userInteracted = true;
        });
        
        // Click bất kỳ đâu trên màn hình → auto open player + auto play (chỉ 1 lần)
        document.addEventListener('click', (e) => {
            this.userInteracted = true;
            
            // Auto-open player và auto-play nếu có playlist, chưa phát, và chưa từng auto-play
            if (!this.hasAutoPlayed && this.currentPlaylist && !this.isPlaying && !this.isRestoringState) {
                console.log('Auto-opening player and playing after first user click');
                this.hasAutoPlayed = true;
                
                // Mở player nếu đang ẩn
                if (this.popup.classList.contains('hidden')) {
                    this.popup.classList.remove('hidden');
                }
                
                // Phát nhạc
                this.playTrack(this.currentTrackIndex);
            }
            
            // Click ngoài khu vực player → thu nhỏ player (nhưng không áp dụng khi vừa mới auto-open)
            if (!this.popup.classList.contains('hidden')) {
                // Kiểm tra xem click có nằm trong popup hoặc toggle button không
                if (!this.popup.contains(e.target) && !this.toggle.contains(e.target)) {
                    // Chỉ close nếu đã auto-play rồi và không phải click đầu tiên
                    if (this.hasAutoPlayed) {
                        console.log('Clicked outside player, closing...');
                        this.togglePlayer();
                    }
                }
            }
        }, { once: false });
        
        document.addEventListener('keydown', () => {
            this.userInteracted = true;
            
            // Auto-open và auto-play khi nhấn phím (nếu chưa auto-play)
            if (!this.hasAutoPlayed && this.currentPlaylist && !this.isPlaying && !this.isRestoringState) {
                console.log('Auto-opening player and playing after keyboard interaction');
                this.hasAutoPlayed = true;
                
                // Mở player nếu đang ẩn
                if (this.popup.classList.contains('hidden')) {
                    this.popup.classList.remove('hidden');
                }
                
                // Phát nhạc
                this.playTrack(this.currentTrackIndex);
            }
        }, { once: true });
        
        // Tab switching
        this.initTabSystem();
    }
    
    initTabSystem() {
        // Scope tab elements within music player popup only
        const popup = document.getElementById('music-player-popup');
        if (!popup) {
            console.error('Music player popup not found');
            return;
        }
        
        const tabHeaders = popup.querySelectorAll('.tab-header');
        const tabContents = popup.querySelectorAll('.tab-content');
        
        console.log('Tab system initialized:', {
            headers: tabHeaders.length,
            contents: tabContents.length
        });
        
        tabHeaders.forEach(header => {
            header.addEventListener('click', (e) => {
                e.preventDefault();
                e.stopPropagation();
                
                const tabName = header.getAttribute('data-tab');
                console.log('Tab clicked:', tabName);
                
                // Remove active class from all headers and contents
                tabHeaders.forEach(h => h.classList.remove('active'));
                tabContents.forEach(c => c.classList.remove('active'));
                
                // Add active class to clicked header and corresponding content
                header.classList.add('active');
                const targetContent = popup.querySelector(`#tab-${tabName}`);
                if (targetContent) {
                    targetContent.classList.add('active');
                    console.log('Tab switched to:', tabName);
                } else {
                    console.error('Tab content not found:', `tab-${tabName}`);
                }
            });
        });
    }

    async loadPlaylists() {
        try {
            const response = await fetch('/music/api/');
            const data = await response.json();
            
            if (data.success) {
                this.playlists = data.playlists;
                this.populatePlaylistSelect();
                
                // Thử restore state trước (chỉ 1 lần)
                if (!this.restoreAttempted) {
                    this.restoreAttempted = true;
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
        // Populate hidden select for backward compatibility
        this.playlistSelect.innerHTML = '<option value="">Chọn playlist...</option>';
        this.playlists.forEach(playlist => {
            const option = document.createElement('option');
            option.value = playlist.id;
            option.textContent = playlist.name;
            this.playlistSelect.appendChild(option);
        });
        
        // Populate playlist grid with beautiful cards
        this.populatePlaylistGrid();
    }
    
    populatePlaylistGrid() {
        const playlistGrid = document.getElementById('playlist-grid');
        if (!playlistGrid) return;
        
        if (this.playlists.length === 0) {
            playlistGrid.innerHTML = `
                <div class="empty-state">
                    <i class="bi bi-collection-play"></i>
                    <p>Chưa có playlist nào</p>
                </div>
            `;
            return;
        }
        
        playlistGrid.innerHTML = '';
        this.playlists.forEach(playlist => {
            const card = document.createElement('div');
            card.className = 'playlist-card';
            if (this.currentPlaylist && this.currentPlaylist.id === playlist.id) {
                card.classList.add('active');
            }
            card.dataset.playlistId = playlist.id;
            
            card.innerHTML = `
                <i class="bi bi-vinyl-fill playlist-card-icon"></i>
                <div class="playlist-card-name" title="${playlist.name}">${playlist.name}</div>
                <div class="playlist-card-count">${playlist.tracks_count || playlist.tracks?.length || 0} bài hát</div>
            `;
            
            card.addEventListener('click', () => {
                // Update select value
                this.playlistSelect.value = playlist.id;
                // Select playlist
                this.selectPlaylist(playlist.id);
                // Update active state
                playlistGrid.querySelectorAll('.playlist-card').forEach(c => c.classList.remove('active'));
                card.classList.add('active');
                // Switch to tracks tab
                const tracksTab = document.querySelector('[data-tab="tracks"]');
                if (tracksTab) {
                    tracksTab.click();
                }
            });
            
            playlistGrid.appendChild(card);
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
        
        // Auto-play if enabled (nhưng không auto-play khi đang restore hoặc đang phát)
        // Chỉ auto-play nếu user đã tương tác
        if (this.settings.auto_play && playlist.tracks.length > 0 && !this.isRestoringState && !this.isPlaying && this.userInteracted) {
            console.log('Auto-playing track 0 after playlist selection');
            // Delay một chút để đảm bảo UI đã update
            setTimeout(() => {
                // Kiểm tra lại isPlaying để tránh trigger nhiều lần
                if (!this.isPlaying) {
                    this.playTrack(0);
                }
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
        
        // Nếu đang load track hoặc đang restore, không làm gì
        if (this.isLoadingTrack || this.isRestoringState) {
            return;
        }
        
        const track = this.currentPlaylist.tracks[index];
        
        // Kiểm tra xem có đang phát cùng track này không
        const currentSrc = this.audio.src;
        const isSameTrack = this.currentTrackIndex === index && currentSrc && currentSrc.includes(track.file_path);
        
        if (isSameTrack) {
            // Nếu đang tạm dừng thì tiếp tục phát, không load lại
            if (!this.isPlaying) {
                this.audio.play().catch(e => console.log('Play failed:', e));
            }
            return;
        }
        
        // Đánh dấu đang load track
        this.isLoadingTrack = true;
        this.currentTrackIndex = index;
        
        const fileUrl = `/media/music/playlist/${track.file_path}`;
        
        // Load track mới
        this.audio.src = fileUrl;
        this.audio.load();
        
        // Update UI ngay
        this.updateCurrentTrack();
        this.updateTrackListSelection();
        
        // Đợi audio sẵn sàng rồi phát
        const onCanPlay = () => {
            this.isLoadingTrack = false;
            
            // Lưu state
            if (!this.isRestoringState) {
                this.savePlayerState();
            }
            
            // Auto play nếu được phép
            if (this.settings.auto_play && this.userInteracted) {
                this.audio.play().catch(e => {
                    console.log('Autoplay prevented:', e.message);
                });
            }
        };
        
        const onError = (e) => {
            this.isLoadingTrack = false;
            console.error('Error loading track:', e);
            this.showMessage('Không thể tải bài hát: ' + track.title, 'error');
        };
        
        // Sử dụng once: true để tránh duplicate listeners
        this.audio.addEventListener('canplaythrough', onCanPlay, { once: true });
        this.audio.addEventListener('error', onError, { once: true });
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
        
        let prevIndex;
        
        if (this.isShuffled) {
            // Shuffle mode: chọn ngẫu nhiên
            do {
                prevIndex = Math.floor(Math.random() * this.currentPlaylist.tracks.length);
            } while (prevIndex === this.currentTrackIndex && this.currentPlaylist.tracks.length > 1);
        } else {
            // Normal mode: theo thứ tự
            if (this.currentTrackIndex > 0) {
                prevIndex = this.currentTrackIndex - 1;
            } else if (this.repeatMode === 'all') {
                prevIndex = this.currentPlaylist.tracks.length - 1;
            } else {
                return; // Không làm gì nếu không có repeat mode
            }
        }
        
        this.playTrack(prevIndex);
    }

    nextTrack() {
        if (!this.currentPlaylist) return;
        
        let nextIndex;
        
        if (this.isShuffled) {
            // Shuffle mode: chọn ngẫu nhiên
            do {
                nextIndex = Math.floor(Math.random() * this.currentPlaylist.tracks.length);
            } while (nextIndex === this.currentTrackIndex && this.currentPlaylist.tracks.length > 1);
        } else {
            // Normal mode: theo thứ tự
            if (this.currentTrackIndex < this.currentPlaylist.tracks.length - 1) {
                nextIndex = this.currentTrackIndex + 1;
            } else if (this.repeatMode === 'all') {
                nextIndex = 0;
            } else {
                // Nếu không có repeat mode 'all' và đã hết playlist, dừng lại
                this.audio.pause();
                this.isPlaying = false;
                this.updatePlayPauseButtons();
                return;
            }
        }
        
        this.playTrack(nextIndex);
    }

    onTrackEnd() {
        console.log('Track ended, repeat mode:', this.repeatMode);
        if (this.repeatMode === 'one') {
            // Lặp lại bài hiện tại
            this.audio.currentTime = 0;
            this.audio.play().catch(e => console.log('Play failed:', e));
        } else if (this.repeatMode === 'all') {
            // Chuyển bài tiếp theo (có thể quay về đầu)
            this.nextTrack();
        } else {
            // Không lặp - chuyển bài tiếp theo
            this.nextTrack();
        }
    }

    onPlay() {
        this.isPlaying = true;
        this.updatePlayPauseButtons();
        
        // Force update thời gian khi bắt đầu phát
        this.updateDuration();
        this.updateProgress();
        
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
        if (this.totalTime && duration) {
            this.totalTime.textContent = this.formatTime(duration);
            console.log('Updated total time:', this.formatTime(duration));
        }
    }

    updateProgress() {
        if (!this.audio.duration) return;
        
        const progress = (this.audio.currentTime / this.audio.duration) * 100;
        
        // Cập nhật progress bar
        if (this.progressFill) {
            this.progressFill.style.width = `${progress}%`;
        }
        if (this.progressHandle) {
            this.progressHandle.style.left = `${progress}%`;
        }
        
        // Cập nhật thời gian hiện tại
        if (this.currentTime) {
            this.currentTime.textContent = this.formatTime(this.audio.currentTime);
        }
        
        // Debug log mỗi 10 giây (giảm tần suất)
        if (Math.floor(this.audio.currentTime) % 10 === 0 && Math.floor(this.audio.currentTime) > 0) {
            console.log('Progress update:', {
                currentTime: this.formatTime(this.audio.currentTime),
                totalTime: this.formatTime(this.audio.duration),
                progress: progress.toFixed(1) + '%'
            });
        }
    }

    formatTime(seconds) {
        const mins = Math.floor(seconds / 60);
        const secs = Math.floor(seconds % 60);
        return `${mins}:${secs.toString().padStart(2, '0')}`;
    }

    seekTo(event) {
        if (!this.audio.duration) {
            return;
        }
        
        const rect = this.progressBar.getBoundingClientRect();
        const clickX = (event.clientX || event.pageX) - rect.left;
        const percent = Math.max(0, Math.min(1, clickX / rect.width));
        const newTime = percent * this.audio.duration;
        
        // Set new time
        this.audio.currentTime = newTime;
        
        // Force update UI immediately
        this.updateProgress();
        
        // Save state after seeking
        if (!this.isRestoringState) {
            this.savePlayerState();
        }
    }

    startSeeking(event) {
        if (!this.audio.duration) return;
        
        const isTouchEvent = event.type && event.type.startsWith('touch');
        
        const handleSeek = (e) => {
            if (!this.audio.duration) return;
            
            const clientX = isTouchEvent ? e.touches[0].clientX : e.clientX;
            const rect = this.progressBar.getBoundingClientRect();
            const dragX = clientX - rect.left;
            const percent = Math.max(0, Math.min(1, dragX / rect.width));
            const newTime = percent * this.audio.duration;
            
            this.audio.currentTime = newTime;
            this.updateProgress();
        };
        
        const handleEnd = () => {
            if (isTouchEvent) {
                document.removeEventListener('touchmove', handleSeek);
                document.removeEventListener('touchend', handleEnd);
            } else {
                document.removeEventListener('mousemove', handleSeek);
                document.removeEventListener('mouseup', handleEnd);
            }
            
            // Save state after seeking completes
            if (!this.isRestoringState) {
                this.savePlayerState();
            }
        };
        
        if (isTouchEvent) {
            document.addEventListener('touchmove', handleSeek, { passive: false });
            document.addEventListener('touchend', handleEnd);
        } else {
            document.addEventListener('mousemove', handleSeek);
            document.addEventListener('mouseup', handleEnd);
        }
    }
    
    // Method để test seek functionality
    testSeek(percent) {
        if (!this.audio.duration) {
            console.log('Cannot test seek: no duration');
            return;
        }
        
        const newTime = percent * this.audio.duration;
        console.log('Testing seek to', percent * 100 + '% =', this.formatTime(newTime));
        
        this.audio.currentTime = newTime;
        this.updateProgress();
        
        // Verify after a short delay
        setTimeout(() => {
            console.log('Seek result:', this.formatTime(this.audio.currentTime), '(expected:', this.formatTime(newTime), ')');
        }, 100);
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
        
        console.log('Shuffle mode changed to:', this.isShuffled);
    }

    toggleRepeat() {
        const modes = ['none', 'one', 'all'];
        const currentIndex = modes.indexOf(this.repeatMode);
        this.repeatMode = modes[(currentIndex + 1) % modes.length];
        
        // Cập nhật icon và styling
        this.updateRepeatButton();
        this.saveSettings();
        
        console.log('Repeat mode changed to:', this.repeatMode);
    }
    
    updateRepeatButton() {
        if (!this.repeatBtn) return;
        
        // Xóa tất cả classes active
        this.repeatBtn.classList.remove('active');
        
        // Thêm class active nếu không phải 'none'
        if (this.repeatMode !== 'none') {
            this.repeatBtn.classList.add('active');
        }
        
        // Cập nhật icon dựa trên mode
        let icon = 'bi-arrow-repeat';
        if (this.repeatMode === 'one') {
            icon = 'bi-arrow-repeat'; // Có thể thay bằng icon khác nếu muốn
        } else if (this.repeatMode === 'all') {
            icon = 'bi-arrow-repeat';
        }
        
        this.repeatBtn.innerHTML = `<i class="bi ${icon}"></i>`;
    }

    togglePlayer() {
        this.popup.classList.toggle('hidden');
    }

    startDragging(event) {
        // Không drag nếu click vào button
        if (event.target.closest('button')) {
            return;
        }
        
        this.isDragging = true;
        this.popup.classList.add('dragging');
        
        const rect = this.popup.getBoundingClientRect();
        
        // Lấy clientX/Y từ touch hoặc mouse event
        const clientX = event.touches ? event.touches[0].clientX : event.clientX;
        const clientY = event.touches ? event.touches[0].clientY : event.clientY;
        
        this.dragOffset.x = clientX - rect.left;
        this.dragOffset.y = clientY - rect.top;
        
        event.preventDefault();
    }

    drag(event) {
        if (!this.isDragging) return;
        
        event.preventDefault();
        
        // Lấy clientX/Y từ touch hoặc mouse event
        const clientX = event.touches ? event.touches[0].clientX : event.clientX;
        const clientY = event.touches ? event.touches[0].clientY : event.clientY;
        
        let x = clientX - this.dragOffset.x;
        let y = clientY - this.dragOffset.y;
        
        // Giới hạn trong viewport
        const rect = this.popup.getBoundingClientRect();
        const maxX = window.innerWidth - rect.width;
        const maxY = window.innerHeight - rect.height;
        
        x = Math.max(0, Math.min(x, maxX));
        y = Math.max(0, Math.min(y, maxY));
        
        this.popup.style.left = `${x}px`;
        this.popup.style.top = `${y}px`;
        this.popup.style.bottom = 'auto';
        this.popup.style.right = 'auto';
    }

    stopDragging() {
        if (this.isDragging) {
            this.isDragging = false;
            this.popup.classList.remove('dragging');
        }
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
                this.updateRepeatButton();
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
        // Không lưu nếu đang restore hoặc không có playlist
        if (this.isRestoringState || !this.currentPlaylist) {
            return;
        }
        
        const state = {
            playlistId: this.currentPlaylist.id,
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
            
            // Chỉ restore nếu state không quá cũ (trong vòng 2 giờ)
            const maxAge = 2 * 60 * 60 * 1000;
            if (Date.now() - state.timestamp > maxAge) {
                localStorage.removeItem('musicPlayerState');
                return false;
            }
            
            // Tìm playlist
            const playlist = this.playlists.find(p => p.id === state.playlistId);
            if (!playlist || !playlist.tracks || playlist.tracks.length === 0) {
                return false;
            }
            
            // Validate track index
            const trackIndex = Math.min(state.trackIndex || 0, playlist.tracks.length - 1);
            const track = playlist.tracks[trackIndex];
            if (!track) return false;
            
            console.log('Restoring player state:', {
                playlist: playlist.name,
                track: track.title,
                trackIndex: trackIndex,
                currentTime: state.currentTime,
                isPlaying: state.isPlaying
            });
            
            // Set flags
            this.isRestoringState = true;
            this.isLoadingTrack = true;
            this.hasAutoPlayed = true;
            
            // Restore playlist và track
            this.currentPlaylist = playlist;
            this.currentTrackIndex = trackIndex;
            this.playlistSelect.value = playlist.id;
            this.populateTrackList();
            
            // Update UI
            this.updateCurrentTrack();
            this.updateTrackListSelection();
            
            // Load audio với approach mới
            const fileUrl = `/media/music/playlist/${track.file_path}`;
            this.audio.src = fileUrl;
            
            // Sử dụng Promise để handle audio loading
            const waitForAudioReady = () => {
                return new Promise((resolve, reject) => {
                    let resolved = false;
                    
                    const cleanup = () => {
                        clearTimeout(timeout);
                        this.audio.removeEventListener('loadeddata', onReady);
                        this.audio.removeEventListener('error', onError);
                    };
                    
                    const onReady = () => {
                        if (resolved) return;
                        resolved = true;
                        cleanup();
                        resolve();
                    };
                    
                    const onError = (e) => {
                        if (resolved) return;
                        resolved = true;
                        cleanup();
                        reject(e);
                    };
                    
                    // Timeout sau 5 giây
                    const timeout = setTimeout(() => {
                        if (resolved) return;
                        resolved = true;
                        cleanup();
                        reject(new Error('Timeout waiting for audio'));
                    }, 5000);
                    
                    this.audio.addEventListener('loadeddata', onReady, { once: true });
                    this.audio.addEventListener('error', onError, { once: true });
                });
            };
            
            // Load audio
            this.audio.load();
            
            // Xử lý async
            waitForAudioReady()
                .then(() => {
                    // Audio đã sẵn sàng
                    console.log('Audio ready for restore');
                    
                    // Set thời gian phát
                    if (state.currentTime && state.currentTime > 0 && this.audio.duration) {
                        const targetTime = Math.min(state.currentTime, this.audio.duration - 1);
                        this.audio.currentTime = targetTime;
                        console.log('Restored position:', this.formatTime(targetTime));
                    }
                    
                    // Update UI
                    this.updateProgress();
                    this.updateDuration();
                    
                    // Resume playback nếu đang phát
                    if (state.isPlaying) {
                        this.userInteracted = true;
                        this.audio.play().catch(e => {
                            console.log('Autoplay prevented:', e.message);
                        });
                    }
                })
                .catch(error => {
                    console.error('Error restoring audio:', error);
                })
                .finally(() => {
                    // Reset flags sau 1 giây để đảm bảo mọi thứ ổn định
                    setTimeout(() => {
                        this.isRestoringState = false;
                        this.isLoadingTrack = false;
                        console.log('Restore completed');
                    }, 1000);
                });
            
            return true;
            
        } catch (error) {
            console.error('Error restoring player state:', error);
            this.isRestoringState = false;
            this.isLoadingTrack = false;
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
