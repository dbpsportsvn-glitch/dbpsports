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
        this.hasOpenedPlayer = false; // ✅ Flag để track lần đầu mở player
        
        // Drag and drop variables
        this.isDragging = false;
        this.dragOffset = { x: 0, y: 0 };
        this.isDraggingVolume = false; // Flag để track volume dragging
        
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
        
        this.initializeElements();
        this.bindEvents();
        this.loadSettings();
        this.loadPlaylists();
        
        // ✅ Initialize mobile optimizations
        this.initializeMobileOptimizations();
        
        // ✅ Handle iOS volume restrictions
        this.handleIOSVolumeRestrictions();
        
        // ❌ REMOVED: Auto refresh interval - không cần thiết và tốn pin
        // Playlists sẽ tự động refresh khi:
        // 1. User mở player (togglePlayer)
        // 2. User switch sang tab Playlists
        // 3. User manually click refresh (nếu cần thêm nút refresh sau này)
        
        // ✅ Track user activity (vẫn giữ để track interaction)
        this.lastUserActivity = Date.now();
        document.addEventListener('click', () => this.updateUserActivity());
        document.addEventListener('keydown', () => this.updateUserActivity());
        document.addEventListener('touchstart', () => this.updateUserActivity());
        
        // Lưu state trước khi chuyển trang (immediate - không debounce)
        window.addEventListener('beforeunload', () => {
            if (!this.isRestoringState) {
                this.savePlayerStateImmediate();
            }
        });
        
        // Handle mobile browser pause/resume - DISABLED (user wants continuous playback)
        document.addEventListener('visibilitychange', () => {
            if (document.hidden) {
                // Page bị ẩn - KHÔNG pause audio trên mobile (user muốn tiếp tục phát)
                console.log('📱 Page hidden - keeping music playing');
            } else {
                // Page hiện lại
                console.log('📱 Page visible again');
            }
        });
        
        // Handle mobile app switching - DISABLED (user wants continuous playback)
        window.addEventListener('blur', () => {
            console.log('📱 App switched - keeping music playing');
        });
        
        // ❌ REMOVED: Save state interval - đã có debounce trong savePlayerState()
        // State sẽ tự động save khi:
        // 1. Play/Pause
        // 2. Change track
        // 3. Seek position
        // 4. Change playlist
        // 5. Before unload
        // Không cần interval polling nữa!
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
        
        // Sleep timer elements
        this.sleepTimerBtn = document.getElementById('sleep-timer-btn');
        this.sleepTimerMenu = document.getElementById('sleep-timer-menu');
        this.sleepTimerStatus = document.getElementById('sleep-timer-status');
        this.timerRemaining = document.getElementById('timer-remaining');
        this.cancelTimerBtn = document.getElementById('cancel-timer-btn');
        
        // ✅ Keyboard shortcuts button
        this.keyboardShortcutsBtn = document.getElementById('keyboard-shortcuts-btn');
        
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
        // ✅ Null guards cho các elements bắt buộc
        if (!this.toggle || !this.closeBtn || !this.popup || !this.audio) {
            console.error('Missing required DOM elements for music player');
            return;
        }
        
        // Toggle events
        this.toggle.addEventListener('click', () => this.togglePlayer());
        this.closeBtn.addEventListener('click', () => this.togglePlayer());
        
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
            // Touch support for mobile
            this.progressBar.addEventListener('touchstart', (e) => {
                e.preventDefault();
                this.seekToPosition(e.touches[0]);
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
                    console.log('Clicked outside player, closing...');
                    this.togglePlayer();
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
                this.sleepTimerMenu.classList.toggle('hidden');
            });
        }
        
        // Sleep timer options
        const timerOptions = document.querySelectorAll('.sleep-timer-option');
        timerOptions.forEach(option => {
            option.addEventListener('click', (e) => {
                e.stopPropagation();
                const minutes = parseInt(option.getAttribute('data-minutes'));
                this.setSleepTimer(minutes);
                this.sleepTimerMenu.classList.add('hidden');
            });
        });
        
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
    
    initPlaylistTypeToggle() {
        const toggleButtons = document.querySelectorAll('.playlist-type-btn');
        const adminGrid = document.getElementById('playlist-grid');
        const userGrid = document.getElementById('user-playlist-grid');
        
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
                    // ✅ Force refresh admin playlists khi click vào Admin Playlists
                    console.log('🔄 Switching to Admin Playlists - force refreshing...');
                    this.refreshPlaylists().then(() => {
                        // Restore active state for admin playlists
                        this.restorePlaylistActiveState();
                    });
                } else if (type === 'personal') {
                    adminGrid.classList.add('hidden');
                    userGrid.classList.remove('hidden');
                    // Load user playlists
                    this.loadUserPlaylistsInMainPlayer().then(() => {
                        // Restore active state after loading
                        this.restorePlaylistActiveState();
                    });
                }
            });
        });
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
    
    async loadUserPlaylistsInMainPlayer() {
        const userGrid = document.getElementById('user-playlist-grid');
        if (!userGrid) return;
        
        try {
            const response = await fetch('/music/user/playlists/');
            
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
                        return `
                            <div class="playlist-card" data-playlist-id="user-${playlist.id}" onclick="musicPlayer.loadUserPlaylist(${playlist.id})">
                                <div class="playlist-card-icon">
                                    <i class="bi bi-vinyl-fill"></i>
                                </div>
                                <div class="playlist-card-name">${escapedName}</div>
                                <div class="playlist-card-count">${playlist.tracks_count} bài hát</div>
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
                
                console.log('✅ Loaded user playlist:', data.playlist.name);
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
                    
                    // ✅ Auto-refresh playlists khi switch sang tab Playlists
                    if (tabName === 'playlists') {
                        console.log('🎵 Refreshing playlists...');
                        this.refreshPlaylists();
                    }
                } else {
                    console.error('Tab content not found:', `tab-${tabName}`);
                }
            });
        });
    }

    async loadPlaylists() {
        try {
            const response = await fetch(`/music/api/?t=${Date.now()}`, {
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
        // ✅ Force refresh playlists from server với cache-busting mạnh
        try {
            console.log('🔄 Force refreshing playlists...');
            
            // ✅ Thêm random parameter để đảm bảo không cache
            const timestamp = Date.now();
            const random = Math.random().toString(36).substring(7);
            
            const response = await fetch(`/music/api/?t=${timestamp}&r=${random}&force=1`, {
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
                    }
                }
                
                console.log('✅ Playlists refreshed successfully:', this.playlists.length, 'playlists');
                
                // ✅ Log chi tiết để debug
                this.playlists.forEach((playlist, index) => {
                    console.log(`  ${index + 1}. ${playlist.name} (${playlist.tracks_count} tracks)`);
                });
            } else {
                console.error('❌ Failed to refresh playlists:', data.error);
            }
        } catch (error) {
            console.error('❌ Error refreshing playlists:', error);
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
        
        if (this.playlists.length === 0) {
            playlistGrid.innerHTML = `
                <div class="empty-state">
                    <i class="bi bi-collection-play"></i>
                    <p>Chưa có playlist nào</p>
                </div>
            `;
            return;
        }
        
        // ✅ Tối ưu: Chỉ update khi cần thiết
        const existingCards = playlistGrid.querySelectorAll('.playlist-card');
        const existingIds = new Set(Array.from(existingCards).map(c => parseInt(c.dataset.playlistId)));
        const newIds = new Set(this.playlists.map(p => p.id));
        
        // ✅ Check nếu danh sách không đổi, chỉ update active state
        const listsMatch = existingIds.size === newIds.size && 
                          Array.from(existingIds).every(id => newIds.has(id));
        
        if (listsMatch) {
            // Chỉ update active state và track count
            existingCards.forEach(card => {
                const playlistId = parseInt(card.dataset.playlistId);
                const playlist = this.playlists.find(p => p.id === playlistId);
                
                if (playlist) {
                    // Update active state
                    if (this.currentPlaylist && this.currentPlaylist.id === playlist.id) {
                        card.classList.add('active');
                    } else {
                        card.classList.remove('active');
                    }
                    
                    // Update track count nếu thay đổi
                    const countElement = card.querySelector('.playlist-card-count');
                    const newCount = `${playlist.tracks_count || playlist.tracks?.length || 0} bài hát`;
                    if (countElement && countElement.textContent !== newCount) {
                        countElement.textContent = newCount;
                    }
                }
            });
            return;
        }
        
        // ✅ Nếu danh sách thay đổi, re-render toàn bộ
        playlistGrid.innerHTML = '';
        this.playlists.forEach(playlist => {
            const card = document.createElement('div');
            card.className = 'playlist-card';
            if (this.currentPlaylist && this.currentPlaylist.id === playlist.id) {
                card.classList.add('active');
            }
            card.dataset.playlistId = playlist.id;
            
            // ✅ Escape HTML để tránh XSS
            const escapedName = this.escapeHtml(playlist.name);
            card.innerHTML = `
                <i class="bi bi-vinyl-fill playlist-card-icon"></i>
                <div class="playlist-card-name" title="${escapedName}">${escapedName}</div>
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
            console.log('Auto-playing track 0 after playlist selection');
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
            
            // ✅ Escape HTML để tránh XSS
            const escapedTitle = this.escapeHtml(track.title);
            const escapedArtist = this.escapeHtml(track.artist);
            const escapedDuration = this.escapeHtml(track.duration_formatted);
            
            trackItem.innerHTML = `
                <div class="track-item-number">${index + 1}</div>
                <i class="bi bi-music-note-beamed track-item-icon"></i>
                <div class="track-item-info">
                    <div class="track-item-title">${escapedTitle}</div>
                    <div class="track-item-artist">${escapedArtist}</div>
                </div>
                <div class="track-item-duration">${escapedDuration}</div>
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
        console.log(`[${type.toUpperCase()}] ${message}`);
        
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
        
        const track = this.currentPlaylist.tracks[index];
        
        // Kiểm tra xem có đang phát cùng track này không
        const currentSrc = this.audio.src;
        const isSameTrack = this.currentTrackIndex === index && currentSrc && currentSrc.includes(track.file_url);
        
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
        
        // Sử dụng file_url từ API (đã có đường dẫn đầy đủ)
        const fileUrl = track.file_url;
        
        // Load track mới
        this.audio.src = fileUrl;
        this.audio.load();
        
        // ✅ Timeout protection
        const loadTimeout = setTimeout(() => {
            if (this.isLoadingTrack) {
                console.warn('⏰ Track load timeout:', track.title);
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
                    console.log('Autoplay prevented:', e.message);
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
                console.log('🔄 Retrying track load...');
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
        const clickX = (event.clientX || event.pageX) - rect.left;
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
            
            this.setVolumePercent(percent);
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
        
        console.log('🎚️ Volume set:', (percent * 100).toFixed(0) + '%', 'Muted:', this.isMuted);
    }

    toggleMute() {
        this.isMuted = !this.isMuted;
        this.audio.volume = this.isMuted ? 0 : this.volume;
        console.log('🔇 Mute toggled:', this.isMuted, 'Volume:', this.audio.volume);
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
        const wasHidden = this.popup.classList.contains('hidden');
        this.popup.classList.toggle('hidden');
        
        // Nếu đang mở player (từ hidden → visible)
        if (wasHidden) {
            console.log('🎵 Opening player - refreshing playlists...');
            this.refreshPlaylists();
            
            // ✅ Reset iOS volume message flag khi mở player
            // (Chỉ show khi user tự nhấn vào volume controls, không auto-show)
            if (this.isIOS) {
                this.hasShownIOSVolumeMessage = false;
                console.log('🍎 iOS volume message flag reset - will show on first volume interaction');
            }
            
            // ✅ Auto-play khi mở lần đầu tiên
            if (!this.hasOpenedPlayer) {
                this.hasOpenedPlayer = true;
                this.userInteracted = true; // Mark user has interacted
                
                // Delay một chút để đảm bảo playlists đã load
                setTimeout(() => {
                    // Nếu chưa phát nhạc và có playlist available
                    if (!this.isPlaying && this.currentPlaylist && this.currentPlaylist.tracks.length > 0) {
                        console.log('🎵 Auto-playing on first open...');
                        this.playTrack(this.currentTrackIndex);
                    }
                }, 300);
            }
        } else {
            // ✅ Đang đóng player
            console.log('🎵 Closing player');
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
    
    // ✅ Show keyboard shortcuts modal
    showKeyboardShortcuts() {
        const modal = document.createElement('div');
        modal.id = 'keyboard-shortcuts-modal';
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
        
        modal.innerHTML = `
            <div style="
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                border-radius: 20px;
                padding: 30px;
                max-width: 600px;
                max-height: 80vh;
                overflow-y: auto;
                box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5);
            ">
                <h3 style="color: white; margin: 0 0 20px 0; font-size: 24px; display: flex; align-items: center; gap: 10px;">
                    ⌨️ Phím tắt Music Player
                </h3>
                ${iosWarning}
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px; color: white;">
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
                <button onclick="this.closest('#keyboard-shortcuts-modal').remove()" style="
                    margin-top: 20px;
                    padding: 10px 20px;
                    background: rgba(255, 255, 255, 0.2);
                    border: 1px solid rgba(255, 255, 255, 0.3);
                    border-radius: 8px;
                    color: white;
                    font-weight: 600;
                    cursor: pointer;
                    width: 100%;
                    transition: all 0.2s;
                " onmouseover="this.style.background='rgba(255, 255, 255, 0.3)'" onmouseout="this.style.background='rgba(255, 255, 255, 0.2)'">
                    Đóng (Esc)
                </button>
            </div>
        `;
        
        // Close on click outside
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                modal.remove();
            }
        });
        
        // Close on Escape
        const escapeHandler = (e) => {
            if (e.code === 'Escape') {
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
                            console.log('✅ Audio ready with duration:', this.formatTime(this.audio.duration));
                            resolve();
                        }
                    };
                    
                    const onMetadataLoaded = () => {
                        console.log('📊 Metadata loaded, duration:', this.audio.duration);
                        checkAndResolve();
                    };
                    
                    const onCanPlay = () => {
                        console.log('▶️ Can play, duration:', this.audio.duration);
                        // Delay nhỏ để chắc chắn duration đã được set
                        setTimeout(checkAndResolve, 50);
                    };
                    
                    const onError = (e) => {
                        if (resolved) return;
                        resolved = true;
                        cleanup();
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
                    // Audio đã sẵn sàng VÀ có duration
                    console.log('🎵 Audio ready for restore, attempting to set position...');
                    
                    // Set thời gian phát với validation tốt hơn
                    if (state.currentTime && state.currentTime > 0) {
                        if (this.audio.duration && !isNaN(this.audio.duration) && this.audio.duration > 0) {
                            const targetTime = Math.min(state.currentTime, this.audio.duration - 0.5);
                            
                            try {
                                this.audio.currentTime = targetTime;
                                console.log('✅ Restored position:', this.formatTime(targetTime), '/', this.formatTime(this.audio.duration));
                            } catch (e) {
                                console.error('❌ Failed to set currentTime:', e);
                                // Retry sau 200ms
                                setTimeout(() => {
                                    try {
                                        this.audio.currentTime = targetTime;
                                        console.log('✅ Restored position (retry):', this.formatTime(targetTime));
                                    } catch (e2) {
                                        console.error('❌ Failed to set currentTime (retry):', e2);
                                    }
                                }, 200);
                            }
                        } else {
                            console.warn('⚠️ Duration not valid:', this.audio.duration, '- cannot restore position');
                        }
                    } else {
                        console.log('ℹ️ No currentTime to restore (starting from beginning)');
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
                    console.error('❌ Error restoring audio:', error);
                })
                .finally(() => {
                    // Reset flags sau 1 giây để đảm bảo mọi thứ ổn định
                    setTimeout(() => {
                        this.isRestoringState = false;
                        this.isLoadingTrack = false;
                        console.log('🏁 Restore completed');
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
        console.log(`⏰ Setting sleep timer for ${minutes} minutes`);
        
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
        console.log('⏰ Sleep timer finished - fading out...');
        
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
                    console.log('⏰ Music stopped by sleep timer');
                }
            }, fadeInterval);
        }
        
        // Cancel timer
        this.cancelSleepTimer();
    }
    
    cancelSleepTimer() {
        console.log('⏰ Cancelling sleep timer');
        
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
    }

    // ✅ Mobile Optimization Methods
    initializeMobileOptimizations() {
        if (this.isMobile) {
            console.log('📱 Initializing mobile optimizations...');
            
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
        
        console.log('🍎 iOS detected - disabling volume controls (system limitation)');
        
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
            console.log('🍎 iOS volume message already shown in this session');
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
    
    initializeMediaSession() {
        if ('mediaSession' in navigator) {
            console.log('🎵 Setting up Media Session API...');
            
            navigator.mediaSession.setActionHandler('play', () => {
                console.log('🎵 Media Session: Play action');
                // ✅ Gọi togglePlayPause thay vì trực tiếp audio.play()
                // để đảm bảo state được update đúng
                if (!this.isPlaying) {
                    this.userInteracted = true;
                    this.togglePlayPause();
                }
            });
            
            navigator.mediaSession.setActionHandler('pause', () => {
                console.log('🎵 Media Session: Pause action');
                // ✅ Gọi togglePlayPause thay vì trực tiếp audio.pause()
                // để đảm bảo state được update đúng
                if (this.isPlaying) {
                    this.togglePlayPause();
                }
            });
            
            navigator.mediaSession.setActionHandler('previoustrack', () => {
                console.log('🎵 Media Session: Previous track');
                this.previousTrack();
            });
            
            navigator.mediaSession.setActionHandler('nexttrack', () => {
                console.log('🎵 Media Session: Next track');
                this.nextTrack();
            });
            
            navigator.mediaSession.setActionHandler('seekbackward', (details) => {
                console.log('🎵 Media Session: Seek backward', details.seekOffset);
                this.seekBackward(details.seekOffset || 10);
            });
            
            navigator.mediaSession.setActionHandler('seekforward', (details) => {
                console.log('🎵 Media Session: Seek forward', details.seekOffset);
                this.seekForward(details.seekOffset || 10);
            });
            
            navigator.mediaSession.setActionHandler('seekto', (details) => {
                if (details.seekTime !== undefined) {
                    console.log('🎵 Media Session: Seek to', details.seekTime);
                    this.seekTo(details.seekTime);
                }
            });
            
            navigator.mediaSession.setActionHandler('stop', () => {
                console.log('🎵 Media Session: Stop action');
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
                navigator.mediaSession.metadata = new MediaMetadata({
                    title: track.title,
                    artist: track.artist || 'Unknown Artist',
                    album: this.currentPlaylist.name,
                    artwork: [
                        { src: '/static/music_player/images/album-art.png', sizes: '96x96', type: 'image/png' },
                        { src: '/static/music_player/images/album-art.png', sizes: '128x128', type: 'image/png' },
                        { src: '/static/music_player/images/album-art.png', sizes: '192x192', type: 'image/png' },
                        { src: '/static/music_player/images/album-art.png', sizes: '256x256', type: 'image/png' },
                        { src: '/static/music_player/images/album-art.png', sizes: '384x384', type: 'image/png' },
                        { src: '/static/music_player/images/album-art.png', sizes: '512x512', type: 'image/png' }
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
        console.log('🎵 Setting up audio preloading...');
        
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
                        console.log('🗑️ Cleaned up preloaded track:', trackId);
                    }
                }
            }
            
            // Preload next track
            const nextIndex = this.getNextTrackIndex();
            if (nextIndex !== this.currentTrackIndex) {
                const nextTrack = this.currentPlaylist.tracks[nextIndex];
                if (nextTrack && !this.preloadedTracks.has(nextTrack.id)) {
                    console.log('🎵 Preloading next track:', nextTrack.title);
                    const audio = new Audio();
                    audio.preload = 'metadata';
                    audio.src = nextTrack.file_url;
                    this.preloadedTracks.set(nextTrack.id, audio);
                }
            }
            
            // Preload previous track
            const prevIndex = this.getPreviousTrackIndex();
            if (prevIndex !== this.currentTrackIndex) {
                const prevTrack = this.currentPlaylist.tracks[prevIndex];
                if (prevTrack && !this.preloadedTracks.has(prevTrack.id)) {
                    console.log('🎵 Preloading previous track:', prevTrack.title);
                    const audio = new Audio();
                    audio.preload = 'metadata';
                    audio.src = prevTrack.file_url;
                    this.preloadedTracks.set(prevTrack.id, audio);
                }
            }
        } catch (error) {
            console.error('Error preloading tracks:', error);
        }
    }
    
    optimizeTouchEvents() {
        console.log('📱 Optimizing touch events...');
        
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
        console.log('🎵 Setting up background playback...');
        
        // Handle page visibility changes
        document.addEventListener('visibilitychange', () => {
            if (document.hidden) {
                console.log('📱 Page hidden - maintaining playback');
                // Keep playing in background
            } else {
                console.log('📱 Page visible - updating UI');
                this.updateMediaSessionMetadata();
            }
        });
        
        // Handle audio focus on mobile
        this.audio.addEventListener('pause', () => {
            if (this.isPlaying && document.hidden) {
                // Resume if paused due to page visibility
                setTimeout(() => {
                    if (this.isPlaying) {
                        this.audio.play().catch(console.error);
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
            console.warn('Invalid time value for seekTo:', time);
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
    
    destroy() {
        // Save state trước khi destroy (immediate)
        this.savePlayerStateImmediate();
        
        // ✅ Cleanup debounce timers
        if (this.saveStateDebounceTimer) {
            clearTimeout(this.saveStateDebounceTimer);
        }
        if (this.refreshPlaylistsDebounceTimer) {
            clearTimeout(this.refreshPlaylistsDebounceTimer);
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
            console.log('🗑️ Cleaned up all preloaded tracks');
        }
        
        // ✅ Cleanup caches
        if (this.formatTimeCache) {
            this.formatTimeCache.clear();
        }
        
        // ✅ Cleanup audio element
        if (this.audio) {
            this.audio.pause();
            this.audio.src = '';
            this.audio.load();
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
