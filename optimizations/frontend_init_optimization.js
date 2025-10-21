/**
 * Frontend Initialization Optimization
 * Tối ưu flow khởi tạo music player
 */

// ==========================================
// 1. Optimized MusicPlayer Initialization
// ==========================================

class OptimizedMusicPlayer {
    constructor() {
        // Basic setup
        this.audio = document.getElementById('audio-player');
        this.playlists = [];
        this.currentPlaylist = null;
        this.currentTrackIndex = 0;
        this.isPlaying = false;
        
        // State flags
        this.userInteracted = false;
        this.isRestoringState = false;
        this.isLoadingTrack = false;
        
        // Initialize elements
        this.initializeElements();
        this.bindEvents();
        
        // ✅ OPTIMIZED: Single async init method
        this.initializeAsync();
    }
    
    /**
     * ✅ OPTIMIZED: Simplified async initialization
     * - Parallel loading
     * - Single render pass
     * - No setTimeout delays
     */
    async initializeAsync() {
        try {
            console.time('Player Initialization');
            
            // Phase 1: Parallel initialization
            const [initialData, offlineManager] = await Promise.all([
                this.loadInitialData(),
                this.initializeOfflineManager()
            ]);
            
            console.log('✅ Phase 1 complete: Initial data loaded');
            
            // Phase 2: Setup player state
            this.playlists = initialData.playlists;
            this.settings = initialData.settings;
            this.userTracks = initialData.userTracks;
            this.userPlaylists = initialData.userPlaylists;
            
            // Phase 3: Restore or setup default state
            const restored = await this.restorePlayerState();
            
            if (!restored && this.playlists.length > 0) {
                // No saved state, load first playlist
                this.selectPlaylist(this.playlists[0].id);
            }
            
            // Phase 4: Update UI once
            this.populatePlaylistSelect();
            this.populateTrackList();
            this.updateCachedTracksUI();
            
            // Phase 5: Setup background tasks
            this.setupBackgroundTasks();
            
            console.timeEnd('Player Initialization');
            console.log('🎵 Music Player ready!');
            
        } catch (error) {
            console.error('❌ Initialization failed:', error);
            this.showError('Không thể khởi tạo music player. Vui lòng reload trang.');
        }
    }
    
    /**
     * ✅ NEW: Load all initial data in single API call
     */
    async loadInitialData() {
        try {
            const response = await fetch('/music/api/initial-data/', {
                cache: 'no-cache',
                headers: {
                    'Cache-Control': 'no-cache, no-store, must-revalidate'
                }
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }
            
            const data = await response.json();
            
            if (!data.success) {
                throw new Error(data.error || 'Failed to load initial data');
            }
            
            return {
                playlists: data.playlists || [],
                settings: data.settings || this.getDefaultSettings(),
                userTracks: data.user_tracks || [],
                userPlaylists: data.user_playlists || []
            };
            
        } catch (error) {
            console.error('Error loading initial data:', error);
            
            // Fallback: Try loading playlists only
            try {
                const response = await fetch('/music/api/');
                const data = await response.json();
                return {
                    playlists: data.playlists || [],
                    settings: this.getDefaultSettings(),
                    userTracks: [],
                    userPlaylists: []
                };
            } catch (fallbackError) {
                throw new Error('Cannot load music data');
            }
        }
    }
    
    /**
     * ✅ OPTIMIZED: Offline manager init với timeout
     */
    async initializeOfflineManager() {
        if (!('serviceWorker' in navigator)) {
            console.warn('Service Worker not supported');
            return null;
        }
        
        try {
            // Create offline manager
            this.offlineManager = new OfflineManager();
            
            // Wait for it to be ready (max 2 seconds)
            await this.waitForOfflineManager(2000);
            
            return this.offlineManager;
            
        } catch (error) {
            console.warn('Offline manager failed to initialize:', error);
            return null;
        }
    }
    
    /**
     * Wait for offline manager to be ready
     */
    waitForOfflineManager(timeout = 2000) {
        return new Promise((resolve, reject) => {
            const startTime = Date.now();
            
            const check = () => {
                if (this.offlineManager && this.offlineManager.swRegistration) {
                    resolve();
                } else if (Date.now() - startTime > timeout) {
                    reject(new Error('Offline manager timeout'));
                } else {
                    setTimeout(check, 100);
                }
            };
            
            check();
        });
    }
    
    /**
     * ✅ OPTIMIZED: Update all cached track indicators once
     */
    async updateCachedTracksUI() {
        if (!this.offlineManager) return;
        
        try {
            // Load cached tracks from service worker
            const cachedTracks = await this.offlineManager.getCachedTracks();
            
            // Build Set for fast lookup
            this.cachedTrackUrls = new Set(
                cachedTracks.map(track => track.url)
            );
            
            // Update indicators in track list
            this.updateTrackListOfflineIndicators();
            
            // Update cache status
            await this.offlineManager.updateCacheStatus();
            
        } catch (error) {
            console.error('Error updating cached tracks UI:', error);
        }
    }
    
    /**
     * Setup background tasks (lazy loading, preloading, etc.)
     */
    setupBackgroundTasks() {
        // Lazy load user music data (if not loaded initially)
        if (this.userTracks.length === 0) {
            setTimeout(() => {
                this.loadUserTracksLazy();
            }, 5000); // Load after 5s
        }
        
        // Preload album covers (lazy)
        setTimeout(() => {
            this.preloadAlbumCovers();
        }, 3000);
        
        // Setup periodic cache check (every 5 minutes)
        setInterval(() => {
            if (this.offlineManager) {
                this.offlineManager.updateCacheStatus();
            }
        }, 5 * 60 * 1000);
    }
    
    /**
     * Lazy load user tracks (background)
     */
    async loadUserTracksLazy() {
        try {
            const response = await fetch('/music/user/tracks/paginated?page=1&per_page=20');
            const data = await response.json();
            
            if (data.success) {
                this.userTracks = data.tracks;
                // No UI update needed yet
            }
        } catch (error) {
            console.warn('Background user tracks load failed:', error);
        }
    }
    
    /**
     * Preload album covers in background
     */
    preloadAlbumCovers() {
        const covers = new Set();
        
        // Collect all unique album covers
        this.playlists.forEach(playlist => {
            if (playlist.cover_image) {
                covers.add(playlist.cover_image);
            }
            playlist.tracks.forEach(track => {
                if (track.album_cover) {
                    covers.add(track.album_cover);
                }
            });
        });
        
        // Preload using Image objects
        covers.forEach(url => {
            const img = new Image();
            img.src = url;
        });
    }
    
    /**
     * Get default settings
     */
    getDefaultSettings() {
        return {
            auto_play: true,
            volume: 0.7,
            repeat_mode: 'all',
            shuffle: false,
            listening_lock: false,
            low_power_mode: false,
            storage_quota_mb: 369,
            upload_usage: {
                used: 0,
                total: 369,
                remaining: 369,
                tracks_count: 0
            }
        };
    }
    
    // ... rest of methods stay the same
}


// ==========================================
// 2. State Manager (Improved)
// ==========================================

class StateManager {
    constructor() {
        this.state = {};
        this.pendingSave = null;
        this.lastSaveTime = 0;
        this.minSaveInterval = 1000;
        this.saveQueue = [];
    }
    
