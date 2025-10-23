// Music Player v1.2.3 - 2025-01-16
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
            shuffle: false,
            listening_lock: false
        };
        
        this.userInteracted = false; // Track user interaction for autoplay
        this.isRestoringState = false; // Flag để tránh lưu state khi đang restore
        this.isLoadingTrack = false; // Flag để tránh load track nhiều lần cùng lúc
        this.hasAutoPlayed = false; // Flag để track đã auto-play chưa
        this.restoreAttempted = false; // Flag để chỉ restore 1 lần duy nhất
        this.hasOpenedPlayer = false; // ✅ Flag để track lần đầu mở player
        
        // Drag and drop variables
        this.isDragging = false;
        this.dragOffset = { x: 0, y: 0 };
        this.isDraggingVolume = false; // Flag để track volume dragging
        this.dragAnimationFrame = null; // ✅ Throttle drag với requestAnimationFrame
        this.volumeDragAnimationFrame = null; // ✅ Throttle volume drag
        
        // ✅ Resize variables (desktop only)
        this.isResizing = false;
        this.resizeStartX = 0;
        this.resizeStartY = 0;
        this.resizeStartWidth = 0;
        this.resizeStartHeight = 0;
        this.resizeAnimationFrame = null;
        
        // Sleep timer variables
        this.sleepTimerActive = false;
        this.sleepTimerEndTime = null;
        this.sleepTimerInterval = null;
        
        // ✅ Mobile optimization variables
        this.preloadedTracks = new Map(); // Cache cho preloaded audio
        this.nextTrackPreloaded = false;
        this.previousTrackPreloaded = false;
        this.isMobile = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
        
        // ✅ Detect iOS specifically (iOS không cho web app control system volume)
        this.isIOS = /iPhone|iPad|iPod/i.test(navigator.userAgent) || 
                     (navigator.platform === 'MacIntel' && navigator.maxTouchPoints > 1); // iPad với iPadOS 13+
        
        // ✅ Flag để track đã show iOS volume message trong session này chưa
        this.hasShownIOSVolumeMessage = false;
        
        // ✅ Cache cho formatted times (tối ưu performance)
        this.formatTimeCache = new Map();
        this.lastProgressUpdate = 0; // Throttle progress updates
        
        // ✅ Debounce timers
        this.saveStateDebounceTimer = null;
        this.refreshPlaylistsDebounceTimer = null;
        
        // ✅ Play tracking variables
        this.currentTrackStartTime = null; // Timestamp khi bắt đầu nghe track hiện tại
        this.currentTrackListenDuration = 0; // Tổng số giây đã nghe track hiện tại (không bao gồm skip)
        this.playTrackingInterval = null; // Interval để update listen duration
        this.hasRecordedPlay = false; // Flag để tránh record trùng lần
        
        // ✅ OFFLINE MANAGER - For offline playback
        this.offlineManager = null; // Will be initialized after DOM is ready
        this.cachedTracks = new Set(); // Track which tracks are cached for offline
        this.updateIndicatorsDebounceTimer = null; // Debounce timer for indicator updates
        
        // ✅ Call async initialization (handles all setup in initializePlayer method)
        this.initializePlayer();
    }

    async initializePlayer() {
        try {
            console.log('🎵 Initializing Music Player...');
            
            // Initialize elements and bind events
            this.initializeElements();
            this.bindEvents();
            
            // Initialize volume display
            this.initializeVolumeDisplay();
            
            // Initialize resize handle (desktop only)
            this.initResizeHandle();
            
            // Initialize offline manager first
            await this.initializeOfflineManager();
            console.log('✅ Offline Manager initialized');
            
            // ✅ Load ALL initial data with batched API call
            const dataLoaded = await this.loadInitialData();
            
            if (!dataLoaded) {
                // Fallback to sequential loading if batched call fails
                console.warn('⚠️ Batched call failed, falling back to sequential loading');
                this.loadSettings();
                await this.loadPlaylists();
            }
            
            console.log('✅ Initial data loaded');
            
            // Load cached tracks and update indicators
            const loaded = await this.loadCachedTracksFromStorage();
            if (loaded) {
                this.updateTrackListOfflineIndicators();
                console.log('✅ Cached tracks loaded and verified');
            }
            
            // Initialize play count display
            this.playCountNumber = document.getElementById('play-count-number');
            
            // Initialize mobile optimizations
            this.initializeMobileOptimizations();
            
            // Handle iOS volume restrictions
            this.handleIOSVolumeRestrictions();
            
            // Track user activity
            this.lastUserActivity = Date.now();
            document.addEventListener('click', () => this.updateUserActivity());
            document.addEventListener('keydown', () => this.updateUserActivity());
            document.addEventListener('touchstart', () => this.updateUserActivity());
            
            // Save state before unload (immediate - không debounce)
            window.addEventListener('beforeunload', () => {
                if (!this.isRestoringState) {
                    this.savePlayerStateImmediate();
                }
            });
            
            // Handle mobile browser pause/resume - DISABLED (user wants continuous playback)
            document.addEventListener('visibilitychange', () => {
                if (document.hidden) {
                    // Page bị ẩn - KHÔNG pause audio trên mobile (user muốn tiếp tục phát)
                } else {
                    // Page hiện lại
                }
            });
            
            // Handle mobile app switching - DISABLED (user wants continuous playback)
            window.addEventListener('blur', () => {
                // App switched - keeping music playing
            });
            
            console.log('✅ Music Player fully initialized');
            
        } catch (error) {
            console.error('❌ Music Player initialization failed:', error);
            this.showMessage('Lỗi khởi tạo trình phát nhạc', 'error');
        }
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
        this.currentAlbumCover = document.getElementById('current-album-cover');
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
        this.lockBtn = document.getElementById('lock-player-btn');
        
        // Sleep timer elements
        this.sleepTimerBtn = document.getElementById('sleep-timer-btn');
        this.sleepTimerMenu = document.getElementById('sleep-timer-menu');
        this.sleepTimerStatus = document.getElementById('sleep-timer-status');
        this.timerRemaining = document.getElementById('timer-remaining');
        this.cancelTimerBtn = document.getElementById('cancel-timer-btn');
        
        // ✅ Keyboard shortcuts button
        this.keyboardShortcutsBtn = document.getElementById('keyboard-shortcuts-btn');
        this.playerTitle = document.getElementById('player-title') || document.querySelector('.player-title');
        
        // Check required elements
        const elementsStatus = {
            currentTime: !!this.currentTime,
            totalTime: !!this.totalTime,
            progressFill: !!this.progressFill,
            progressHandle: !!this.progressHandle,
            audio: !!this.audio
        };
        
        // Log missing elements only if there are issues
        const missingElements = Object.entries(elementsStatus).filter(([key, exists]) => !exists);
        if (missingElements.length > 0) {
            console.warn('Missing elements:', missingElements.map(([key]) => key));
        }
    }

    bindEvents() {
        // ✅ Null guards cho các elements bắt buộc
        if (!this.toggle || !this.closeBtn || !this.popup || !this.audio) {
            console.error('Missing required DOM elements for music player');
            return;
        }
        
        // Toggle events
        this.toggle.addEventListener('click', () => this.togglePlayer());
        this.closeBtn.addEventListener('click', () => this.togglePlayer());
        if (this.lockBtn) {
            this.lockBtn.addEventListener('click', () => this.toggleListeningLock());
        }
        
        // Playlist selection
        this.playlistSelect.addEventListener('change', (e) => this.selectPlaylist(e.target.value));
        
        // ✅ Event delegation cho track items - chỉ cần 1 listener cho tất cả tracks
        if (this.trackList) {
            this.trackList.addEventListener('click', (e) => {
                const trackItem = e.target.closest('.track-item');
                if (trackItem && trackItem.dataset.index !== undefined) {
                    const index = parseInt(trackItem.dataset.index);
                    this.playTrack(index);
                }
            });
        }
        
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
                this.seekToPosition(e);
            });
            // ✅ Improved touch support for mobile - prevent default scrolling
            this.progressBar.addEventListener('touchstart', (e) => {
                e.preventDefault();
                this.seekToPosition(e);
            }, { passive: false });
        }
        if (this.progressHandle) {
            // Mouse drag
            this.progressHandle.addEventListener('mousedown', (e) => {
                e.stopPropagation(); // Prevent click event on bar
                this.startSeeking(e);
            });
            // ✅ Improved touch drag for mobile
            this.progressHandle.addEventListener('touchstart', (e) => {
                e.stopPropagation();
                e.preventDefault();
                this.startSeeking(e);
            }, { passive: false });
        }
        
        // ========================================
        // ✅ VOLUME CONTROL - VIẾT LẠI TỪ ĐẦU
        // ========================================
        const volumeBar = this.volumeFill?.parentElement;
        if (volumeBar) {
            // Desktop: Click anywhere on volume bar to set volume
            volumeBar.addEventListener('click', (e) => {
                this.handleVolumeClick(e);
            });
            
            // Mobile: Touch on volume bar
            volumeBar.addEventListener('touchstart', (e) => {
                this.handleVolumeTouchStart(e, volumeBar);
            }, { passive: false });
        }
        
        if (this.volumeHandle) {
            // Desktop: Drag volume handle
            this.volumeHandle.addEventListener('mousedown', (e) => {
                e.stopPropagation();
                this.startVolumeDrag(e, false);
            });
            
            // Mobile: Drag volume handle
            this.volumeHandle.addEventListener('touchstart', (e) => {
                e.stopPropagation();
                e.preventDefault();
                this.startVolumeDrag(e, true);
            }, { passive: false });
        }
        
        // Audio events
        this.audio.addEventListener('loadedmetadata', () => {
            this.updateDuration();
        });
        this.audio.addEventListener('timeupdate', () => this.updateProgress());
        this.audio.addEventListener('ended', () => this.onTrackEnd());
        this.audio.addEventListener('play', () => this.onPlay());
        this.audio.addEventListener('pause', () => this.onPause());
        this.audio.addEventListener('error', (e) => {
            // Essential error logging - chỉ hiển thị thông tin quan trọng
            console.group('🚨 Audio Error');
            console.error('Error:', e.type);
            console.error('Source:', this.audio.src);
            console.error('Track:', this.currentTrack?.title || 'Unknown');
            console.error('Playlist:', this.currentPlaylist?.name || 'Unknown');
            console.error('File Path:', this.currentTrack?.file_url || 'Unknown');
            console.error('Current Track Index:', this.currentTrackIndex);
            console.error('Total Tracks:', this.currentPlaylist?.tracks?.length || 0);
            console.groupEnd();
            
            // Set loading state to false
            this.isLoadingTrack = false;
            
            // ✅ Retry mechanism với URL encoding fix
            this.retryAudioLoad();
        });
        
        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => this.handleKeyboard(e));
        // Hidden trigger: click/Enter on title to open shortcuts
        if (this.playerTitle) {
            this.playerTitle.addEventListener('click', (e) => {
                e.stopPropagation();
                this.showKeyboardShortcuts();
            });
            // Mobile: touchstart để mở nhanh
            this.playerTitle.addEventListener('touchstart', (e) => {
                e.stopPropagation();
                e.preventDefault();
                this.showKeyboardShortcuts();
            }, { passive: false });
            this.playerTitle.addEventListener('keydown', (e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    this.showKeyboardShortcuts();
                }
            });
        }
        
        // Drag and drop for player header (Desktop)
        if (this.playerHeader) {
            this.playerHeader.addEventListener('mousedown', (e) => this.startDragging(e));
            // Touch events for mobile
            this.playerHeader.addEventListener('touchstart', (e) => this.startDragging(e), { passive: false });
        }
        // ✅ Throttled drag events với requestAnimationFrame
        document.addEventListener('mousemove', (e) => this.throttledDrag(e));
        document.addEventListener('mouseup', () => this.stopDragging());
        // Touch events for mobile
        document.addEventListener('touchmove', (e) => this.throttledDrag(e), { passive: false });
        document.addEventListener('touchend', () => this.stopDragging());
        document.addEventListener('touchcancel', () => this.stopDragging());
        
        // Prevent popup from closing when clicking inside
        if (this.popup) {
            this.popup.addEventListener('click', (e) => {
                e.stopPropagation();
                this.userInteracted = true;
            });
        }
        
        // ✅ Hợp nhất global click listener để tránh conflict
        document.addEventListener('click', (e) => {
            this.userInteracted = true;
            
            // Close player nếu click ngoài
            if (!this.popup.classList.contains('hidden')) {
                if (!this.popup.contains(e.target) && !this.toggle.contains(e.target)) {
                    if (!(this.settings && this.settings.listening_lock)) {
                        this.togglePlayer();
                    }
                }
            }
            
            // Close sleep timer menu nếu click ngoài
            if (this.sleepTimerMenu && !this.sleepTimerMenu.classList.contains('hidden')) {
                if (!this.sleepTimerMenu.contains(e.target) && !this.sleepTimerBtn.contains(e.target)) {
                    this.sleepTimerMenu.classList.add('hidden');
                }
            }
        });
        
        // Track user interaction for play permission
        document.addEventListener('keydown', () => {
            this.userInteracted = true;
        }, { once: true });
        
        // Sleep timer events
        if (this.sleepTimerBtn) {
            this.sleepTimerBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                this.showSleepTimerModal();
            });
        }
        
        // Sleep timer options - removed (now using modal)
        
        // Cancel timer button
        if (this.cancelTimerBtn) {
            this.cancelTimerBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                this.cancelSleepTimer();
            });
        }
        
        // ✅ Keyboard shortcuts button
        if (this.keyboardShortcutsBtn) {
            this.keyboardShortcutsBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                this.showKeyboardShortcuts();
            });
        }
        
        // Tab switching
        this.initTabSystem();
        
        // Playlist type toggle
        this.initPlaylistTypeToggle();
    }

    async toggleListeningLock() {
        const newLock = !(this.settings && this.settings.listening_lock);
        this.settings.listening_lock = newLock;
        // Toggle global body class to disable header/nav interactions when locked
        document.body.classList.toggle('listening-locked', newLock);
        document.documentElement.classList.toggle('listening-locked', newLock);
        if (this.lockBtn) {
            this.lockBtn.classList.toggle('active', newLock);
            this.lockBtn.title = newLock ? 'Đang khóa nghe nhạc' : 'Khóa nghe nhạc';
            this.lockBtn.innerHTML = newLock ? '<i class="bi bi-lock-fill"></i>' : '<i class="bi bi-lock"></i>';
        }
        if (newLock && this.popup && this.popup.classList.contains('hidden')) {
            this.popup.classList.remove('hidden');
        }
        try {
            await fetch('/music/user/settings/update/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                credentials: 'same-origin',
                body: JSON.stringify({ listening_lock: newLock })
            });
        } catch (e) {
            console.error('Failed to persist listening lock', e);
        }
    }
    
    initPlaylistTypeToggle() {
        const toggleButtons = document.querySelectorAll('.playlist-type-btn');
        const adminGrid = document.getElementById('playlist-grid');
        const userGrid = document.getElementById('user-playlist-grid');
        const globalGrid = document.getElementById('global-playlist-grid');
        
        toggleButtons.forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                const type = btn.getAttribute('data-type');
                
                // Update active state
                toggleButtons.forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                
                // Toggle grids
                if (type === 'admin') {
                    adminGrid.classList.remove('hidden');
                    userGrid.classList.add('hidden');
                    if (globalGrid) globalGrid.classList.add('hidden');
                    // Force refresh admin playlists khi click vào Admin Playlists
                    this.refreshPlaylists().then(() => {
                        // Restore active state for admin playlists
                        this.restorePlaylistActiveState();
                    });
                } else if (type === 'personal') {
                    adminGrid.classList.add('hidden');
                    userGrid.classList.remove('hidden');
                    if (globalGrid) globalGrid.classList.add('hidden');
                    // Load user playlists
                    this.loadUserPlaylistsInMainPlayer().then(() => {
                        // Restore active state after loading
                        this.restorePlaylistActiveState();
                    });
                } else if (type === 'global') {
                    adminGrid.classList.add('hidden');
                    userGrid.classList.add('hidden');
                    if (globalGrid) globalGrid.classList.remove('hidden');
                    // Load global playlists
                    this.loadGlobalPlaylists();
                }
            });
        });
        
        // Initialize global search
        this.initGlobalSearch();
    }
    
    restorePlaylistActiveState() {
        if (!this.currentPlaylist) return;
        
        // Check if it's a user playlist or admin playlist
        const isUserPlaylist = typeof this.currentPlaylist.id === 'string' && this.currentPlaylist.id.startsWith('user-playlist-');
        
        if (isUserPlaylist) {
            // Extract the actual playlist ID from "user-playlist-3" format
            const playlistIdMatch = this.currentPlaylist.id.match(/user-playlist-(\d+)/);
            if (playlistIdMatch) {
                const playlistId = playlistIdMatch[1];
                const userGrid = document.getElementById('user-playlist-grid');
                if (userGrid) {
                    userGrid.querySelectorAll('.playlist-card').forEach(card => {
                        if (card.dataset.playlistId === `user-${playlistId}`) {
                            card.classList.add('active');
                        } else {
                            card.classList.remove('active');
                        }
                    });
                }
            }
        } else {
            // Admin playlist
            const playlistGrid = document.getElementById('playlist-grid');
            if (playlistGrid) {
                playlistGrid.querySelectorAll('.playlist-card').forEach(card => {
                    if (parseInt(card.dataset.playlistId) === this.currentPlaylist.id) {
                        card.classList.add('active');
                    } else {
                        card.classList.remove('active');
                    }
                });
            }
        }
    }
    
    // ✅ Initialize Resize Handle (Desktop Only)
    initResizeHandle() {
        const resizeHandle = document.getElementById('player-resize-handle');
        if (!resizeHandle) return;
        
        // Skip on mobile
        if (this.isMobile) {
            resizeHandle.style.display = 'none';
            return;
        }
        
        // ✅ Restore saved size from localStorage
        this.restorePlayerSize();
        
        resizeHandle.addEventListener('mousedown', (e) => {
            e.preventDefault();
            e.stopPropagation();
            
            this.isResizing = true;
            this.resizeStartX = e.clientX;
            this.resizeStartY = e.clientY;
            
            const rect = this.fullPlayer.getBoundingClientRect();
            this.resizeStartWidth = rect.width;
            this.resizeStartHeight = rect.height;
            
            this.popup.classList.add('resizing');
            document.body.style.cursor = 'nwse-resize';
            document.body.style.userSelect = 'none';
        });
        
        document.addEventListener('mousemove', (e) => {
            if (!this.isResizing) return;
            
            // ✅ Throttle with requestAnimationFrame
            if (this.resizeAnimationFrame) return;
            
            this.resizeAnimationFrame = requestAnimationFrame(() => {
                const deltaX = e.clientX - this.resizeStartX;
                const deltaY = e.clientY - this.resizeStartY;
                
                const newWidth = Math.max(350, Math.min(800, this.resizeStartWidth + deltaX));
                const newHeight = Math.max(500, Math.min(window.innerHeight * 0.9, this.resizeStartHeight + deltaY));
                
                this.fullPlayer.style.width = newWidth + 'px';
                this.fullPlayer.style.height = newHeight + 'px';
                
                this.resizeAnimationFrame = null;
            });
        });
        
        document.addEventListener('mouseup', () => {
            if (!this.isResizing) return;
            
            this.isResizing = false;
            this.popup.classList.remove('resizing');
            document.body.style.cursor = '';
            document.body.style.userSelect = '';
            
            // ✅ Save size to localStorage
            this.savePlayerSize();
            
            // Clean up animation frame
            if (this.resizeAnimationFrame) {
                cancelAnimationFrame(this.resizeAnimationFrame);
                this.resizeAnimationFrame = null;
            }
        });
    }
    
    // ✅ Save player size to localStorage
    savePlayerSize() {
        if (!this.fullPlayer) return;
        
        const rect = this.fullPlayer.getBoundingClientRect();
        const size = {
            width: rect.width,
            height: rect.height
        };
        
        try {
            localStorage.setItem('musicPlayerSize', JSON.stringify(size));
        } catch (error) {
            console.error('Error saving player size:', error);
        }
    }
    
    // ✅ Restore player size from localStorage
    restorePlayerSize() {
        if (!this.fullPlayer) return;
        
        try {
            const sizeStr = localStorage.getItem('musicPlayerSize');
            if (!sizeStr) return;
            
            const size = JSON.parse(sizeStr);
            
            // Validate size
            if (size.width >= 350 && size.width <= 800) {
                this.fullPlayer.style.width = size.width + 'px';
            }
            
            if (size.height >= 500 && size.height <= window.innerHeight * 0.9) {
                this.fullPlayer.style.height = size.height + 'px';
            }
        } catch (error) {
            console.error('Error restoring player size:', error);
        }
    }
    
    async loadUserPlaylistsInMainPlayer() {
        const userGrid = document.getElementById('user-playlist-grid');
        if (!userGrid) return;
        
        try {
            // Add cache-busting parameter để luôn lấy data mới nhất
            const response = await fetch(`/music/user/playlists/?t=${Date.now()}`);
            
            if (!response.ok) {
                if (response.status === 302 || response.status === 401 || response.status === 403) {
                    userGrid.innerHTML = `
                        <div class="empty-state">
                            <i class="bi bi-lock-fill"></i>
                            <p style="margin-bottom: 12px;">Vui lòng đăng nhập để sử dụng tính năng này!</p>
                            <a href="/accounts/login/?next=${window.location.pathname}" style="color: #f093fb; text-decoration: underline;">
                                Đăng nhập ngay
                            </a>
                        </div>
                    `;
                    return;
                }
                throw new Error(`HTTP ${response.status}`);
            }
            
            const data = await response.json();
            
            if (data.success) {
                if (data.playlists.length === 0) {
                    userGrid.innerHTML = `
                        <div class="empty-state">
                            <i class="bi bi-music-note"></i>
                            <p>Chưa có playlist cá nhân. Vào Cài đặt để tạo!</p>
                        </div>
                    `;
                } else {
                    // ✅ Escape HTML để tránh XSS
                    userGrid.innerHTML = data.playlists.map(playlist => {
                        const escapedName = this.escapeHtml(playlist.name);
                        const totalDuration = playlist.total_duration ? Math.floor(playlist.total_duration / 60) : 0;
                        return `
                            <div class="playlist-card" data-playlist-id="user-${playlist.id}" onclick="musicPlayer.loadUserPlaylist(${playlist.id})">
                                <div class="playlist-card-icon">
                                    <i class="bi bi-vinyl-fill"></i>
                                </div>
                                <div class="playlist-card-name">${escapedName}</div>
                                <div class="playlist-card-count">${playlist.tracks_count} bài${totalDuration > 0 ? ` • ${totalDuration} phút` : ''}</div>
                            </div>
                        `;
                    }).join('');
                }
            }
        } catch (error) {
            console.error('Error loading user playlists in main player:', error);
            if (error.message.includes('Unexpected token')) {
                userGrid.innerHTML = `
                    <div class="empty-state">
                        <i class="bi bi-lock-fill"></i>
                        <p style="margin-bottom: 12px;">Vui lòng đăng nhập để sử dụng tính năng này!</p>
                        <a href="/accounts/login/?next=${window.location.pathname}" style="color: #f093fb; text-decoration: underline;">
                            Đăng nhập ngay
                        </a>
                    </div>
                `;
            } else {
                userGrid.innerHTML = `
                    <div class="empty-state">
                        <i class="bi bi-exclamation-circle"></i>
                        <p>Lỗi khi tải danh sách playlist!</p>
                    </div>
                `;
            }
        }
    }
    
    async loadUserPlaylist(playlistId) {
        try {
            const response = await fetch(`/music/user/playlists/${playlistId}/tracks/`);
            
            if (!response.ok) {
                if (response.status === 302 || response.status === 401 || response.status === 403) {
                    this.showMessage('⚠️ Vui lòng đăng nhập để phát playlist cá nhân!', 'info');
                    setTimeout(() => {
                        window.location.href = '/accounts/login/?next=' + window.location.pathname;
                    }, 1500);
                    return;
                }
                throw new Error(`HTTP ${response.status}`);
            }
            
            const data = await response.json();
            
            if (data.success && data.tracks.length > 0) {
                // Convert to player format
                this.currentPlaylist = {
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
                
                this.currentTrackIndex = 0;
                this.populateTrackList();
                
                // Update active state for user playlist cards
                const userPlaylistGrid = document.getElementById('user-playlist-grid');
                if (userPlaylistGrid) {
                    userPlaylistGrid.querySelectorAll('.playlist-card').forEach(card => {
                        if (card.dataset.playlistId === `user-${playlistId}`) {
                            card.classList.add('active');
                        } else {
                            card.classList.remove('active');
                        }
                    });
                }
                
                // Remove active from admin playlists
                const playlistGrid = document.getElementById('playlist-grid');
                if (playlistGrid) {
                    playlistGrid.querySelectorAll('.playlist-card').forEach(card => {
                        card.classList.remove('active');
                    });
                }
                
                // Switch to tracks tab FIRST before playing
                const popup = document.getElementById('music-player-popup');
                if (popup) {
                    const tracksTab = popup.querySelector('[data-tab="tracks"]');
                    if (tracksTab && !tracksTab.classList.contains('active')) {
                        tracksTab.click();
                    }
                }
                
                // Then auto-play
                this.userInteracted = true;
                setTimeout(() => {
                    this.playTrack(0);
                }, 100);
                
                // Loaded user playlist
            } else {
                this.showMessage('Playlist chưa có bài hát!', 'info');
            }
        } catch (error) {
            console.error('Error loading user playlist:', error);
            if (error.message.includes('Unexpected token')) {
                this.showMessage('⚠️ Vui lòng đăng nhập để phát playlist cá nhân!', 'info');
            } else {
                this.showMessage('Lỗi khi load playlist!', 'error');
            }
        }
    }
    
    async loadGlobalPlaylists(searchQuery = '') {
        const globalGrid = document.getElementById('global-playlist-grid');
        if (!globalGrid) {
            console.error('❌ Global grid not found!');
            return;
        }
        
        console.log('🔍 Loading all playlists...', searchQuery ? `search: "${searchQuery}"` : 'all');
        
        // Get container
        const playlistsWrapper = document.getElementById('all-playlists-wrapper');
        const clearBtn = document.getElementById('clear-search-btn');
        
        if (!playlistsWrapper) {
            console.error('❌ Playlists wrapper not found!');
            return;
        }
        
        try {
            // Show loading
            playlistsWrapper.innerHTML = `
                <div class="empty-state">
                    <i class="bi bi-hourglass-split"></i>
                    <p>Đang tải...</p>
                </div>
            `;
            
            // Load admin playlists
            const adminResponse = await fetch('/music/api/');
            const adminData = await adminResponse.json();
            
            // Load user public playlists
            const userURL = searchQuery 
                ? `/music/global/playlists/?search=${encodeURIComponent(searchQuery)}`
                : '/music/global/playlists/';
            const userResponse = await fetch(userURL);
            const userData = await userResponse.json();
            
            console.log('📊 Admin Playlists:', adminData);
            console.log('📊 User Playlists:', userData);
            
            // Show/hide clear button
            if (clearBtn) {
                if (searchQuery) {
                    clearBtn.classList.remove('hidden');
                } else {
                    clearBtn.classList.add('hidden');
                }
            }
            
            // Merge and render all playlists
            let allPlaylists = [];
            
            // Add admin playlists
            if (adminData.success && adminData.playlists.length > 0) {
                let filteredAdminPlaylists = adminData.playlists;
                
                // Filter by search query if provided
                if (searchQuery) {
                    const query = searchQuery.toLowerCase();
                    filteredAdminPlaylists = adminData.playlists.filter(p => 
                        p.name.toLowerCase().includes(query)
                    );
                }
                
                filteredAdminPlaylists.forEach(playlist => {
                    const escapedName = this.escapeHtml(playlist.name);
                    const coverImage = playlist.cover_image || '';
                    const totalDuration = playlist.tracks ? Math.floor(playlist.tracks.reduce((sum, t) => sum + (t.duration || 0), 0) / 60) : 0;
                    
                    allPlaylists.push(`
                        <div class="playlist-card" data-playlist-id="${playlist.id}" onclick="musicPlayer.loadPlaylist(${playlist.id})">
                            ${coverImage ? `
                                <div class="playlist-card-cover" style="background-image: url('${coverImage}')"></div>
                            ` : `
                                <div class="playlist-card-icon">
                                    <i class="bi bi-music-note-list"></i>
                                </div>
                            `}
                            <div class="playlist-card-name" title="${escapedName}">${escapedName}</div>
                            <div class="playlist-card-count">${playlist.tracks_count || playlist.tracks?.length || 0} bài${totalDuration > 0 ? ` • ${totalDuration} phút` : ''}</div>
                        </div>
                    `);
                });
            }
            
            // Add user public playlists
            if (userData.success && userData.playlists.length > 0) {
                console.log(`✅ Found ${userData.playlists.length} user playlists`);
                userData.playlists.forEach(playlist => {
                    const escapedName = this.escapeHtml(playlist.name);
                    const escapedOwner = this.escapeHtml(playlist.owner.full_name);
                    const coverImage = playlist.cover_image || '';
                    const totalDuration = playlist.total_duration ? Math.floor(playlist.total_duration / 60) : 0;
                    
                    allPlaylists.push(`
                        <div class="playlist-card" data-playlist-id="global-${playlist.id}" onclick="musicPlayer.loadGlobalPlaylist(${playlist.id})">
                            ${coverImage ? `
                                <div class="playlist-card-cover" style="background-image: url('${coverImage}')"></div>
                            ` : `
                                <div class="playlist-card-icon">
                                    <i class="bi bi-music-note-list"></i>
                                </div>
                            `}
                            <div class="playlist-card-name" title="${escapedName}">${escapedName}</div>
                            <div class="playlist-card-count">${playlist.tracks_count} bài${totalDuration > 0 ? ` • ${totalDuration} phút` : ''}</div>
                            <div class="playlist-card-owner">
                                <i class="bi bi-person-circle"></i>
                                <span class="playlist-card-owner-name" title="${escapedOwner}">${escapedOwner}</span>
                            </div>
                        </div>
                    `);
                });
            }
            
            // Render all playlists or show empty state
            if (allPlaylists.length > 0) {
                playlistsWrapper.innerHTML = allPlaylists.join('');
            } else {
                const emptyMessage = searchQuery 
                    ? `Không tìm thấy playlist nào cho "${this.escapeHtml(searchQuery)}"`
                    : 'Chưa có playlist nào!';
                playlistsWrapper.innerHTML = `
                    <div class="empty-state">
                        <i class="bi bi-search"></i>
                        <p>${emptyMessage}</p>
                    </div>
                `;
            }
            
        } catch (error) {
            console.error('Error loading playlists:', error);
            playlistsWrapper.innerHTML = `
                <div class="empty-state">
                    <i class="bi bi-exclamation-circle"></i>
                    <p>Lỗi khi tải danh sách playlist!</p>
                </div>
            `;
        }
    }
    
    // ✅ Wrapper function để tự động load admin hoặc global playlist
    async loadPlaylist(playlistId) {
        // Admin playlists không có prefix, gọi loadGlobalPlaylist
        return await this.loadGlobalPlaylist(playlistId);
    }
    
    async loadGlobalPlaylist(playlistId) {
        try {
            const response = await fetch(`/music/global/playlists/${playlistId}/`);
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }
            
            const data = await response.json();
            
            if (data.success && data.tracks.length > 0) {
                // Convert to player format
                this.currentPlaylist = {
                    id: 'global-playlist-' + data.playlist.id,
                    name: data.playlist.name + ' (by ' + data.playlist.owner.full_name + ')',
                    tracks: data.tracks.map(track => ({
                        id: track.id,
                        title: track.title,
                        artist: track.artist || 'Unknown Artist',
                        album: track.album || '',
                        album_cover: track.album_cover || null,
                        file_url: track.file_url,
                        duration: track.duration,
                        play_count: track.play_count || 0
                    }))
                };
                
                this.currentTrackIndex = 0;
                this.populateTrackList();
                
                // Update active state for global playlist cards
                const playlistsWrapper = document.getElementById('all-playlists-wrapper');
                if (playlistsWrapper) {
                    playlistsWrapper.querySelectorAll('.playlist-card').forEach(card => {
                        if (card.dataset.playlistId === `global-${playlistId}` || card.dataset.playlistId === String(playlistId)) {
                            card.classList.add('active');
                        } else {
                            card.classList.remove('active');
                        }
                    });
                }
                
                // Remove active from user playlists
                const userGrid = document.getElementById('user-playlist-grid');
                if (userGrid) {
                    userGrid.querySelectorAll('.playlist-card').forEach(card => {
                        card.classList.remove('active');
                    });
                }
                
                // Remove active from admin playlists tab
                const playlistGrid = document.getElementById('playlist-grid');
                if (playlistGrid) {
                    playlistGrid.querySelectorAll('.playlist-card').forEach(card => {
                        if (card.dataset.playlistId === String(playlistId)) {
                            card.classList.add('active');
                        } else {
                            card.classList.remove('active');
                        }
                    });
                }
                
                // Switch to tracks tab FIRST before playing
                const popup = document.getElementById('music-player-popup');
                if (popup) {
                    const tracksTab = popup.querySelector('[data-tab="tracks"]');
                    if (tracksTab && !tracksTab.classList.contains('active')) {
                        tracksTab.click();
                    }
                }
                
                // Then auto-play
                this.userInteracted = true;
                setTimeout(() => {
                    this.playTrack(0);
                }, 100);
                
                this.showMessage(`🎵 Đang phát: ${data.playlist.name}`, 'success');
            } else {
                this.showMessage('Playlist chưa có bài hát!', 'info');
            }
        } catch (error) {
            console.error('Error loading global playlist:', error);
            this.showMessage('Lỗi khi load playlist!', 'error');
        }
    }
    
    initGlobalSearch() {
        const searchInput = document.getElementById('global-search-input');
        const clearBtn = document.getElementById('clear-search-btn');
        
        if (!searchInput) return;
        
        let searchTimeout;
        searchInput.addEventListener('input', (e) => {
            clearTimeout(searchTimeout);
            const query = e.target.value.trim();
            
            // Debounce search by 500ms
            searchTimeout = setTimeout(() => {
                this.loadGlobalPlaylists(query);
            }, 500);
        });
        
        // Clear search button
        if (clearBtn) {
            clearBtn.addEventListener('click', () => {
                searchInput.value = '';
                searchInput.focus();
                this.loadGlobalPlaylists('');
            });
        }
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
        
        // Tab system initialized
        
        tabHeaders.forEach(header => {
            header.addEventListener('click', (e) => {
                e.preventDefault();
                e.stopPropagation();
                
                const tabName = header.getAttribute('data-tab');
                
                // Remove active class from all headers and contents
                tabHeaders.forEach(h => h.classList.remove('active'));
                tabContents.forEach(c => c.classList.remove('active'));
                
                // Add active class to clicked header and corresponding content
                header.classList.add('active');
                const targetContent = popup.querySelector(`#tab-${tabName}`);
                if (targetContent) {
                    targetContent.classList.add('active');
                    
                    // Auto-load user playlists khi switch sang tab Playlists (default personal first)
                    if (tabName === 'playlists') {
                        this.loadUserPlaylistsInMainPlayer();
                    }
                }
            });
        });
    }

    async loadPlaylists() {
        try {
            // ✅ Use optimized endpoint with prefetch_related for better performance
            const response = await fetch(`/music/api/optimized/?t=${Date.now()}`, {
                cache: 'no-cache',
                headers: {
                    'Cache-Control': 'no-cache, no-store, must-revalidate',
                    'Pragma': 'no-cache',
                    'Expires': '0'
                }
            });
            const data = await response.json();
            
            if (data.success) {
                this.playlists = data.playlists;
                this.populatePlaylistSelect();
                
                // ✅ Thử restore state trước (chỉ 1 lần) - now async
                if (!this.restoreAttempted) {
                    this.restoreAttempted = true;
                    console.log('🔄 Restoring player state...');
                    
                    // Use async/await since restorePlayerState is now async
                    this.restorePlayerState().then(restored => {
                        if (!restored) {
                            console.log('ℹ️ No saved state found or restore failed');
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
                    }).catch(error => {
                        console.error('❌ Error during restore:', error);
                        // Fallback to default playlist on error
                        if (this.playlists.length > 0) {
                            this.selectPlaylist(this.playlists[0].id);
                        }
                    });
                }
            }
        } catch (error) {
            console.error('Error loading playlists:', error);
        }
    }

    async refreshPlaylists() {
        // ✅ Force refresh playlists from server với cache-busting mạnh
        try {
            // Force refreshing playlists
            
            // ✅ Thêm random parameter để đảm bảo không cache
            const timestamp = Date.now();
            const random = Math.random().toString(36).substring(7);
            
            // ✅ Use optimized endpoint with prefetch_related for better performance
            const response = await fetch(`/music/api/optimized/?t=${timestamp}&r=${random}&force=1`, {
                method: 'GET',
                cache: 'no-store', // ✅ Force no cache
                headers: {
                    'Cache-Control': 'no-cache, no-store, must-revalidate, max-age=0',
                    'Pragma': 'no-cache',
                    'Expires': '0',
                    'If-Modified-Since': '0' // ✅ Force fresh data
                }
            });
            
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
                        
                        // ✅ Update cached indicators after refresh
                        setTimeout(() => {
                            this.updateTrackListOfflineIndicators();
                        }, 300);
                    }
                }
                
                
            }
        } catch (error) {
            console.error('Error refreshing playlists:', error);
        }
    }

    async loadInitialData() {
        try {
            console.log('📡 Loading initial data (batched)...');
            
            const response = await fetch('/music/api/initial-data/', {
                cache: 'no-store',
                credentials: 'same-origin'
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }
            
            const data = await response.json();
            
            if (!data.success) {
                throw new Error(data.error || 'Failed to load data');
            }
            
            // ✅ Parse playlists
            this.playlists = data.playlists || [];
            this.populatePlaylistSelect();
            
            // ✅ Parse settings and apply
            if (data.settings) {
                this.settings = data.settings;
                this.volume = this.settings.volume;
                this.repeatMode = this.settings.repeat_mode;
                this.isShuffled = this.settings.shuffle;
                
                this.audio.volume = this.volume;
                this.updateVolumeDisplay();
                this.updateRepeatButton();
                this.shuffleBtn.classList.toggle('active', this.isShuffled);
                
                // ✅ Apply listening lock and low power mode if enabled
                const locked = !!this.settings.listening_lock;
                const lowPower = !!this.settings.low_power_mode;
                
                if (locked || lowPower) {
                    document.body.classList.toggle('listening-locked', locked);
                    document.documentElement.classList.toggle('listening-locked', locked);
                    document.body.classList.toggle('low-power', lowPower);
                    
                    // If locked, ensure player is open
                    if (locked && this.popup && this.popup.classList.contains('hidden')) {
                        this.popup.classList.remove('hidden');
                    }
                    
                    // Update lock button icon
                    if (this.lockBtn) {
                        this.lockBtn.classList.toggle('active', locked);
                        this.lockBtn.innerHTML = locked ? '<i class="bi bi-lock-fill"></i>' : '<i class="bi bi-lock"></i>';
                        this.lockBtn.title = locked ? 'Đang khóa nghe nhạc' : 'Khóa nghe nhạc';
                    }
                }
            }
            
            // ✅ Parse user tracks and playlists (if authenticated)
            this.userTracks = data.user_tracks || [];
            this.userPlaylists = data.user_playlists || [];
            
            console.log('✅ Initial data loaded:', {
                playlists: this.playlists.length,
                tracks: this.userTracks.length,
                playlists_user: this.userPlaylists.length
            });
            
            // ✅ Try restore state (chỉ 1 lần duy nhất)
            if (!this.restoreAttempted) {
                this.restoreAttempted = true;
                console.log('🔄 Restoring player state...');
                
                // Use async/await since restorePlayerState is now async
                this.restorePlayerState().then(restored => {
                    if (!restored) {
                        console.log('ℹ️ No saved state found or restore failed');
                        // ✅ If no state to restore, auto-select first playlist
                        console.log('🔄 Fallback: Selecting first playlist');
                        if (this.playlists.length > 0 && this.settings.default_playlist_id) {
                            const defaultPlaylist = this.playlists.find(p => p.id === this.settings.default_playlist_id);
                            if (defaultPlaylist) {
                                this.selectPlaylist(defaultPlaylist.id);
                            }
                        } else if (this.playlists.length > 0) {
                            this.selectPlaylist(this.playlists[0].id);
                        }
                    }
                }).catch(error => {
                    console.error('❌ Error during restore:', error);
                    // Fallback to default playlist on error
                    console.log('🔄 Fallback: Selecting first playlist');
                    if (this.playlists.length > 0) {
                        this.selectPlaylist(this.playlists[0].id);
                    }
                });
            }
            
            return true;
            
        } catch (error) {
            console.error('❌ Failed to load initial data:', error);
            return false;
        }
    }

    // ❌ REMOVED: checkForUpdates() - không cần auto-polling
    // Nếu cần check updates, user có thể:
    // 1. Đóng/mở lại player (auto refresh)
    // 2. Switch tab Playlists (auto refresh)
    // 3. Manual refresh button (có thể thêm sau)

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
        
        // ✅ Clear existing content first to prevent duplicates
        playlistGrid.innerHTML = '';
        
        if (this.playlists.length === 0) {
            playlistGrid.innerHTML = `
                <div class="empty-state">
                    <i class="bi bi-collection-play"></i>
                    <p>Chưa có playlist nào</p>
                </div>
            `;
            return;
        }
        
        // ✅ Render each playlist card once
        this.playlists.forEach(playlist => {
            const card = document.createElement('div');
            card.className = 'playlist-card';
            if (this.currentPlaylist && this.currentPlaylist.id === playlist.id) {
                card.classList.add('active');
            }
            card.dataset.playlistId = playlist.id;
            
            // ✅ Escape HTML để tránh XSS
            const escapedName = this.escapeHtml(playlist.name);
            const coverImage = playlist.cover_image || '/static/music_player/images/album-art.png';
            const totalDuration = playlist.tracks ? Math.floor(playlist.tracks.reduce((sum, t) => sum + (t.duration || 0), 0) / 60) : 0;
            card.innerHTML = `
                <div class="playlist-card-cover" style="background-image: url('${coverImage}');"></div>
                <div class="playlist-card-name" title="${escapedName}">${escapedName}</div>
                <div class="playlist-card-count">${playlist.tracks_count || playlist.tracks?.length || 0} bài${totalDuration > 0 ? ` • ${totalDuration} phút` : ''}</div>
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
        
        this.currentPlaylist = playlist;
        this.currentTrackIndex = 0;
        this.populateTrackList();
        this.updateCurrentTrack();
        
        // ✅ Update cached tracks status for offline indicators (with retry if offline manager not ready)
        this.updateCachedTracksStatus();
        
        // ✅ Retry update after 500ms if offline manager wasn't ready yet
        if (!this.offlineManager) {
            setTimeout(async () => {
                if (this.offlineManager && this.currentPlaylist) {
                    await this.updateCachedTracksStatus();
                    this.updateTrackListOfflineIndicators();
                    console.log('🔄 Cached indicators updated (retry after offline manager ready)');
                }
            }, 500);
        }
        
        // Update active state for playlist cards
        const playlistGrid = document.getElementById('playlist-grid');
        if (playlistGrid) {
            playlistGrid.querySelectorAll('.playlist-card').forEach(card => {
                if (parseInt(card.dataset.playlistId) === playlist.id) {
                    card.classList.add('active');
                } else {
                    card.classList.remove('active');
                }
            });
        }
        
        // Also update user playlist cards if visible
        const userPlaylistGrid = document.getElementById('user-playlist-grid');
        if (userPlaylistGrid) {
            userPlaylistGrid.querySelectorAll('.playlist-card').forEach(card => {
                const cardPlaylistId = card.dataset.playlistId;
                // User playlists have string IDs like "user-3"
                if (cardPlaylistId === `user-${playlist.id}` || parseInt(cardPlaylistId) === playlist.id) {
                    card.classList.add('active');
                } else {
                    card.classList.remove('active');
                }
            });
        }
        
        // Lưu state khi chọn playlist mới
        if (!this.isRestoringState) {
            this.savePlayerState();
        }
        
        // Auto-play khi user chọn playlist (KHÔNG auto-play khi restore state)
        if (playlist.tracks.length > 0 && !this.isRestoringState) {
            this.userInteracted = true; // Mark user has interacted
            // Delay một chút để đảm bảo UI đã update
            setTimeout(() => {
                this.playTrack(0);
            }, 100);
        }
    }

    populateTrackList() {
        if (!this.currentPlaylist) return;
        
        if (this.currentPlaylist.tracks.length === 0) {
            this.trackList.innerHTML = `
                <div class="empty-state">
                    <i class="bi bi-music-note"></i>
                    <p>Chưa có bài hát nào</p>
                </div>
            `;
            return;
        }
        
        // ✅ Tối ưu: Sử dụng DocumentFragment để giảm reflow
        const fragment = document.createDocumentFragment();
        
        this.currentPlaylist.tracks.forEach((track, index) => {
            const trackItem = document.createElement('div');
            trackItem.className = 'track-item';
            if (index === this.currentTrackIndex) {
                trackItem.classList.add('active');
            }
            trackItem.dataset.index = index;
            trackItem.dataset.trackId = track.id; // ✅ For offline indicator
            
            // ✅ Escape HTML để tránh XSS
            const escapedTitle = this.escapeHtml(track.title);
            const escapedArtist = this.escapeHtml(track.artist);
            const escapedDuration = this.escapeHtml(track.duration_formatted);
            const playCount = track.play_count || 0;
            
            trackItem.innerHTML = `
                <div class="track-item-number">${index + 1}</div>
                <i class="bi bi-music-note-beamed track-item-icon"></i>
                <div class="track-item-info">
                    <div class="track-item-title">${escapedTitle}</div>
                    <div class="track-item-artist">${escapedArtist}</div>
                </div>
                <div class="track-item-meta">
                    <span class="track-item-play-count" title="Lượt nghe">
                        <i class="bi bi-headphones"></i>
                        <span>${playCount}</span>
                    </span>
                    <span class="track-item-duration">${escapedDuration}</span>
                </div>
            `;
            
            // ✅ Không cần add listener cho từng item - dùng event delegation
            fragment.appendChild(trackItem);
        });
        
        // ✅ Single DOM update thay vì nhiều appendChild calls
        this.trackList.innerHTML = '';
        this.trackList.appendChild(fragment);
    }

    showMessage(message, type = 'info') {
        // ✅ Toast notification thay vì alert - không chặn UX
        
        // Tạo toast element
        const toast = document.createElement('div');
        toast.className = `music-player-toast music-player-toast-${type}`;
        
        // ✅ Preserve line breaks trong message
        toast.style.whiteSpace = 'pre-line';
        toast.textContent = message;
        
        // Style cho toast
        Object.assign(toast.style, {
            position: 'fixed',
            bottom: '20px',
            padding: '16px 20px',
            borderRadius: '12px',
            color: '#fff',
            fontSize: '14px',
            fontWeight: '500',
            zIndex: '100002', /* ✅ Cao hơn player và settings modal */
            maxWidth: this.isIOS ? '90%' : '350px', // ✅ Wider cho iOS messages
            lineHeight: '1.5',
            textAlign: 'center',
            boxShadow: '0 8px 24px rgba(0,0,0,0.4)',
            backgroundColor: type === 'error' ? '#e74c3c' : type === 'success' ? '#27ae60' : '#3498db'
        });
        
        // ✅ Center horizontally on mobile với animation tùy chỉnh
        if (this.isMobile) {
            toast.style.left = '50%';
            toast.style.right = 'auto';
            toast.style.transform = 'translateX(-50%)';
            // ✅ Animation riêng cho mobile để preserve horizontal centering
            toast.style.animation = 'mobileToastSlideIn 0.3s ease-out';
        } else {
            toast.style.right = '20px';
            toast.style.animation = 'slideInUp 0.3s ease-out';
        }
        
        document.body.appendChild(toast);
        
        // ✅ Auto remove sau 5 giây cho iOS messages (dài hơn để đọc), 3s cho các loại khác
        const duration = this.isIOS && message.includes('iOS') ? 5000 : 3000;
        
        setTimeout(() => {
            // ✅ Animation riêng cho mobile khi slide out
            if (this.isMobile) {
                toast.style.animation = 'mobileToastSlideOut 0.3s ease-in';
            } else {
                toast.style.animation = 'slideOutDown 0.3s ease-in';
            }
            
            setTimeout(() => {
                if (toast.parentNode) {
                    toast.parentNode.removeChild(toast);
                }
            }, 300);
        }, duration);
    }
    
    playTrack(index) {
        if (!this.currentPlaylist || !this.currentPlaylist.tracks[index]) return;
        
        // Nếu đang load track hoặc đang restore, không làm gì
        if (this.isLoadingTrack || this.isRestoringState) {
            return;
        }
        
        // ✅ Record play của track hiện tại trước khi chuyển sang track mới
        this.recordCurrentTrackPlay();
        
        const track = this.currentPlaylist.tracks[index];
        
        // Kiểm tra xem có đang phát cùng track này không
        const currentSrc = this.audio.src;
        const isSameTrack = this.currentTrackIndex === index && currentSrc && currentSrc.includes(track.file_url);
        
        if (isSameTrack) {
            // Nếu đang tạm dừng thì tiếp tục phát, không load lại
            if (!this.isPlaying) {
                this.audio.play().catch(e => {
                    // Play failed - handle silently
                });
            }
            return;
        }
        
        // Đánh dấu đang load track
        this.isLoadingTrack = true;
        this.currentTrackIndex = index;
        
        // Sử dụng file_url từ API (đã có đường dẫn đầy đủ)
        const fileUrl = track.file_url;
        
        // Load track mới
        this.audio.src = fileUrl;
        this.audio.load();
        
        // ✅ Preload track for offline (Service Worker will auto-cache)
        this.preloadTrackForOffline(track);
        
        // ✅ Timeout protection
        const loadTimeout = setTimeout(() => {
            if (this.isLoadingTrack) {
                // Track load timeout
                this.isLoadingTrack = false;
                this.showMessage('Timeout khi tải bài hát: ' + track.title, 'error');
            }
        }, 10000); // 10 seconds timeout
        
        // Update UI ngay
        this.updateCurrentTrack();
        this.updateTrackListSelection();
        
        // ✅ Update Media Session cho mobile
        this.updateMediaSessionMetadata();
        
        // Đợi audio sẵn sàng rồi phát
        const onCanPlay = () => {
            this.isLoadingTrack = false;
            clearTimeout(loadTimeout); // ✅ Clear timeout
            
            // Lưu state
            if (!this.isRestoringState) {
                this.savePlayerState();
            }
            
            // Auto play nếu được phép
            if (this.settings.auto_play && this.userInteracted) {
                this.audio.play().catch(e => {
                    // Autoplay prevented
                });
            }
        };
        
        const onError = (e) => {
            this.isLoadingTrack = false;
            clearTimeout(loadTimeout); // ✅ Clear timeout
            console.error('Error loading track:', e);
            
            // ✅ Detailed error handling
            let errorMessage = 'Không thể tải bài hát: ' + track.title;
            
            if (e.target && e.target.error) {
                switch(e.target.error.code) {
                    case 1: // MEDIA_ERR_ABORTED
                        errorMessage = 'Tải bài hát bị hủy: ' + track.title;
                        break;
                    case 2: // MEDIA_ERR_NETWORK
                        errorMessage = 'Lỗi mạng khi tải: ' + track.title;
                        break;
                    case 3: // MEDIA_ERR_DECODE
                        errorMessage = 'Lỗi định dạng file: ' + track.title;
                        break;
                    case 4: // MEDIA_ERR_SRC_NOT_SUPPORTED
                        errorMessage = 'Định dạng không hỗ trợ: ' + track.title;
                        break;
                }
            }
            
            this.showMessage(errorMessage, 'error');
            
            // ✅ Retry mechanism
            setTimeout(() => {
                // Retrying track load
                this.audio.load();
            }, 2000);
        };
        
        // Sử dụng once: true để tránh duplicate listeners
        this.audio.addEventListener('canplaythrough', onCanPlay, { once: true });
        this.audio.addEventListener('error', onError, { once: true });
    }

    updateCurrentTrack() {
        if (!this.currentPlaylist || !this.currentPlaylist.tracks[this.currentTrackIndex]) return;
        
        const track = this.currentPlaylist.tracks[this.currentTrackIndex];
        
        // ✅ Dùng textContent thay vì innerHTML để tránh XSS
        this.currentTrackTitle.textContent = track.title;
        this.currentTrackArtist.textContent = track.artist;
        
        // Update album cover (track cover → playlist cover → default) with cache-busting
        if (this.currentAlbumCover) {
            const playlistCover = this.currentPlaylist && this.currentPlaylist.cover_image ? this.currentPlaylist.cover_image : null;
            const baseUrl = track.album_cover || playlistCover || '/static/music_player/images/album-art.png';
            const cb = `v=${Date.now()}`;
            const albumCoverUrl = baseUrl.includes('?') ? `${baseUrl}&${cb}` : `${baseUrl}?${cb}`;
            this.currentAlbumCover.src = albumCoverUrl;
        }
        
        // Update play count display
        if (this.playCountNumber) {
            const playCount = track.play_count || 0;
            this.playCountNumber.textContent = playCount;
        }
        
        // Force refresh Media Session metadata to update lock screen artwork
        this.updateMediaSessionMetadata();
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
                // Play failed
                this.showMessage('Không thể phát nhạc. Vui lòng thử lại.', 'error');
            });
        }
        
        // ✅ Update Media Session cho mobile
        this.updateMediaSessionMetadata();
    }

    previousTrack() {
        if (!this.currentPlaylist) return;
        
        const prevIndex = this.getPreviousTrackIndex();
        
        // Nếu ở vị trí đầu mà không repeat, không làm gì
        if (prevIndex === this.currentTrackIndex && this.repeatMode === 'none' && this.currentTrackIndex === 0) {
            return;
        }
        
        this.playTrack(prevIndex);
        this.updateMediaSessionMetadata();
    }

    nextTrack() {
        if (!this.currentPlaylist) return;
        
        const nextIndex = this.getNextTrackIndex();
        
        // Nếu ở cuối playlist mà không repeat, dừng phát
        if (nextIndex === this.currentTrackIndex && 
            this.currentTrackIndex === this.currentPlaylist.tracks.length - 1 && 
            this.repeatMode !== 'all') {
            this.audio.pause();
            this.isPlaying = false;
            this.updatePlayPauseButtons();
            return;
        }
        
        this.playTrack(nextIndex);
        this.updateMediaSessionMetadata();
    }

    onTrackEnd() {
        // Track ended
        if (this.repeatMode === 'one') {
            // Lặp lại bài hiện tại
            this.audio.currentTime = 0;
            this.audio.play().catch(e => {
                // Play failed
            });
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
        
        // Thêm class 'playing' cho toggle button để trigger animation
        this.toggle.classList.add('playing');
        
        // Force update thời gian khi bắt đầu phát
        this.updateDuration();
        this.updateProgress();
        
        // ✅ Update Media Session playback state cho màn hình khóa
        if ('mediaSession' in navigator) {
            navigator.mediaSession.playbackState = 'playing';
        }
        
        // Lưu state khi bắt đầu phát
        if (!this.isRestoringState) {
            this.savePlayerState();
        }
        
        // ✅ Start tracking play time
        this.startPlayTracking();
    }

    onPause() {
        this.isPlaying = false;
        this.updatePlayPauseButtons();
        
        // Xóa class 'playing' khỏi toggle button để tắt animation
        this.toggle.classList.remove('playing');
        
        // ✅ Update Media Session playback state cho màn hình khóa
        if ('mediaSession' in navigator) {
            navigator.mediaSession.playbackState = 'paused';
        }
        
        // Lưu state khi tạm dừng
        if (!this.isRestoringState) {
            this.savePlayerState();
        }
        
        // ✅ Stop tracking play time
        this.stopPlayTracking();
    }

    updatePlayPauseButtons() {
        const icon = this.isPlaying ? 'bi-pause-fill' : 'bi-play-fill';
        this.playPauseBtn.innerHTML = `<i class="bi ${icon}"></i>`;
    }

    updateDuration() {
        const duration = this.audio.duration;
        if (this.totalTime && duration) {
            this.totalTime.textContent = this.formatTime(duration);
        }
    }

    updateProgress() {
        if (!this.audio.duration) return;
        
        // ✅ Throttle updates - chỉ update UI mỗi 250ms để giảm CPU usage
        const now = Date.now();
        if (now - this.lastProgressUpdate < 250) {
            return;
        }
        this.lastProgressUpdate = now;
        
        const progress = (this.audio.currentTime / this.audio.duration) * 100;
        
        // ✅ Batch DOM updates để tránh reflow nhiều lần
        requestAnimationFrame(() => {
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
        });
        
        // ✅ Update Media Session position cho lock screen (mỗi 5 giây để tối ưu)
        if (Math.floor(this.audio.currentTime) % 5 === 0 && 'mediaSession' in navigator) {
            try {
                if (this.audio.duration && !isNaN(this.audio.duration)) {
                    navigator.mediaSession.setPositionState({
                        duration: this.audio.duration,
                        playbackRate: this.audio.playbackRate,
                        position: this.audio.currentTime
                    });
                }
            } catch (error) {
                // Silent fail - không log để tránh spam console
            }
        }
        
    }

    formatTime(seconds) {
        // ✅ Cache với LRU limit (giữ tối đa 100 entries để tiết kiệm memory)
        const secondsInt = Math.floor(seconds);
        
        if (this.formatTimeCache.has(secondsInt)) {
            return this.formatTimeCache.get(secondsInt);
        }
        
        const mins = Math.floor(secondsInt / 60);
        const secs = secondsInt % 60;
        const formatted = `${mins}:${secs.toString().padStart(2, '0')}`;
        
        // ✅ LRU cleanup - clear cache khi quá 100 entries
        if (this.formatTimeCache.size > 100) {
            const firstKey = this.formatTimeCache.keys().next().value;
            this.formatTimeCache.delete(firstKey);
        }
        
        this.formatTimeCache.set(secondsInt, formatted);
        return formatted;
    }

    seekToPosition(event) {
        if (!this.audio.duration) {
            return;
        }
        
        const rect = this.progressBar.getBoundingClientRect();
        // ✅ Fix mobile touch events - handle both mouse and touch properly
        let clickX;
        if (event.touches && event.touches[0]) {
            // Touch event
            clickX = event.touches[0].clientX - rect.left;
        } else {
            // Mouse event
            clickX = (event.clientX || event.pageX) - rect.left;
        }
        
        const percent = Math.max(0, Math.min(1, clickX / rect.width));
        const newTime = percent * this.audio.duration;
        
        // ✅ Validate và set time
        if (isFinite(newTime) && newTime >= 0) {
            this.audio.currentTime = newTime;
            
            // Force update UI immediately
            this.updateProgress();
            
            // Save state after seeking
            if (!this.isRestoringState) {
                this.savePlayerState();
            }
        }
    }

    startSeeking(event) {
        if (!this.audio.duration) return;
        
        const isTouchEvent = event.type && event.type.startsWith('touch');
        
        const handleSeek = (e) => {
            if (!this.audio.duration) return;
            
            // ✅ Improved touch event handling
            let clientX;
            if (isTouchEvent && e.touches && e.touches[0]) {
                clientX = e.touches[0].clientX;
            } else {
                clientX = e.clientX;
            }
            
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
                document.removeEventListener('touchcancel', handleEnd);
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
            document.addEventListener('touchcancel', handleEnd);
        } else {
            document.addEventListener('mousemove', handleSeek);
            document.addEventListener('mouseup', handleEnd);
        }
    }
    
    // ✅ Retry audio load với URL encoding fix
    retryAudioLoad() {
        if (!this.currentTrack || !this.currentPlaylist) return;
        
        const track = this.currentPlaylist.tracks[this.currentTrackIndex];
        if (!track || !track.file_url) return;
        
        console.log('🔄 Retrying audio load...');
        
        // ✅ Use URL as-is from backend (Django already encodes it properly)
        this.audio.src = track.file_url;
        this.audio.load();
        
        // ✅ Timeout protection cho retry
        setTimeout(() => {
            if (this.isLoadingTrack) {
                console.warn('⚠️ Retry timeout, skipping track');
                this.isLoadingTrack = false;
                this.nextTrack(); // Skip to next track
            }
        }, 5000);
    }
    
    // Method để test seek functionality
    testSeek(percent) {
        if (!this.audio.duration) {
            // Cannot test seek: no duration
            return;
        }
        
        const newTime = percent * this.audio.duration;
        // Testing seek
        
        this.audio.currentTime = newTime;
        this.updateProgress();
        
        // Verify after a short delay
        setTimeout(() => {
            // Seek result
        }, 100);
    }

    // ========================================
    // ✅ VOLUME CONTROL METHODS - VIẾT LẠI TỪ ĐẦU
    // ========================================
    
    handleVolumeClick(event) {
        if (this.isDraggingVolume) return; // Ignore clicks during drag
        
        const rect = event.currentTarget.getBoundingClientRect();
        const x = event.clientX - rect.left;
        const percent = Math.max(0, Math.min(1, x / rect.width));
        
        this.setVolumePercent(percent);
    }
    
    handleVolumeTouchStart(event, volumeBar) {
        event.preventDefault();
        event.stopPropagation();
        
        // Get initial touch position và set volume ngay
        const touch = event.touches[0];
        const rect = volumeBar.getBoundingClientRect();
        const x = touch.clientX - rect.left;
        const percent = Math.max(0, Math.min(1, x / rect.width));
        
        this.setVolumePercent(percent);
        
        // Start tracking touch move
        this.startVolumeDrag(event, true);
    }
    
    startVolumeDrag(event, isTouch) {
        event.preventDefault();
        this.isDraggingVolume = true;
        
        const volumeBar = this.volumeFill.parentElement;
        
        const onMove = (e) => {
            e.preventDefault();
            
            const clientX = isTouch ? e.touches[0].clientX : e.clientX;
            const rect = volumeBar.getBoundingClientRect();
            const x = clientX - rect.left;
            const percent = Math.max(0, Math.min(1, x / rect.width));
            
            // ✅ Use immediate update for mobile touch, regular for desktop
            if (isTouch) {
                this.setVolumePercentImmediate(percent);
            } else {
                this.setVolumePercent(percent);
            }
        };
        
        const onEnd = () => {
            this.isDraggingVolume = false;
            
            if (isTouch) {
                document.removeEventListener('touchmove', onMove);
                document.removeEventListener('touchend', onEnd);
                document.removeEventListener('touchcancel', onEnd);
            } else {
                document.removeEventListener('mousemove', onMove);
                document.removeEventListener('mouseup', onEnd);
            }
            
            this.saveSettings();
        };
        
        if (isTouch) {
            document.addEventListener('touchmove', onMove, { passive: false });
            document.addEventListener('touchend', onEnd);
            document.addEventListener('touchcancel', onEnd);
        } else {
            document.addEventListener('mousemove', onMove);
            document.addEventListener('mouseup', onEnd);
        }
    }
    
    setVolumePercent(percent) {
        // Unmute tự động nếu kéo volume lên
        if (percent > 0 && this.isMuted) {
            this.isMuted = false;
        }
        
        this.volume = percent;
        this.audio.volume = this.isMuted ? 0 : percent;
        this.updateVolumeDisplay();
        
        // Volume set
    }
    
    // ✅ Immediate volume update for smooth mobile dragging
    setVolumePercentImmediate(percent) {
        // Unmute tự động nếu kéo volume lên
        if (percent > 0 && this.isMuted) {
            this.isMuted = false;
        }
        
        this.volume = percent;
        this.audio.volume = this.isMuted ? 0 : percent;
        
        // ✅ Immediate visual update without transition for smooth dragging
        const volumePercent = this.isMuted ? 0 : this.volume * 100;
        this.volumeFill.style.width = `${volumePercent}%`;
        this.volumeHandle.style.left = `${volumePercent}%`;
        
        // ✅ Update icon immediately
        const icon = this.isMuted ? 'bi-volume-mute-fill' : 
                    this.volume === 0 ? 'bi-volume-mute-fill' :
                    this.volume < 0.5 ? 'bi-volume-down-fill' : 'bi-volume-up-fill';
        this.muteBtn.innerHTML = `<i class="bi ${icon}"></i>`;
    }

    toggleMute() {
        this.isMuted = !this.isMuted;
        this.audio.volume = this.isMuted ? 0 : this.volume;
        // Mute toggled
        this.updateVolumeDisplay();
    }

    initializeVolumeDisplay() {
        // ✅ Initialize volume display with default values
        if (this.volumeFill && this.volumeHandle && this.muteBtn) {
            const volumePercent = this.isMuted ? 0 : this.volume * 100;
            this.volumeFill.style.width = `${volumePercent}%`;
            this.volumeHandle.style.left = `${volumePercent}%`;
            
            const icon = this.isMuted ? 'bi-volume-mute-fill' : 
                        this.volume === 0 ? 'bi-volume-mute-fill' :
                        this.volume < 0.5 ? 'bi-volume-down-fill' : 'bi-volume-up-fill';
            this.muteBtn.innerHTML = `<i class="bi ${icon}"></i>`;
        }
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
        
        // Shuffle mode changed
    }

    toggleRepeat() {
        const modes = ['none', 'one', 'all'];
        const currentIndex = modes.indexOf(this.repeatMode);
        this.repeatMode = modes[(currentIndex + 1) % modes.length];
        
        // Cập nhật icon và styling
        this.updateRepeatButton();
        this.saveSettings();
        
        // Repeat mode changed
    }
    
    updateRepeatButton() {
        if (!this.repeatBtn) return;
        
        // Xóa tất cả classes active
        this.repeatBtn.classList.remove('active');
        
        // Thêm class active nếu không phải 'none'
        if (this.repeatMode !== 'none') {
            this.repeatBtn.classList.add('active');
        }
        
        // Cập nhật icon và text dựa trên mode
        let content = '';
        if (this.repeatMode === 'none') {
            // Không lặp - icon mờ
            content = `<i class="bi bi-arrow-repeat"></i>`;
        } else if (this.repeatMode === 'one') {
            // Lặp 1 bài - icon + số "1"
            content = `
                <i class="bi bi-arrow-repeat"></i>
                <span style="position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); font-size: 10px; font-weight: bold; color: #f093fb;">1</span>
            `;
        } else if (this.repeatMode === 'all') {
            // Lặp tất cả - icon sáng
            content = `<i class="bi bi-arrow-repeat"></i>`;
        }
        
        this.repeatBtn.innerHTML = content;
        
        // Thêm title để hiển thị tooltip
        const titles = {
            'none': 'Không lặp',
            'one': 'Lặp một bài',
            'all': 'Lặp tất cả'
        };
        this.repeatBtn.title = titles[this.repeatMode] || 'Lặp lại';
    }

    togglePlayer() {
        // Nếu đang khóa, không cho đóng bằng toggle hoặc phím tắt
        if (this.settings && this.settings.listening_lock) {
            // Nếu đang ẩn (ví dụ khi mới vào trang), thì mở
            if (this.popup.classList.contains('hidden')) {
                this.popup.classList.remove('hidden');
                
                // ✅ Update cached indicators khi mở player (listening lock case)
                setTimeout(() => {
                    this.updateTrackListOfflineIndicators();
                }, 100);
            }
            return;
        }
        const wasHidden = this.popup.classList.contains('hidden');
        this.popup.classList.toggle('hidden');
        
        // Nếu đang mở player (từ hidden → visible)
        if (wasHidden) {
            // Opening player - refreshing playlists
            this.refreshPlaylists();
            
            // ✅ Update cached indicators khi mở player
            setTimeout(() => {
                this.updateTrackListOfflineIndicators();
                console.log('🔄 Updated cached indicators after opening player');
            }, 200);
            
            // ✅ Reset iOS volume message flag khi mở player
            // (Chỉ show khi user tự nhấn vào volume controls, không auto-show)
            if (this.isIOS) {
                this.hasShownIOSVolumeMessage = false;
                // iOS volume message flag reset
            }
            
            // ✅ Auto-play khi mở lần đầu tiên
            if (!this.hasOpenedPlayer) {
                this.hasOpenedPlayer = true;
                this.userInteracted = true; // Mark user has interacted
                
                // Delay một chút để đảm bảo playlists đã load
                setTimeout(() => {
                    // Nếu chưa phát nhạc và có playlist available
                    if (!this.isPlaying && this.currentPlaylist && this.currentPlaylist.tracks.length > 0) {
                        // Auto-playing on first open
                        this.playTrack(this.currentTrackIndex);
                    }
                }, 300);
            }
        } else {
            // ✅ Đang đóng player
            // Closing player
        }
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

    // ✅ Throttled drag method - giảm 70% CPU usage
    throttledDrag(event) {
        if (!this.isDragging) return;
        
        // Nếu đã có animation frame pending, skip
        if (this.dragAnimationFrame) return;
        
        // Schedule update trên next animation frame
        this.dragAnimationFrame = requestAnimationFrame(() => {
            this.drag(event);
            this.dragAnimationFrame = null;
        });
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
            
            // ✅ Cancel pending animation frame
            if (this.dragAnimationFrame) {
                cancelAnimationFrame(this.dragAnimationFrame);
                this.dragAnimationFrame = null;
            }
        }
    }

    handleKeyboard(event) {
        // ✅ Không xử lý phím tắt khi đang typing trong input/textarea
        if (event.target.tagName === 'INPUT' || event.target.tagName === 'TEXTAREA') return;
        
        // ✅ Kiểm tra modifier keys
        const hasShift = event.shiftKey;
        const hasCtrl = event.ctrlKey || event.metaKey;
        
        switch(event.code) {
            // Play/Pause
            case 'Space':
                event.preventDefault();
                this.togglePlayPause();
                this.showKeyboardHint('⏯️ Play/Pause');
                break;
            
            // Previous/Next track
            case 'ArrowLeft':
                event.preventDefault();
                if (hasShift) {
                    // Shift + Left: Seek backward 10s
                    this.seekBackward(10);
                    this.showKeyboardHint('⏪ -10s');
                } else {
                    this.previousTrack();
                    this.showKeyboardHint('⏮️ Previous');
                }
                break;
            
            case 'ArrowRight':
                event.preventDefault();
                if (hasShift) {
                    // Shift + Right: Seek forward 10s
                    this.seekForward(10);
                    this.showKeyboardHint('⏩ +10s');
                } else {
                    this.nextTrack();
                    this.showKeyboardHint('⏭️ Next');
                }
                break;
            
            // Volume Up/Down
            case 'ArrowUp':
                event.preventDefault();
                if (this.isIOS) {
                    this.showIOSVolumeMessage();
                } else {
                    this.adjustVolume(0.1);
                    this.showKeyboardHint(`🔊 Volume: ${Math.round(this.volume * 100)}%`);
                }
                break;
            
            case 'ArrowDown':
                event.preventDefault();
                if (this.isIOS) {
                    this.showIOSVolumeMessage();
                } else {
                    this.adjustVolume(-0.1);
                    this.showKeyboardHint(`🔉 Volume: ${Math.round(this.volume * 100)}%`);
                }
                break;
            
            // Mute
            case 'KeyM':
                event.preventDefault();
                if (this.isIOS) {
                    this.showIOSVolumeMessage();
                } else {
                    this.toggleMute();
                    this.showKeyboardHint(this.isMuted ? '🔇 Muted' : '🔊 Unmuted');
                }
                break;
            
            // Shuffle
            case 'KeyS':
                event.preventDefault();
                this.toggleShuffle();
                this.showKeyboardHint(this.isShuffled ? '🔀 Shuffle On' : '➡️ Shuffle Off');
                break;
            
            // Repeat
            case 'KeyR':
                event.preventDefault();
                this.toggleRepeat();
                const repeatTexts = {
                    'none': '➡️ Repeat Off',
                    'one': '🔂 Repeat One',
                    'all': '🔁 Repeat All'
                };
                this.showKeyboardHint(repeatTexts[this.repeatMode]);
                break;
            
            // Toggle Player (P key hoặc Escape)
            case 'KeyP':
            case 'Escape':
                event.preventDefault();
                this.togglePlayer();
                this.showKeyboardHint(this.popup.classList.contains('hidden') ? '📻 Player Closed' : '🎵 Player Opened');
                break;
            
            // Number keys (0-9): Seek to percentage
            case 'Digit0': case 'Digit1': case 'Digit2': case 'Digit3': case 'Digit4':
            case 'Digit5': case 'Digit6': case 'Digit7': case 'Digit8': case 'Digit9':
                event.preventDefault();
                const digit = parseInt(event.code.replace('Digit', ''));
                const percent = digit / 10;
                if (this.audio.duration) {
                    this.seekTo(this.audio.duration * percent);
                    this.showKeyboardHint(`⏩ Seek to ${digit * 10}%`);
                }
                break;
            
            // Question mark: Show keyboard shortcuts help
            case 'Slash':
                if (hasShift) { // Shift + / = ?
                    event.preventDefault();
                    this.showKeyboardShortcuts();
                }
                break;
        }
    }
    
    // ✅ Helper method để adjust volume
    adjustVolume(delta) {
        const newVolume = Math.max(0, Math.min(1, this.volume + delta));
        this.setVolumePercent(newVolume);
        this.saveSettings();
    }
    
    // ✅ Hiển thị keyboard hint khi dùng phím tắt
    showKeyboardHint(text) {
        // Tạo hint element
        let hint = document.getElementById('keyboard-hint');
        if (!hint) {
            hint = document.createElement('div');
            hint.id = 'keyboard-hint';
            hint.style.cssText = `
                position: fixed;
                top: 50%;
                left: 50%;
                transform: translate(-50%, -50%);
                background: rgba(0, 0, 0, 0.9);
                color: white;
                padding: 16px 24px;
                border-radius: 12px;
                font-size: 18px;
                font-weight: 600;
                z-index: 100002;
                pointer-events: none;
                box-shadow: 0 8px 24px rgba(0, 0, 0, 0.5);
                animation: keyboardHintFade 1s ease-in-out;
            `;
            document.body.appendChild(hint);
        }
        
        hint.textContent = text;
        hint.style.display = 'block';
        hint.style.animation = 'none';
        
        // Trigger reflow để restart animation
        void hint.offsetWidth;
        hint.style.animation = 'keyboardHintFade 1s ease-in-out';
        
        // Auto hide
        clearTimeout(hint.hideTimeout);
        hint.hideTimeout = setTimeout(() => {
            hint.style.display = 'none';
        }, 1000);
    }
    
    // ✅ Show sleep timer modal
    showSleepTimerModal() {
        // Remove existing modal if any
        const existingModal = document.getElementById('sleep-timer-modal');
        if (existingModal) {
            existingModal.remove();
        }
        
        const modal = document.createElement('div');
        modal.id = 'sleep-timer-modal';
        
        // Get music player popup bounds để căn giữa với popup
        const playerPopup = document.getElementById('music-player-popup');
        const playerRect = playerPopup ? playerPopup.getBoundingClientRect() : null;
        
        if (playerRect && !playerPopup.classList.contains('hidden')) {
            // Desktop: Căn giữa với popup
            modal.style.cssText = `
                position: fixed;
                top: ${playerRect.top}px;
                left: ${playerRect.left}px;
                width: ${playerRect.width}px;
                height: ${playerRect.height}px;
                background: rgba(0, 0, 0, 0.8);
                z-index: 100010;
                display: flex;
                align-items: center;
                justify-content: center;
                animation: fadeIn 0.3s ease;
            `;
        } else {
            // Mobile hoặc popup bị ẩn: Full screen
            modal.style.cssText = `
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background: rgba(0, 0, 0, 0.8);
                z-index: 100010;
                display: flex;
                align-items: center;
                justify-content: center;
                animation: fadeIn 0.3s ease;
            `;
        }
        
        // Check if timer is active
        const isActive = this.sleepTimerActive;
        
        // Responsive sizing based on popup size
        const isDesktop = playerRect && !playerPopup.classList.contains('hidden');
        
        const remainingText = isActive ? 
            `<div class="timer-remaining" style="color: #ffd700; font-weight: 600; font-size: 18px; text-align: center; margin-bottom: 15px; text-shadow: 0 0 10px rgba(255, 215, 0, 0.5);">Còn lại: ${this.timerRemaining?.textContent || '--:--'}</div>` : '';
        
        const cancelButton = isActive ? 
            `<button id="cancel-timer-modal-btn" style="
                display: block;
                width: 100%;
                background: rgba(255, 77, 77, 0.8);
                border: none;
                border-radius: 8px;
                color: white;
                padding: ${isDesktop ? '8px 16px' : '12px 20px'};
                font-size: ${isDesktop ? '13px' : '14px'};
                font-weight: 600;
                cursor: pointer;
                transition: all 0.2s ease;
                margin-top: 15px;
            " onmouseover="this.style.background='rgba(255, 77, 77, 1)'" onmouseout="this.style.background='rgba(255, 77, 77, 0.8)'">
                Hủy Timer
            </button>` : '';
        const contentStyle = isDesktop ? `
            background: linear-gradient(135deg, rgba(102, 126, 234, 0.95) 0%, rgba(118, 75, 162, 0.95) 100%);
            backdrop-filter: blur(10px);
            border-radius: 15px;
            padding: 20px;
            max-width: 250px;
            width: 90%;
            box-shadow: 0 15px 40px rgba(0, 0, 0, 0.5);
            border: 1px solid rgba(255, 255, 255, 0.2);
            animation: modalSlideIn 0.3s ease;
        ` : `
            background: linear-gradient(135deg, rgba(102, 126, 234, 0.95) 0%, rgba(118, 75, 162, 0.95) 100%);
            backdrop-filter: blur(10px);
            border-radius: 20px;
            padding: 30px;
            max-width: 300px;
            width: 90%;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5);
            border: 1px solid rgba(255, 255, 255, 0.2);
            animation: modalSlideIn 0.3s ease;
        `;
        
        modal.innerHTML = `
            <div style="${contentStyle}">
                <h3 style="color: white; margin: 0 0 ${isDesktop ? '15px' : '20px'} 0; font-size: ${isDesktop ? '16px' : '20px'}; display: flex; align-items: center; gap: 10px; justify-content: center;">
                    ⏰ Hẹn giờ tắt nhạc
                </h3>
                ${remainingText}
                <div style="display: flex; flex-direction: column; gap: ${isDesktop ? '8px' : '10px'};">
                    <button class="sleep-timer-modal-option" data-minutes="15" style="
                        display: block;
                        width: 100%;
                        background: rgba(255, 255, 255, 0.15);
                        border: none;
                        border-radius: 8px;
                        color: white;
                        padding: ${isDesktop ? '8px 16px' : '12px 20px'};
                        font-size: ${isDesktop ? '13px' : '14px'};
                        font-weight: 500;
                        cursor: pointer;
                        transition: all 0.2s ease;
                        text-align: left;
                    " onmouseover="this.style.background='rgba(255, 255, 255, 0.25)'" onmouseout="this.style.background='rgba(255, 255, 255, 0.15)'">
                        15 phút
                    </button>
                    <button class="sleep-timer-modal-option" data-minutes="30" style="
                        display: block;
                        width: 100%;
                        background: rgba(255, 255, 255, 0.15);
                        border: none;
                        border-radius: 8px;
                        color: white;
                        padding: ${isDesktop ? '8px 16px' : '12px 20px'};
                        font-size: ${isDesktop ? '13px' : '14px'};
                        font-weight: 500;
                        cursor: pointer;
                        transition: all 0.2s ease;
                        text-align: left;
                    " onmouseover="this.style.background='rgba(255, 255, 255, 0.25)'" onmouseout="this.style.background='rgba(255, 255, 255, 0.15)'">
                        30 phút
                    </button>
                    <button class="sleep-timer-modal-option" data-minutes="60" style="
                        display: block;
                        width: 100%;
                        background: rgba(255, 255, 255, 0.15);
                        border: none;
                        border-radius: 8px;
                        color: white;
                        padding: ${isDesktop ? '8px 16px' : '12px 20px'};
                        font-size: ${isDesktop ? '13px' : '14px'};
                        font-weight: 500;
                        cursor: pointer;
                        transition: all 0.2s ease;
                        text-align: left;
                    " onmouseover="this.style.background='rgba(255, 255, 255, 0.25)'" onmouseout="this.style.background='rgba(255, 255, 255, 0.15)'">
                        1 giờ
                    </button>
                    <button class="sleep-timer-modal-option" data-minutes="120" style="
                        display: block;
                        width: 100%;
                        background: rgba(255, 255, 255, 0.15);
                        border: none;
                        border-radius: 8px;
                        color: white;
                        padding: ${isDesktop ? '8px 16px' : '12px 20px'};
                        font-size: ${isDesktop ? '13px' : '14px'};
                        font-weight: 500;
                        cursor: pointer;
                        transition: all 0.2s ease;
                        text-align: left;
                    " onmouseover="this.style.background='rgba(255, 255, 255, 0.25)'" onmouseout="this.style.background='rgba(255, 255, 255, 0.15)'">
                        2 giờ
                    </button>
                </div>
                ${cancelButton}
                <button id="sleep-timer-close-btn" style="
                    margin-top: ${isDesktop ? '15px' : '20px'};
                    padding: ${isDesktop ? '8px 16px' : '10px 20px'};
                    background: rgba(255, 255, 255, 0.2);
                    border: 1px solid rgba(255, 255, 255, 0.3);
                    border-radius: 8px;
                    color: white;
                    font-weight: 600;
                    font-size: ${isDesktop ? '13px' : '14px'};
                    cursor: pointer;
                    width: 100%;
                    transition: all 0.2s;
                " onmouseover="this.style.background='rgba(255, 255, 255, 0.3)'" onmouseout="this.style.background='rgba(255, 255, 255, 0.2)'">
                    Đóng (Esc)
                </button>
            </div>
        `;
        
        // Close button
        const closeBtn = modal.querySelector('#sleep-timer-close-btn');
        closeBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            modal.remove();
        });
        
        // Cancel timer button
        if (isActive) {
            const cancelBtn = modal.querySelector('#cancel-timer-modal-btn');
            cancelBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                this.cancelSleepTimer();
                modal.remove();
            });
        }
        
        // Timer options
        const timerOptions = modal.querySelectorAll('.sleep-timer-modal-option');
        timerOptions.forEach(option => {
            option.addEventListener('click', (e) => {
                e.stopPropagation();
                const minutes = parseInt(option.getAttribute('data-minutes'));
                this.setSleepTimer(minutes);
                modal.remove();
            });
        });
        
        // Close on click outside
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                e.stopPropagation();
                modal.remove();
            }
        });
        
        // Close on Escape
        const escapeHandler = (e) => {
            if (e.code === 'Escape') {
                e.stopPropagation();
                modal.remove();
                document.removeEventListener('keydown', escapeHandler);
            }
        };
        document.addEventListener('keydown', escapeHandler);
        
        // Add to DOM
        document.body.appendChild(modal);
    }

    // ✅ Show keyboard shortcuts modal
    showKeyboardShortcuts() {
        const modal = document.createElement('div');
        modal.id = 'keyboard-shortcuts-modal';
        
        // Get music player popup bounds để căn giữa với popup
        const playerPopup = document.getElementById('music-player-popup');
        const playerRect = playerPopup ? playerPopup.getBoundingClientRect() : null;
        
        if (playerRect && !playerPopup.classList.contains('hidden')) {
            // Desktop: Căn giữa với popup
            modal.style.cssText = `
                position: fixed;
                top: ${playerRect.top}px;
                left: ${playerRect.left}px;
                width: ${playerRect.width}px;
                height: ${playerRect.height}px;
                background: rgba(0, 0, 0, 0.8);
                z-index: 100003;
                display: flex;
                align-items: center;
                justify-content: center;
                animation: fadeIn 0.3s ease;
            `;
        } else {
            // Mobile hoặc popup bị ẩn: Full screen
            modal.style.cssText = `
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background: rgba(0, 0, 0, 0.8);
                z-index: 100003;
                display: flex;
                align-items: center;
                justify-content: center;
                animation: fadeIn 0.3s ease;
            `;
        }
        
        // ✅ iOS warning note
        const iosWarning = this.isIOS ? `
            <div style="
                background: rgba(255, 152, 0, 0.2);
                border: 1px solid rgba(255, 152, 0, 0.4);
                border-radius: 8px;
                padding: 12px;
                margin-bottom: 15px;
                color: #ffa726;
                font-size: 13px;
                line-height: 1.5;
            ">
                🍎 <strong>iOS Note:</strong> Volume controls không khả dụng trên iOS do giới hạn của hệ điều hành. 
                Vui lòng dùng phím cứng bên cạnh thiết bị.
            </div>
        ` : '';
        
        // Responsive sizing based on popup size
        const isDesktop = playerRect && !playerPopup.classList.contains('hidden');
        
        modal.innerHTML = `
            <div style="
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                border-radius: ${isDesktop ? '15px' : '20px'};
                padding: ${isDesktop ? '20px' : '30px'};
                max-width: ${isDesktop ? '500px' : '600px'};
                max-height: ${isDesktop ? '90%' : '80vh'};
                width: ${isDesktop ? '90%' : 'auto'};
                overflow-y: auto;
                box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5);
            ">
                <h3 style="color: white; margin: 0 0 ${isDesktop ? '15px' : '20px'} 0; font-size: ${isDesktop ? '20px' : '24px'}; display: flex; align-items: center; gap: 10px;">
                    ⌨️ Phím tắt Music
                </h3>
                ${iosWarning}
                <div style="display: grid; grid-template-columns: ${isDesktop ? '1fr' : '1fr 1fr'}; gap: ${isDesktop ? '8px' : '12px'}; color: white;">
                    <div><kbd>Space</kbd> Play/Pause</div>
                    <div style="${this.isIOS ? 'opacity: 0.5;' : ''}"><kbd>M</kbd> Mute/Unmute${this.isIOS ? ' 🚫' : ''}</div>
                    <div><kbd>←</kbd> Previous track</div>
                    <div><kbd>→</kbd> Next track</div>
                    <div style="${this.isIOS ? 'opacity: 0.5;' : ''}"><kbd>↑</kbd> Volume up${this.isIOS ? ' 🚫' : ''}</div>
                    <div style="${this.isIOS ? 'opacity: 0.5;' : ''}"><kbd>↓</kbd> Volume down${this.isIOS ? ' 🚫' : ''}</div>
                    <div><kbd>Shift+←</kbd> Seek -10s</div>
                    <div><kbd>Shift+→</kbd> Seek +10s</div>
                    <div><kbd>S</kbd> Toggle shuffle</div>
                    <div><kbd>R</kbd> Toggle repeat</div>
                    <div><kbd>P</kbd> / <kbd>Esc</kbd> Toggle player</div>
                    <div><kbd>0-9</kbd> Seek to %</div>
                    <div><kbd>Shift+?</kbd> Show shortcuts</div>
                </div>
                <button id="shortcuts-close-btn" style="
                    margin-top: ${isDesktop ? '15px' : '20px'};
                    padding: ${isDesktop ? '8px 16px' : '10px 20px'};
                    background: rgba(255, 255, 255, 0.2);
                    border: 1px solid rgba(255, 255, 255, 0.3);
                    border-radius: 8px;
                    color: white;
                    font-weight: 600;
                    font-size: ${isDesktop ? '13px' : '14px'};
                    cursor: pointer;
                    width: 100%;
                    transition: all 0.2s;
                " onmouseover="this.style.background='rgba(255, 255, 255, 0.3)'" onmouseout="this.style.background='rgba(255, 255, 255, 0.2)'">
                    Đóng (Esc)
                </button>
            </div>
        `;
        
        // ✅ Close button với stopPropagation để không đóng popup
        const closeBtn = modal.querySelector('#shortcuts-close-btn');
        closeBtn.addEventListener('click', (e) => {
            e.stopPropagation(); // ✅ Prevent closing music player
            modal.remove();
        });
        
        // Close on click outside
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                e.stopPropagation(); // ✅ Prevent closing music player
                modal.remove();
            }
        });
        
        // Close on Escape
        const escapeHandler = (e) => {
            if (e.code === 'Escape') {
                e.stopPropagation(); // ✅ Prevent closing music player
                modal.remove();
                document.removeEventListener('keydown', escapeHandler);
            }
        };
        document.addEventListener('keydown', escapeHandler);
        
        document.body.appendChild(modal);
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
            // ✅ Fallback: Initialize volume display with default values
            this.updateVolumeDisplay();
        }
    }

    async saveSettings() {
        // Chỉ save lên server nếu có CSRF token (user đã đăng nhập)
        const csrfToken = this.getCSRFToken();
        if (!csrfToken) {
            // User chưa đăng nhập, settings sẽ được lưu trong localStorage
            // thông qua savePlayerState(), không cần gọi API
            return;
        }
        
        try {
            const response = await fetch('/music/api/settings/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken
                },
                body: JSON.stringify({
                    auto_play: this.settings.auto_play,
                    volume: this.volume,
                    repeat_mode: this.repeatMode,
                    shuffle: this.isShuffled,
                    default_playlist_id: this.currentPlaylist ? this.currentPlaylist.id : null
                })
            });
            
            // Nếu 401 (session expired), không log error
            if (!response.ok && response.status !== 401) {
                console.error('Error saving settings:', response.status);
            }
        } catch (error) {
            // Silent fail - settings vẫn được lưu trong localStorage
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
        
        // ✅ Debounce saves - chỉ lưu sau 500ms idle để giảm localStorage writes
        if (this.saveStateDebounceTimer) {
            clearTimeout(this.saveStateDebounceTimer);
        }
        
        this.saveStateDebounceTimer = setTimeout(() => {
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
        }, 500);
    }
    
    // ✅ Immediate save (không debounce) - dùng khi beforeunload
    savePlayerStateImmediate() {
        if (this.isRestoringState || !this.currentPlaylist) {
            return;
        }
        
        // Clear debounce timer
        if (this.saveStateDebounceTimer) {
            clearTimeout(this.saveStateDebounceTimer);
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

    async restorePlayerState() {
        try {
            const stateStr = localStorage.getItem('musicPlayerState');
            if (!stateStr) {
                return false;
            }
            
            const state = JSON.parse(stateStr);
            
            // Chỉ restore nếu state không quá cũ (trong vòng 2 giờ)
            const maxAge = 2 * 60 * 60 * 1000;
            if (Date.now() - state.timestamp > maxAge) {
                localStorage.removeItem('musicPlayerState');
                return false;
            }
            
            let playlist = null;
            
            // ✅ Check if this is a user playlist or user track
            const isUserPlaylist = typeof state.playlistId === 'string' && state.playlistId.startsWith('user-playlist-');
            const isUserTrack = typeof state.playlistId === 'string' && state.playlistId.startsWith('user-track-');
            
            if (isUserPlaylist) {
                // Extract playlist ID from "user-playlist-123" format
                const playlistIdMatch = state.playlistId.match(/user-playlist-(\d+)/);
                if (playlistIdMatch) {
                    const playlistId = playlistIdMatch[1];
                    console.log(`🔄 Restoring user playlist ID: ${playlistId}`);
                    
                    // Fetch user playlist from API
                    try {
                        const response = await fetch(`/music/user/playlists/${playlistId}/tracks/`);
                        if (response.ok) {
                            const data = await response.json();
                            if (data.success && data.tracks.length > 0) {
                                playlist = {
                                    id: state.playlistId,
                                    name: data.playlist.name,
                                    tracks: data.tracks.map(track => ({
                                        id: track.id,
                                        title: track.title,
                                        artist: track.artist || 'Unknown Artist',
                                        album: track.album || '',
                                        album_cover: track.album_cover,
                                        file_url: track.file_url,
                                        duration: track.duration
                                    }))
                                };
                                console.log(`✅ Fetched user playlist: ${playlist.name} (${playlist.tracks.length} tracks)`);
                            }
                        }
                    } catch (error) {
                        console.error('❌ Failed to fetch user playlist:', error);
                    }
                }
            } else if (isUserTrack) {
                // User was playing a single track (not in a playlist)
                console.log(`ℹ️ Cannot restore single user track, skipping`);
                return false;
            } else {
                // Normal admin/global playlist
                playlist = this.playlists.find(p => p.id === state.playlistId);
            }
            
            if (!playlist || !playlist.tracks || playlist.tracks.length === 0) {
                console.log(`⚠️ Playlist not found or empty, cannot restore`);
                return false;
            }
            
            // Validate track index
            const trackIndex = Math.min(state.trackIndex || 0, playlist.tracks.length - 1);
            const track = playlist.tracks[trackIndex];
            if (!track) {
                return false;
            }
            
            console.log(`🎵 Restoring: ${track.title} (${Math.floor(state.currentTime)}s)`);
            
            // Restoring player state
            
            // Set flags
            this.isRestoringState = true;
            this.isLoadingTrack = true;
            // CHỈ set hasAutoPlayed nếu đang phát, nếu không phát thì để user click để auto-play
            if (state.isPlaying) {
                this.hasAutoPlayed = true;
            }
            
            // Restore playlist và track
            this.currentPlaylist = playlist;
            this.currentTrackIndex = trackIndex;
            this.playlistSelect.value = playlist.id;
            this.populateTrackList();
            
            // Update UI
            this.updateCurrentTrack();
            this.updateTrackListSelection();
            
            // Load audio với approach mới - sử dụng file_url từ API
            const fileUrl = track.file_url;
            
            // ✅ Use URL as-is from backend (Django already encodes it properly)
            this.audio.src = fileUrl;
            
            // Sử dụng Promise để handle audio loading với retry logic
            const waitForAudioReady = () => {
                return new Promise((resolve, reject) => {
                    let resolved = false;
                    
                    const cleanup = () => {
                        clearTimeout(timeout);
                        this.audio.removeEventListener('loadedmetadata', onMetadataLoaded);
                        this.audio.removeEventListener('canplay', onCanPlay);
                        this.audio.removeEventListener('error', onError);
                    };
                    
                    const checkAndResolve = () => {
                        // Đảm bảo duration đã có và hợp lệ
                        if (this.audio.duration && !isNaN(this.audio.duration) && this.audio.duration > 0) {
                            if (resolved) return;
                            resolved = true;
                            cleanup();
                            resolve();
                        }
                    };
                    
                    const onMetadataLoaded = () => {
                        // Metadata loaded
                        checkAndResolve();
                    };
                    
                    const onCanPlay = () => {
                        // Can play
                        // Delay nhỏ để chắc chắn duration đã được set
                        setTimeout(checkAndResolve, 50);
                    };
                    
                    const onError = (e) => {
                        if (resolved) return;
                        resolved = true;
                        cleanup();
                        console.error('🚨 Audio loading failed during restore');
                        reject(e);
                    };
                    
                    // Timeout sau 8 giây (tăng lên để audio có thời gian load)
                    const timeout = setTimeout(() => {
                        if (resolved) return;
                        resolved = true;
                        cleanup();
                        reject(new Error('Timeout waiting for audio'));
                    }, 8000);
                    
                    // Listen cả 2 events để đảm bảo
                    this.audio.addEventListener('loadedmetadata', onMetadataLoaded, { once: true });
                    this.audio.addEventListener('canplay', onCanPlay, { once: true });
                    this.audio.addEventListener('error', onError, { once: true });
                });
            };
            
            // Load audio
            this.audio.load();
            
            // Xử lý async với retry logic
            waitForAudioReady()
                .then(() => {
                    // Set thời gian phát với validation tốt hơn
                    if (state.currentTime && state.currentTime > 0) {
                        if (this.audio.duration && !isNaN(this.audio.duration) && this.audio.duration > 0) {
                            const targetTime = Math.min(state.currentTime, this.audio.duration - 0.5);
                            
                            try {
                                this.audio.currentTime = targetTime;
                                console.log(`✅ Restored to ${Math.floor(targetTime)}s`);
                            } catch (e) {
                                console.error('🚨 Failed to restore position');
                                // Retry sau 200ms
                                setTimeout(() => {
                                    try {
                                        this.audio.currentTime = targetTime;
                                        console.log(`✅ Restored to ${Math.floor(targetTime)}s (retry)`);
                                    } catch (e2) {
                                        console.error('🚨 Failed to restore position (retry)');
                                    }
                                }, 200);
                            }
                        }
                    }
                    
                    // Update UI
                    this.updateProgress();
                    this.updateDuration();
                    
                    // Resume playback nếu đang phát
                    if (state.isPlaying) {
                        this.userInteracted = true;
                        this.audio.play().catch(e => {
                            console.log('⚠️ Autoplay prevented');
                        });
                    }
                })
                .catch(error => {
                    console.error('🚨 Error restoring audio');
                    // ✅ Fallback: If audio restore fails, select first playlist
                    console.log('🔄 Audio restore failed, selecting first playlist');
                    if (this.playlists.length > 0) {
                        this.selectPlaylist(this.playlists[0].id);
                    }
                })
                .finally(() => {
                    // Reset flags sau 1 giây để đảm bảo mọi thứ ổn định
                    setTimeout(() => {
                        this.isRestoringState = false;
                        this.isLoadingTrack = false;
                        
                        // ✅ Update cached indicators after restore complete
                        this.updateTrackListOfflineIndicators();
                        console.log('🔄 Updated cached indicators after restore state');
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


    // Sleep Timer Methods
    setSleepTimer(minutes) {
        // Setting sleep timer
        
        // Cancel existing timer if any
        this.cancelSleepTimer();
        
        // Set new timer
        this.sleepTimerActive = true;
        this.sleepTimerEndTime = Date.now() + (minutes * 60 * 1000);
        
        // Update UI
        this.sleepTimerBtn.classList.add('active');
        
        // Show timer options buttons
        const timerOptions = document.querySelectorAll('.sleep-timer-option');
        timerOptions.forEach(opt => opt.style.display = 'none');
        
        // Show status
        this.sleepTimerStatus.classList.remove('hidden');
        
        // Start countdown
        this.sleepTimerInterval = setInterval(() => {
            this.updateTimerDisplay();
        }, 1000);
        
        // Update immediately
        this.updateTimerDisplay();
    }
    
    updateTimerDisplay() {
        if (!this.sleepTimerActive || !this.sleepTimerEndTime) return;
        
        const remaining = this.sleepTimerEndTime - Date.now();
        
        if (remaining <= 0) {
            // Time's up! Fade out and stop
            this.fadeOutAndStop();
            return;
        }
        
        // Calculate minutes and seconds
        const totalSeconds = Math.floor(remaining / 1000);
        const minutes = Math.floor(totalSeconds / 60);
        const seconds = totalSeconds % 60;
        
        // Update display
        this.timerRemaining.textContent = `Còn lại: ${minutes}:${seconds.toString().padStart(2, '0')}`;
        
        // If less than 10 seconds, add warning animation
        if (totalSeconds <= 10) {
            this.timerRemaining.style.animation = 'pulse 0.5s infinite';
        }
    }
    
    fadeOutAndStop() {
        // Sleep timer finished - fading out
        
        if (!this.audio.paused) {
            // Fade out over 3 seconds
            const startVolume = this.audio.volume;
            const fadeSteps = 30;
            const fadeInterval = 3000 / fadeSteps;
            const volumeStep = startVolume / fadeSteps;
            
            let currentStep = 0;
            const fadeIntervalId = setInterval(() => {
                currentStep++;
                const newVolume = Math.max(0, startVolume - (volumeStep * currentStep));
                this.audio.volume = newVolume;
                
                if (currentStep >= fadeSteps || newVolume <= 0) {
                    clearInterval(fadeIntervalId);
                    this.audio.pause();
                    this.audio.volume = this.volume; // Restore original volume
                    this.isPlaying = false;
                    this.updatePlayPauseButton();
                    // Music stopped by sleep timer
                }
            }, fadeInterval);
        }
        
        // Cancel timer
        this.cancelSleepTimer();
    }
    
    cancelSleepTimer() {
        // Cancelling sleep timer
        
        // Clear interval
        if (this.sleepTimerInterval) {
            clearInterval(this.sleepTimerInterval);
            this.sleepTimerInterval = null;
        }
        
        // Reset state
        this.sleepTimerActive = false;
        this.sleepTimerEndTime = null;
        
        // Update UI
        this.sleepTimerBtn.classList.remove('active');
        this.sleepTimerStatus.classList.add('hidden');
        
        // Show timer options again
        const timerOptions = document.querySelectorAll('.sleep-timer-option');
        timerOptions.forEach(opt => opt.style.display = 'block');
        
        // Reset timer display animation
        this.timerRemaining.style.animation = '';
        
        // ✅ Tự động đóng menu sau khi cancel
        if (this.sleepTimerMenu) {
            this.sleepTimerMenu.classList.add('hidden');
        }
    }

    // ✅ Mobile Optimization Methods
    initializeMobileOptimizations() {
        if (this.isMobile) {
            // Initializing mobile optimizations
            
            // ✅ Media Session API cho lock screen controls
            this.initializeMediaSession();
            
            // ✅ Audio preloading cho smooth transitions
            this.setupAudioPreloading();
            
            // ✅ Touch optimization
            this.optimizeTouchEvents();
            
            // ✅ Background playback support
            this.setupBackgroundPlayback();
        }
    }
    
    // ✅ Handle iOS Volume Restrictions
    handleIOSVolumeRestrictions() {
        if (!this.isIOS) return; // Chỉ xử lý cho iOS
        
        // iOS detected - disabling volume controls
        
        // Disable volume slider visually
        if (this.volumeFill && this.volumeHandle) {
            const volumeBar = this.volumeFill.parentElement;
            if (volumeBar) {
                volumeBar.style.opacity = '0.5';
                volumeBar.style.cursor = 'not-allowed';
                volumeBar.style.pointerEvents = 'none';
            }
            this.volumeHandle.style.pointerEvents = 'none';
        }
        
        // Disable mute button và thay đổi tooltip
        if (this.muteBtn) {
            this.muteBtn.style.opacity = '0.5';
            this.muteBtn.style.cursor = 'not-allowed';
            this.muteBtn.title = 'iOS: Sử dụng phím cứng để điều chỉnh âm lượng';
            
            // Override mute button click
            this.muteBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                e.preventDefault();
                this.showIOSVolumeMessage();
            });
        }
        
        // Add overlay click handler cho volume bar
        if (this.volumeFill && this.volumeHandle) {
            const volumeBar = this.volumeFill.parentElement;
            if (volumeBar) {
                // Re-enable pointer events để bắt click
                volumeBar.style.pointerEvents = 'auto';
                
                // Thêm overlay div trong suốt
                const overlay = document.createElement('div');
                overlay.style.cssText = `
                    position: absolute;
                    top: 0;
                    left: 0;
                    right: 0;
                    bottom: 0;
                    cursor: not-allowed;
                    z-index: 10;
                `;
                overlay.addEventListener('click', (e) => {
                    e.stopPropagation();
                    e.preventDefault();
                    this.showIOSVolumeMessage();
                });
                volumeBar.style.position = 'relative';
                volumeBar.appendChild(overlay);
            }
        }
    }
    
    // ✅ Show iOS volume message
    showIOSVolumeMessage() {
        // ✅ Chỉ show 1 lần khi mở popup, không spam
        if (this.hasShownIOSVolumeMessage) {
            // iOS volume message already shown
            return;
        }
        
        const message = `
🍎 iOS Limitation

Vui lòng sử dụng phím cứng bên cạnh iPhone/iPad để điều chỉnh âm lượng.

📱 Ứng dụng iOS chính thức với đầy đủ tính năng sắp ra mắt trên App Store!
        `.trim();
        
        this.showMessage(message, 'info');
        
        // ✅ Đánh dấu đã show, không show lại cho đến khi đóng/mở player
        this.hasShownIOSVolumeMessage = true;
    }
    
    // ✅ Initialize Offline Manager for caching music
    initializeOfflineManager() {
        if (typeof OfflineManager === 'undefined') {
            console.warn('⚠️ OfflineManager not loaded. Offline features disabled.');
            return;
        }
        
        try {
            this.offlineManager = new OfflineManager();
            // console.log('✅ Offline Manager initialized');
            
            // Listen to cache status updates
            window.addEventListener('cacheStatusUpdated', (event) => {
                const { size, percentage, sizeMB, maxMB } = event.detail;
                // console.log(`📦 Cache: ${sizeMB}MB / ${maxMB}MB (${percentage}%)`);
                
                // Update UI if cache status element exists
                this.updateOfflineCacheUI(event.detail);
            });
            
            // Listen to offline status changes
            window.addEventListener('offlineStatusChanged', (event) => {
                const { isOnline } = event.detail;
                console.log(isOnline ? '🟢 Online' : '🔴 Offline');
                
                // Update player UI for offline mode
                this.updateOfflineModeUI(isOnline);
            });
            
            // ✅ OPTIMIZED: Single Service Worker message listener (handles both navigator.serviceWorker and controller)
            navigator.serviceWorker.addEventListener('message', (event) => {
                if (event.data.type === 'trackCached') {
                    const { trackId } = event.data;
                    this.addTrackToCache(trackId);
                    console.log(`✅ Track ${trackId} cached via Service Worker`);
                    
                    // ✅ Auto-update cached indicators
                    this.updateTrackListOfflineIndicators();
                    
                    // ✅ Update cache status in settings if modal is open
                    const settingsModal = document.getElementById('settings-modal');
                    if (settingsModal && !settingsModal.classList.contains('hidden')) {
                        // Trigger cache status update
                        window.dispatchEvent(new CustomEvent('updateCacheStatus'));
                    }
                }
            });
            
            // ✅ FALLBACK: Auto-add tracks to cache after playing (only if auto-cache enabled)
            this.audio.addEventListener('loadeddata', () => {
                if (this.currentTrack && this.offlineManager && this.offlineManager.isAutoCacheEnabled()) {
                    this.addTrackToCache(this.currentTrack.id);
                }
            });
            
            // ✅ FALLBACK: Auto-add tracks when audio starts playing (only if auto-cache enabled)
            this.audio.addEventListener('play', () => {
                if (this.currentTrack && this.offlineManager && this.offlineManager.isAutoCacheEnabled()) {
                    setTimeout(() => {
                        this.addTrackToCache(this.currentTrack.id);
                    }, 1000); // Wait 1s for Service Worker to cache
                }
            });
            
            // Check and update cached tracks status after offline manager is ready
            setTimeout(async () => {
                if (this.currentPlaylist) {
                    await this.updateCachedTracksStatus();
                    this.updateTrackListOfflineIndicators();
                    console.log('🎵 Cached indicators updated after offline manager ready');
                }
            }, 1200);
            
        } catch (error) {
            console.error('❌ Failed to initialize Offline Manager:', error);
        }
    }
    
    // ✅ Update offline cache UI in settings
    updateOfflineCacheUI(cacheInfo) {
        const cacheStatus = document.getElementById('offline-cache-status');
        if (!cacheStatus) return;
        
        const { sizeMB, maxMB, percentage } = cacheInfo;
        const barColor = percentage < 70 ? '#11998e' : percentage < 90 ? '#f59e0b' : '#ef4444';
        
        cacheStatus.innerHTML = `
            <div class="cache-info" style="margin-bottom: 12px;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                    <span style="font-size: 13px; color: rgba(255,255,255,0.9);">
                        <i class="bi bi-cloud-download"></i> Offline Cache
                    </span>
                    <span style="font-size: 13px; font-weight: 600; color: rgba(255,255,255,1);">
                        ${sizeMB}MB / ${maxMB}MB
                    </span>
                </div>
                <div class="cache-progress" style="width: 100%; height: 6px; background: rgba(255,255,255,0.2); border-radius: 3px; overflow: hidden;">
                    <div class="cache-progress-bar" style="width: ${percentage}%; height: 100%; background: ${barColor}; transition: width 0.3s ease;"></div>
                </div>
                <div style="font-size: 11px; color: rgba(255,255,255,0.7); margin-top: 4px; text-align: center;">
                    ${percentage}% đã sử dụng
                </div>
            </div>
        `;
    }
    
    // ✅ Update offline mode UI indicators
    updateOfflineModeUI(isOnline) {
        // Add/remove offline class from player
        if (this.popup) {
            this.popup.classList.toggle('offline-mode', !isOnline);
        }
        
        // Update player title to show offline status
        const playerTitle = document.getElementById('player-title');
        if (playerTitle && !isOnline) {
            playerTitle.textContent = 'Music (Offline)';
        } else if (playerTitle) {
            playerTitle.textContent = 'Music';
        }
    }
    
    // ✅ Check and update which tracks are cached
    async updateCachedTracksStatus() {
        if (!this.offlineManager || !this.currentPlaylist) return;
        
        // Don't clear cachedTracks - merge with localStorage data
        const localStorageTracks = new Set();
        try {
            const stored = localStorage.getItem('dbp_cached_tracks');
            if (stored) {
                const trackIds = JSON.parse(stored);
                trackIds.forEach(id => localStorageTracks.add(id));
            }
        } catch (error) {
            console.error('Error loading from localStorage:', error);
        }
        
        // Check which tracks are actually cached by Service Worker
        const actuallyCached = new Set();
        for (const track of this.currentPlaylist.tracks) {
            const isCached = await this.offlineManager.isTrackCached(track.file_url);
            if (isCached) {
                actuallyCached.add(track.id);
            }
        }
        
        // Merge: keep localStorage tracks + add newly cached tracks
        this.cachedTracks = new Set([...localStorageTracks, ...actuallyCached]);
        
        // Update track list UI to show cached indicators
        this.updateTrackListOfflineIndicators();
    }
    
    // ✅ Load cached tracks from localStorage AND verify with Service Worker
    async loadCachedTracksFromStorage() {
        try {
            const stored = localStorage.getItem('dbp_cached_tracks');
            if (stored) {
                const trackIds = JSON.parse(stored);
                const verifiedTracks = new Set();
                
                // Verify each track is actually cached by Service Worker
                for (const trackId of trackIds) {
                    if (this.offlineManager) {
                        // Find track by ID
                        const track = this.currentPlaylist?.tracks?.find(t => t.id === trackId);
                        if (track) {
                            const isActuallyCached = await this.offlineManager.isTrackCached(track.file_url);
                            if (isActuallyCached) {
                                verifiedTracks.add(trackId);
                            } else {
                                console.log(`❌ Track ${trackId} not actually cached, removing from localStorage`);
                            }
                        }
                    } else {
                        // If offlineManager not ready, trust localStorage temporarily
                        verifiedTracks.add(trackId);
                    }
                }
                
                this.cachedTracks = verifiedTracks;
                // console.log('📦 Loaded verified cached tracks:', this.cachedTracks);
                
                // Update localStorage with verified tracks only
                this.saveCachedTracksToStorage();
                
                return true; // Success
            }
        } catch (error) {
            console.error('Error loading cached tracks:', error);
        }
        return false; // No data or error
    }
    
    // ✅ Save cached tracks to localStorage
    saveCachedTracksToStorage() {
        try {
            const trackIds = Array.from(this.cachedTracks);
            localStorage.setItem('dbp_cached_tracks', JSON.stringify(trackIds));
            // console.log('💾 Saved cached tracks to storage:', trackIds);
        } catch (error) {
            console.error('Error saving cached tracks:', error);
        }
    }
    
    // ✅ Add track to cache and save (with debounced UI update)
    addTrackToCache(trackId) {
        this.cachedTracks.add(trackId);
        this.saveCachedTracksToStorage();
        this.updateTrackListOfflineIndicatorsDebounced();
        // console.log(`✅ Added track ${trackId} to cache and saved`);
    }
    
    // ✅ Debounced version to prevent excessive DOM updates
    updateTrackListOfflineIndicatorsDebounced(delay = 100) {
        clearTimeout(this.updateIndicatorsDebounceTimer);
        this.updateIndicatorsDebounceTimer = setTimeout(() => {
            this.updateTrackListOfflineIndicators();
        }, delay);
    }
    
    // ✅ Update track list to show offline indicators (immediate, no debounce)
    updateTrackListOfflineIndicators() {
        // console.log('🔧 Updating track list offline indicators...');
        
        if (!this.trackList) {
            // console.log('❌ Track list not found');
            return;
        }
        
        const trackItems = this.trackList.querySelectorAll('.track-item');
        // console.log(`🎵 Found ${trackItems.length} track items`);
        
        trackItems.forEach((item, index) => {
            const trackId = parseInt(item.dataset.trackId);
            const isCached = this.cachedTracks.has(trackId);
            
            // console.log(`Track ${index}: ID=${trackId}, Cached=${isCached}`);
            
            // Add/remove cached indicator
            let indicator = item.querySelector('.offline-indicator');
            if (isCached && !indicator) {
                indicator = document.createElement('span');
                indicator.className = 'offline-indicator';
                indicator.innerHTML = '<i class="bi bi-cloud-check-fill" title="Đã cache offline"></i>';
                indicator.style.cssText = 'color: #11998e !important; margin-left: 8px !important; font-size: 14px !important; display: inline-block !important; visibility: visible !important; opacity: 1 !important; position: relative !important; z-index: 999 !important;';
                
                const artistElement = item.querySelector('.track-item-artist');
                if (artistElement) {
                    artistElement.appendChild(indicator);
                    // console.log(`✅ Added indicator to track ${trackId}`);
                } else {
                    // console.log(`❌ Artist element not found for track ${trackId}`);
                }
            } else if (!isCached && indicator) {
                indicator.remove();
                // console.log(`🗑️ Removed indicator from track ${trackId}`);
            }
        });
        
        // console.log('✅ Track list indicators updated');
    }
    
    // ✅ Preload track for offline (called when track is played)
    async preloadTrackForOffline(track) {
        if (!this.offlineManager || !track) return;
        
        // ✅ Check auto-cache setting - chỉ cache nếu user bật
        if (!this.offlineManager.isAutoCacheEnabled()) {
            console.log(`⏸️ Auto-cache disabled, skipping track: ${track.title}`);
            return;
        }
        
        // Auto-cache khi nghe (Service Worker sẽ tự động cache)
        // Không cần manually preload, Service Worker sẽ làm
        
        try {
            const isCached = await this.offlineManager.isTrackCached(track.file_url);
            if (!isCached) {
                console.log(`📥 Auto-caching track: ${track.title}`);
                // Service Worker sẽ tự động cache khi fetch
                // Sau khi cache xong, update UI (addTrackToCache already updates UI)
                setTimeout(() => {
                    this.addTrackToCache(track.id);
                }, 2000); // Wait 2s for cache to complete
            } else {
                console.log(`✅ Track already cached: ${track.title}`);
                // addTrackToCache already calls updateTrackListOfflineIndicatorsDebounced
                this.addTrackToCache(track.id);
            }
        } catch (error) {
            console.error('Error checking cache status:', error);
        }
    }
    
    initializeMediaSession() {
        if ('mediaSession' in navigator) {
            // Setting up Media Session API
            
            navigator.mediaSession.setActionHandler('play', () => {
                // Media Session: Play action
                // ✅ Gọi togglePlayPause thay vì trực tiếp audio.play()
                // để đảm bảo state được update đúng
                if (!this.isPlaying) {
                    this.userInteracted = true;
                    this.togglePlayPause();
                }
            });
            
            navigator.mediaSession.setActionHandler('pause', () => {
                // Media Session: Pause action
                // ✅ Gọi togglePlayPause thay vì trực tiếp audio.pause()
                // để đảm bảo state được update đúng
                if (this.isPlaying) {
                    this.togglePlayPause();
                }
            });
            
            navigator.mediaSession.setActionHandler('previoustrack', () => {
                // Media Session: Previous track
                this.previousTrack();
            });
            
            navigator.mediaSession.setActionHandler('nexttrack', () => {
                // Media Session: Next track
                this.nextTrack();
            });
            
            navigator.mediaSession.setActionHandler('seekbackward', (details) => {
                // Media Session: Seek backward
                this.seekBackward(details.seekOffset || 10);
            });
            
            navigator.mediaSession.setActionHandler('seekforward', (details) => {
                // Media Session: Seek forward
                this.seekForward(details.seekOffset || 10);
            });
            
            navigator.mediaSession.setActionHandler('seekto', (details) => {
                if (details.seekTime !== undefined) {
                    // Media Session: Seek to
                    this.seekTo(details.seekTime);
                }
            });
            
            navigator.mediaSession.setActionHandler('stop', () => {
                // Media Session: Stop action
                this.audio.pause();
                this.audio.currentTime = 0;
            });
        }
    }
    
    updateMediaSessionMetadata() {
        if (!('mediaSession' in navigator)) return;
        
        if (this.currentPlaylist && this.currentPlaylist.tracks[this.currentTrackIndex]) {
            const track = this.currentPlaylist.tracks[this.currentTrackIndex];
            
            try {
                // Use album cover if available, otherwise use default
                const baseArtwork = track.album_cover || (this.currentPlaylist && this.currentPlaylist.cover_image) || '/static/music_player/images/album-art.png';
                const bust = `v=${Date.now()}`;
                const artworkUrl = baseArtwork.includes('?') ? `${baseArtwork}&${bust}` : `${baseArtwork}?${bust}`;
                const artworkType = baseArtwork.endsWith('.png') ? 'image/png' : 'image/jpeg';
                const albumName = track.album || (this.currentPlaylist && this.currentPlaylist.name) || '';
                
                navigator.mediaSession.metadata = new MediaMetadata({
                    title: track.title,
                    artist: track.artist || 'Unknown Artist',
                    album: albumName,
                    artwork: [
                        { src: artworkUrl, sizes: '96x96', type: artworkType },
                        { src: artworkUrl, sizes: '128x128', type: artworkType },
                        { src: artworkUrl, sizes: '192x192', type: artworkType },
                        { src: artworkUrl, sizes: '256x256', type: artworkType },
                        { src: artworkUrl, sizes: '384x384', type: artworkType },
                        { src: artworkUrl, sizes: '512x512', type: artworkType }
                    ]
                });
                
                // ✅ Update playback state
                navigator.mediaSession.playbackState = this.isPlaying ? 'playing' : 'paused';
                
                // ✅ Update position state (quan trọng cho lock screen!)
                if (this.audio.duration && !isNaN(this.audio.duration)) {
                    navigator.mediaSession.setPositionState({
                        duration: this.audio.duration,
                        playbackRate: this.audio.playbackRate,
                        position: this.audio.currentTime
                    });
                }
            } catch (error) {
                console.error('Error updating Media Session metadata:', error);
            }
        }
    }
    
    setupAudioPreloading() {
        // Setting up audio preloading
        
        // Preload next và previous tracks
        this.audio.addEventListener('loadedmetadata', () => {
            this.preloadAdjacentTracks();
        });
        
        this.audio.addEventListener('canplaythrough', () => {
            this.preloadAdjacentTracks();
        });
    }
    
    async preloadAdjacentTracks() {
        if (!this.currentPlaylist || this.currentPlaylist.tracks.length <= 1) return;
        
        try {
            // ✅ Cleanup old preloaded tracks (giữ tối đa 5 tracks để tránh memory leak)
            if (this.preloadedTracks.size > 5) {
                const tracksToKeep = new Set();
                
                // Get IDs of current, next, and previous tracks
                const currentTrack = this.currentPlaylist.tracks[this.currentTrackIndex];
                if (currentTrack) tracksToKeep.add(currentTrack.id);
                
                const nextIndex = this.getNextTrackIndex();
                const nextTrack = this.currentPlaylist.tracks[nextIndex];
                if (nextTrack) tracksToKeep.add(nextTrack.id);
                
                const prevIndex = this.getPreviousTrackIndex();
                const prevTrack = this.currentPlaylist.tracks[prevIndex];
                if (prevTrack) tracksToKeep.add(prevTrack.id);
                
                // Remove tracks that are not in tracksToKeep
                for (const [trackId, audioElement] of this.preloadedTracks.entries()) {
                    if (!tracksToKeep.has(trackId)) {
                        // ✅ Cleanup audio element
                        audioElement.src = '';
                        audioElement.load(); // Free memory
                        this.preloadedTracks.delete(trackId);
                        // Cleaned up preloaded track
                    }
                }
            }
            
            // Preload next track
            const nextIndex = this.getNextTrackIndex();
            if (nextIndex !== this.currentTrackIndex) {
                const nextTrack = this.currentPlaylist.tracks[nextIndex];
                if (nextTrack && !this.preloadedTracks.has(nextTrack.id)) {
                    // Preloading next track
                    const audio = new Audio();
                    audio.preload = 'metadata';
                    
                    // ✅ Use URL as-is from backend (Django already encodes it properly)
                    audio.src = nextTrack.file_url;
                    this.preloadedTracks.set(nextTrack.id, audio);
                }
            }
            
            // Preload previous track
            const prevIndex = this.getPreviousTrackIndex();
            if (prevIndex !== this.currentTrackIndex) {
                const prevTrack = this.currentPlaylist.tracks[prevIndex];
                if (prevTrack && !this.preloadedTracks.has(prevTrack.id)) {
                    // Preloading previous track
                    const audio = new Audio();
                    audio.preload = 'metadata';
                    
                    // ✅ Use URL as-is from backend (Django already encodes it properly)
                    audio.src = prevTrack.file_url;
                    this.preloadedTracks.set(prevTrack.id, audio);
                }
            }
        } catch (error) {
            console.error('Error preloading tracks:', error);
        }
    }
    
    optimizeTouchEvents() {
        // Optimizing touch events
        
        // Prevent double-tap zoom
        let lastTouchEnd = 0;
        document.addEventListener('touchend', (event) => {
            const now = (new Date()).getTime();
            if (now - lastTouchEnd <= 300) {
                event.preventDefault();
            }
            lastTouchEnd = now;
        }, false);
        
        // Optimize touch events for controls
        const controlButtons = document.querySelectorAll('.control-btn');
        controlButtons.forEach(btn => {
            btn.addEventListener('touchstart', (e) => {
                e.preventDefault();
                btn.style.transform = 'scale(0.95)';
            });
            
            btn.addEventListener('touchend', (e) => {
                e.preventDefault();
                btn.style.transform = 'scale(1)';
                btn.click();
            });
        });
    }
    
    setupBackgroundPlayback() {
        // Setting up background playback
        
        // Handle page visibility changes
        document.addEventListener('visibilitychange', () => {
            if (document.hidden) {
                // Page hidden - maintaining playback
                // Keep playing in background
            } else {
                // Page visible - updating UI
                this.updateMediaSessionMetadata();
            }
        });
        
        // Handle audio focus on mobile
        this.audio.addEventListener('pause', () => {
            if (this.isPlaying && document.hidden) {
                // Resume if paused due to page visibility
                setTimeout(() => {
                    if (this.isPlaying) {
                        this.audio.play().catch(() => {
                            // Play failed - handle silently
                        });
                    }
                }, 100);
            }
        });
    }
    
    seekBackward(seconds = 10) {
        this.audio.currentTime = Math.max(0, this.audio.currentTime - seconds);
    }
    
    seekForward(seconds = 10) {
        this.audio.currentTime = Math.min(this.audio.duration, this.audio.currentTime + seconds);
    }
    
    seekTo(time) {
        // ✅ Validate time value trước khi set
        if (typeof time !== 'number' || !isFinite(time) || time < 0) {
            // Invalid time value for seekTo
            return;
        }
        
        // ✅ Ensure time is within valid range
        const maxTime = this.audio.duration || 0;
        const validTime = Math.min(Math.max(time, 0), maxTime);
        
        this.audio.currentTime = validTime;
    }
    
    // ✅ Helper method cho random index (tránh duplicate code)
    getRandomTrackIndex() {
        if (!this.currentPlaylist || this.currentPlaylist.tracks.length <= 1) {
            return this.currentTrackIndex;
        }
        
        let randomIndex;
        do {
            randomIndex = Math.floor(Math.random() * this.currentPlaylist.tracks.length);
        } while (randomIndex === this.currentTrackIndex);
        return randomIndex;
    }
    
    // ✅ Helper methods cho track navigation
    getNextTrackIndex() {
        if (!this.currentPlaylist) return 0;
        
        if (this.isShuffled) {
            return this.getRandomTrackIndex();
        }
        
        // Normal mode: theo thứ tự
        if (this.currentTrackIndex < this.currentPlaylist.tracks.length - 1) {
            return this.currentTrackIndex + 1;
        } else if (this.repeatMode === 'all') {
            return 0;
        }
        return this.currentTrackIndex; // Stay on current if no repeat
    }
    
    getPreviousTrackIndex() {
        if (!this.currentPlaylist) return 0;
        
        if (this.isShuffled) {
            return this.getRandomTrackIndex();
        }
        
        // Normal mode: theo thứ tự
        if (this.currentTrackIndex > 0) {
            return this.currentTrackIndex - 1;
        } else if (this.repeatMode === 'all') {
            return this.currentPlaylist.tracks.length - 1;
        }
        return this.currentTrackIndex; // Stay on current if no repeat
    }
    
    // ✅ Helper methods để tối ưu battery
    updateUserActivity() {
        this.lastUserActivity = Date.now();
    }
    
    // ❌ REMOVED: isUserActive() - không cần nữa vì đã remove auto-refresh interval
    
    // ✅ Utility function để escape HTML và tránh XSS
    escapeHtml(text) {
        if (!text) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    // ========================================
    // ✅ PLAY TRACKING METHODS
    // ========================================
    
    startPlayTracking() {
        // Nếu đã có interval rồi, không tạo mới
        if (this.playTrackingInterval) {
            return;
        }
        
        // Reset tracking cho track mới
        this.currentTrackStartTime = Date.now();
        this.currentTrackListenDuration = 0;
        this.hasRecordedPlay = false;
        
        // Update listen duration mỗi giây
        this.playTrackingInterval = setInterval(() => {
            if (this.isPlaying && !this.audio.paused) {
                this.currentTrackListenDuration += 1;
                
                // Kiểm tra nếu đã nghe đủ để record play
                const track = this.currentPlaylist?.tracks[this.currentTrackIndex];
                if (track && !this.hasRecordedPlay) {
                    const minDuration = Math.min(30, track.duration * 0.5);
                    
                    if (this.currentTrackListenDuration >= minDuration) {
                        // Đã nghe đủ, gửi record play ngay
                        this.recordCurrentTrackPlay();
                    }
                }
            }
        }, 1000);
    }
    
    stopPlayTracking() {
        if (this.playTrackingInterval) {
            clearInterval(this.playTrackingInterval);
            this.playTrackingInterval = null;
        }
    }
    
    async recordCurrentTrackPlay() {
        // Nếu đã record rồi hoặc không có track, skip
        if (this.hasRecordedPlay || !this.currentPlaylist || !this.currentPlaylist.tracks[this.currentTrackIndex]) {
            return;
        }
        
        const track = this.currentPlaylist.tracks[this.currentTrackIndex];
        
        // Kiểm tra đã nghe đủ thời gian chưa
        const minDuration = Math.min(30, track.duration * 0.5);
        if (this.currentTrackListenDuration < minDuration) {
            return;
        }
        
        // Đánh dấu đã record để tránh gửi nhiều lần
        this.hasRecordedPlay = true;
        
        // Gửi lên server
        try {
            const csrfToken = this.getCSRFToken();
            
            const response = await fetch('/music/stats/record-play/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken
                },
                credentials: 'same-origin',
                body: JSON.stringify({
                    track_id: track.id,
                    track_type: this.currentPlaylist.type || 'global',
                    listen_duration: Math.floor(this.currentTrackListenDuration)
                })
            });
            
            const data = await response.json();
            
            if (data.success && data.counted) {
                // Cập nhật play_count trong UI nếu cần
                if (data.play_count !== undefined) {
                    track.play_count = data.play_count;
                    
                    // Update display if this is current track
                    if (this.playCountNumber && this.currentPlaylist && this.currentPlaylist.tracks[this.currentTrackIndex] === track) {
                        this.playCountNumber.textContent = data.play_count;
                    }
                }
            }
        } catch (error) {
            console.error('Error recording play:', error);
        }
    }

    destroy() {
        // ✅ Record play của track hiện tại trước khi destroy
        this.recordCurrentTrackPlay();
        
        // ✅ Stop tracking
        this.stopPlayTracking();
        
        // Save state trước khi destroy (immediate)
        this.savePlayerStateImmediate();
        
        // ✅ Cleanup debounce timers
        if (this.saveStateDebounceTimer) {
            clearTimeout(this.saveStateDebounceTimer);
        }
        if (this.refreshPlaylistsDebounceTimer) {
            clearTimeout(this.refreshPlaylistsDebounceTimer);
        }
        
        // ✅ Cleanup animation frames
        if (this.dragAnimationFrame) {
            cancelAnimationFrame(this.dragAnimationFrame);
        }
        if (this.volumeDragAnimationFrame) {
            cancelAnimationFrame(this.volumeDragAnimationFrame);
        }
        
        // Cleanup intervals
        if (this.sleepTimerInterval) {
            clearInterval(this.sleepTimerInterval);
        }
        
        // ✅ Cleanup preloaded tracks để free memory
        if (this.preloadedTracks) {
            for (const [trackId, audioElement] of this.preloadedTracks.entries()) {
                audioElement.src = '';
                audioElement.load();
            }
            this.preloadedTracks.clear();
            // Cleaned up all preloaded tracks
        }
        
        // ✅ Cleanup caches
        if (this.formatTimeCache) {
            this.formatTimeCache.clear();
        }
        
        // ✅ Cleanup audio element (chỉ pause, không reset src để giữ state)
        if (this.audio) {
            this.audio.pause();
            // KHÔNG reset src để giữ state cho restore
            // this.audio.src = '';
            // this.audio.load();
        }
    }
}

// Initialize music player when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.musicPlayer = new MusicPlayer();
    // ✅ REMOVED: Duplicate settings fetch - batched call đã load settings rồi
    // Listening lock và low power mode được apply trong loadInitialData() method
});

// Cleanup when page unloads (chỉ save state, không destroy audio)
window.addEventListener('beforeunload', () => {
    if (window.musicPlayer) {
        // Chỉ save state, không destroy audio để giữ state
        window.musicPlayer.savePlayerStateImmediate();
    }
});