    /**
     * Update state
     */
    setState(updates) {
        this.state = {
            ...this.state,
            ...updates
        };
        
        // Queue save
        this.queueSave();
    }
    
    /**
     * Queue save with debouncing
     */
    queueSave() {
        clearTimeout(this.pendingSave);
        this.pendingSave = setTimeout(() => {
            this.flush();
        }, this.minSaveInterval);
    }
    
    /**
     * Immediate save (for critical events)
     */
    async saveImmediate() {
        clearTimeout(this.pendingSave);
        return this.flush();
    }
    
    /**
     * Flush state to storage
     */
    async flush() {
        const stateToSave = { ...this.state };
        
        try {
            // Save to localStorage immediately
            localStorage.setItem('player_state', JSON.stringify(stateToSave));
            
            // Also save to server if logged in
            if (this.isLoggedIn()) {
                await this.saveToServer(stateToSave);
            }
            
            this.lastSaveTime = Date.now();
            
        } catch (error) {
            console.error('Failed to save state:', error);
        }
    }
    
    /**
     * Save to server
     */
    async saveToServer(state) {
        try {
            await fetch('/music/user/save-state/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: JSON.stringify(state)
            });
        } catch (error) {
            console.error('Failed to save state to server:', error);
        }
    }
    
    /**
     * Load state
     */
    loadState() {
        try {
            const saved = localStorage.getItem('player_state');
            if (saved) {
                this.state = JSON.parse(saved);
                return this.state;
            }
        } catch (error) {
            console.error('Failed to load state:', error);
        }
        return null;
    }
    
    /**
     * Clear state
     */
    clearState() {
        this.state = {};
        localStorage.removeItem('player_state');
    }
    
    isLoggedIn() {
        // Check if user is logged in
        return document.querySelector('[data-user-id]') !== null;
    }
    
    getCSRFToken() {
        const name = 'csrftoken';
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let cookie of cookies) {
                cookie = cookie.trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
}


// ==========================================
// 3. Usage Example
// ==========================================

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    console.log('🎵 Initializing Music Player...');
    
    // Create player instance
    window.musicPlayer = new OptimizedMusicPlayer();
    
    // Also initialize state manager
    window.stateManager = new StateManager();
    
    // Save state on critical events
    window.addEventListener('beforeunload', () => {
        if (window.stateManager) {
            window.stateManager.saveImmediate();
        }
    });
});


// ==========================================
// 4. Performance Monitoring
// ==========================================

class PerformanceMonitor {
    constructor() {
        this.marks = new Map();
        this.measures = [];
    }
    
    /**
     * Start timing
     */
    mark(name) {
        this.marks.set(name, performance.now());
    }
    
    /**
     * End timing and record
     */
    measure(name, startMark) {
        if (!this.marks.has(startMark)) {
            console.warn(`Start mark '${startMark}' not found`);
            return null;
        }
        
        const startTime = this.marks.get(startMark);
        const endTime = performance.now();
        const duration = endTime - startTime;
        
        this.measures.push({
            name,
            startMark,
            duration,
            timestamp: new Date().toISOString()
        });
        
        console.log(`⏱️ ${name}: ${duration.toFixed(2)}ms`);
        
        return duration;
    }
    
    /**
     * Get all measures
     */
    getMeasures() {
        return this.measures;
    }
    
    /**
     * Get average duration for a measure
     */
    getAverage(name) {
        const filtered = this.measures.filter(m => m.name === name);
        if (filtered.length === 0) return 0;
        
        const sum = filtered.reduce((acc, m) => acc + m.duration, 0);
        return sum / filtered.length;
    }
    
    /**
     * Report performance stats
     */
    report() {
        console.group('📊 Performance Report');
        
        const uniqueNames = [...new Set(this.measures.map(m => m.name))];
        
        uniqueNames.forEach(name => {
            const avg = this.getAverage(name);
            const count = this.measures.filter(m => m.name === name).length;
            console.log(`${name}: ${avg.toFixed(2)}ms (${count} samples)`);
        });
        
        console.groupEnd();
    }
}

// Global instance
window.perfMonitor = new PerformanceMonitor();

