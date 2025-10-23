/**
 * Offline Manager cho Music Player
 * Quản lý Service Worker và offline capabilities
 * 
 * ✅ Features:
 * - Cache tracks để offline playback TRONG APP
 * - Hiển thị offline indicator
 * - Quản lý storage quota
 * - Preload tracks cho offline
 * 
 * ❌ Không cho:
 * - Download files ra ngoài app
 * - Share/export cached files
 */

class OfflineManager {
    constructor() {
        this.swRegistration = null;
        this.isOnline = navigator.onLine;
        this.cachedTracks = new Set();
        // ✅ Bỏ giới hạn 500MB - Browser tự quản lý quota
        this.autoCacheEnabled = this.getAutoCacheSetting(); // User preference
        
        this.init();
    }
    
    /**
     * Khởi tạo Service Worker
     */
    async init() {
        // Check browser support
        if (!('serviceWorker' in navigator)) {
            console.warn('Service Worker not supported');
            return;
        }
        
        try {
            // Register service worker
            this.swRegistration = await navigator.serviceWorker.register('/service-worker.js', {
                scope: '/'
            });
            
            // console.log('[Offline Manager] Service Worker registered');
            
            // ✅ Communicate auto-cache setting to service worker
            if (this.swRegistration && this.swRegistration.active) {
                this.sendMessage({
                    action: 'setAutoCacheEnabled',
                    enabled: this.autoCacheEnabled
                }).catch(() => {});
            }
            
            // Listen for updates
            this.swRegistration.addEventListener('updatefound', () => {
                // console.log('[Offline Manager] Service Worker update found');
            });
            
            // Listen for online/offline events
            window.addEventListener('online', () => this.handleOnlineStatusChange(true));
            window.addEventListener('offline', () => this.handleOnlineStatusChange(false));
            
            // Check current cache (delay để Service Worker active)
            setTimeout(() => this.updateCacheStatus(), 500);
            
        } catch (error) {
            console.error('🚨 Offline Manager Error:', error.message);
        }
    }
    
    /**
     * Xử lý thay đổi online/offline status
     */
    handleOnlineStatusChange(isOnline) {
        this.isOnline = isOnline;
        
        // Show toast notification
        const message = isOnline 
            ? '🟢 Đã kết nối Internet' 
            : '🔴 Mất kết nối - Chế độ offline (chỉ nghe được bài đã cache)';
        
        this.showNotification(message, isOnline ? 'success' : 'warning');
        
        // Update UI
        document.body.classList.toggle('offline-mode', !isOnline);
        
        // Dispatch event
        window.dispatchEvent(new CustomEvent('offlineStatusChanged', { 
            detail: { isOnline } 
        }));
    }
    
    /**
     * Preload track vào cache cho offline playback
     * ✅ Cache TRONG APP (không download ra ngoài)
     */
    async preloadTrack(trackUrl, trackTitle) {
        if (!this.swRegistration) {
            console.warn('Service Worker not available');
            return false;
        }
        
        try {
            // ✅ Không còn check size limit - Browser tự quản lý
            // Optional: Warn if browser quota is low
            if (navigator.storage && navigator.storage.estimate) {
                const estimate = await navigator.storage.estimate();
                const usagePercent = (estimate.usage / estimate.quota) * 100;
                
                if (usagePercent > 90) {
                    this.showNotification('⚠️ Dung lượng browser gần đầy (' + Math.round(usagePercent) + '%)!', 'warning');
                }
            }
            
            // Preload track
            const response = await this.sendMessage({
                action: 'preloadTrack',
                url: trackUrl
            });
            
            if (response.success) {
                this.cachedTracks.add(trackUrl);
                this.showNotification(`✅ Đã cache "${trackTitle}" để nghe offline`, 'success');
                await this.updateCacheStatus();
                return true;
            } else {
                throw new Error(response.error);
            }
            
        } catch (error) {
            console.error('🚨 Preload Track Error:', error.message);
            this.showNotification('❌ Lỗi khi cache bài hát', 'error');
            return false;
        }
    }
    
    /**
     * Xóa track khỏi cache
     */
    async removeCachedTrack(trackUrl) {
        if (!this.swRegistration) return false;
        
        try {
            const response = await this.sendMessage({
                action: 'clearCache',
                url: trackUrl
            });
            
            if (response.success) {
                this.cachedTracks.delete(trackUrl);
                
                // ✅ Remove from localStorage
                try {
                    const stored = localStorage.getItem('dbp_cached_tracks');
                    if (stored) {
                        const trackIds = JSON.parse(stored);
                        // Find track ID from URL
                        const trackId = this.extractTrackIdFromUrl(trackUrl);
                        if (trackId) {
                            const filtered = trackIds.filter(id => id !== trackId);
                            localStorage.setItem('dbp_cached_tracks', JSON.stringify(filtered));
                        }
                    }
                } catch (e) {
                    console.error('Failed to update localStorage:', e);
                }
                
                this.showNotification('🗑️ Đã xóa bài hát khỏi cache offline', 'info');
                await this.updateCacheStatus();
                return true;
            }
            
        } catch (error) {
            console.error('[Offline Manager] Remove failed:', error);
            return false;
        }
    }
    
    /**
     * Extract track ID from URL
     */
    extractTrackIdFromUrl(url) {
        try {
            const patterns = [
                /(\d{3})\s*-\s*/,          // 001 - TITLE.mp3
                /(\d{3})%20-%20/,          // 001%20-%20TITLE.mp3 (URL encoded)
                /playlist\/(\d{3})/,       // playlist/001
                /track_(\d+)\./,           // track_123.mp3
                /\/(\d+)\.mp3/,            // /123.mp3
                /\/(\d+)\//,               // /123/
                /playlist\/(\d+)/          // playlist/123
            ];
            
            for (const pattern of patterns) {
                const match = url.match(pattern);
                if (match) {
                    return parseInt(match[1]);
                }
            }
            
            return null;
        } catch (error) {
            return null;
        }
    }
    
    /**
     * Lấy kích thước cache hiện tại
     */
    async getCacheSize() {
        if (!this.swRegistration) return 0;
        
        try {
            const response = await this.sendMessage({ action: 'getCacheSize' });
            return response.size || 0;
        } catch (error) {
            console.error('[Offline Manager] Get cache size failed:', error);
            return 0;
        }
    }
    
    /**
     * Lấy danh sách các tracks đã cache
     */
    async getCachedTracks() {
        if (!this.swRegistration) return [];
        
        try {
            const response = await this.sendMessage({ action: 'getCachedTracks' });
            return response.tracks || [];
        } catch (error) {
            console.error('[Offline Manager] Get cached tracks failed:', error);
            return [];
        }
    }
    
    /**
     * Force cleanup range request caches
     */
    async cleanupRangeRequests() {
        if (!this.swRegistration) return false;
        
        try {
            const response = await this.sendMessage({ action: 'cleanupRangeRequests' });
            if (response.success) {
                this.showNotification('✅ Đã dọn dẹp cache rác', 'success');
                await this.updateCacheStatus();
                return true;
            }
        } catch (error) {
            console.error('[Offline Manager] Cleanup failed:', error);
            return false;
        }
    }
    
    /**
     * Update cache status UI
     */
    async updateCacheStatus() {
        const size = await this.getCacheSize();
        const sizeMB = (size / (1024 * 1024)).toFixed(2);
        
        // Get browser quota
        let maxMB = '∞'; // Unlimited
        let percentage = 0;
        
        if (navigator.storage && navigator.storage.estimate) {
            try {
                const estimate = await navigator.storage.estimate();
                maxMB = (estimate.quota / (1024 * 1024)).toFixed(0);
                percentage = Math.round((size / estimate.quota) * 100);
            } catch (e) {
                // Fallback if quota not available
            }
        }
        
        // Update UI
        const cacheStatus = document.getElementById('offline-cache-status');
        if (cacheStatus) {
            cacheStatus.innerHTML = `
                <div class="cache-info">
                    <i class="bi bi-cloud-download"></i>
                    <span>Offline Cache: ${sizeMB}MB / ${maxMB}MB (${percentage}%)</span>
                </div>
                <div class="cache-progress">
                    <div class="cache-progress-bar" style="width: ${percentage}%"></div>
                </div>
            `;
        }
        
        // Dispatch event
        window.dispatchEvent(new CustomEvent('cacheStatusUpdated', {
            detail: { size, percentage, sizeMB, maxMB }
        }));
    }
    
    /**
     * Check if track is cached
     */
    async isTrackCached(trackUrl) {
        if (!('caches' in window)) return false;
        
        try {
            // ✅ Match with Service Worker cache version
            const cache = await caches.open('dbp-music-v4-range-fix');
            const response = await cache.match(trackUrl);
            return !!response;
        } catch (error) {
            return false;
        }
    }
    
    /**
     * Gửi message đến Service Worker với retry logic
     */
    sendMessage(message, retries = 3) {
        return new Promise(async (resolve, reject) => {
            // Wait for Service Worker to be active với retry
            for (let i = 0; i < retries; i++) {
                if (this.swRegistration && this.swRegistration.active) {
                    break;
                }
                // Wait 100ms và thử lại
                await new Promise(r => setTimeout(r, 100));
            }
            
            if (!this.swRegistration || !this.swRegistration.active) {
                // Nếu vẫn chưa active thì return default values thay vì reject
                console.warn('[Offline Manager] Service Worker not active yet, returning defaults');
                if (message.action === 'getCacheSize') {
                    resolve({ size: 0 });
                } else {
                    resolve({ success: false });
                }
                return;
            }
            
            const messageChannel = new MessageChannel();
            
            messageChannel.port1.onmessage = (event) => {
                resolve(event.data);
            };
            
            this.swRegistration.active.postMessage(message, [messageChannel.port2]);
            
            // Timeout after 10s
            setTimeout(() => reject(new Error('Message timeout')), 10000);
        });
    }
    
    /**
     * Show notification toast
     */
    showNotification(message, type = 'info') {
        // Tạo toast notification
        const toast = document.createElement('div');
        toast.className = `offline-toast offline-toast-${type}`;
        toast.textContent = message;
        
        document.body.appendChild(toast);
        
        // Animate in
        setTimeout(() => toast.classList.add('show'), 10);
        
        // Remove after 3s
        setTimeout(() => {
            toast.classList.remove('show');
            setTimeout(() => toast.remove(), 300);
        }, 3000);
    }
    
    /**
     * Clear all cache
     */
    async clearAllCache() {
        if (!('caches' in window)) return false;
        
        try {
            const cacheNames = await caches.keys();
            await Promise.all(
                cacheNames.map(cacheName => caches.delete(cacheName))
            );
            
            this.cachedTracks.clear();
            
            // ✅ Clear localStorage cached tracks
            try {
                localStorage.removeItem('dbp_cached_tracks');
            } catch (e) {
                console.error('Failed to clear localStorage:', e);
            }
            
            this.showNotification('🗑️ Đã xóa toàn bộ cache offline', 'success');
            await this.updateCacheStatus();
            return true;
            
        } catch (error) {
            console.error('[Offline Manager] Clear all cache failed:', error);
            return false;
        }
    }
    
    /**
     * Get auto-cache setting from localStorage
     */
    getAutoCacheSetting() {
        try {
            const setting = localStorage.getItem('autoCacheEnabled');
            // Default: enabled
            return setting === null ? true : setting === 'true';
        } catch (e) {
            return true; // Default enabled
        }
    }
    
    /**
     * Set auto-cache setting
     */
    setAutoCacheSetting(enabled) {
        try {
            this.autoCacheEnabled = enabled;
            localStorage.setItem('autoCacheEnabled', enabled.toString());
            
            // Notify service worker (optional - for future use)
            if (this.swRegistration) {
                this.sendMessage({
                    action: 'setAutoCacheEnabled',
                    enabled: enabled
                }).catch(() => {});
            }
            
            return true;
        } catch (e) {
            console.error('Failed to save auto-cache setting:', e);
            return false;
        }
    }
    
    /**
     * Check if auto-cache is enabled
     */
    isAutoCacheEnabled() {
        return this.autoCacheEnabled;
    }
}

// CSS cho toast notifications
const style = document.createElement('style');
style.textContent = `
.offline-toast {
    position: fixed;
    bottom: 100px;
    left: 50%;
    transform: translateX(-50%) translateY(100px);
    background: rgba(0, 0, 0, 0.9);
    color: white;
    padding: 12px 24px;
    border-radius: 8px;
    font-size: 14px;
    z-index: 100010;
    opacity: 0;
    transition: all 0.3s ease;
    max-width: 90%;
    text-align: center;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
    word-wrap: break-word;
}

.offline-toast.show {
    opacity: 1;
    transform: translateX(-50%) translateY(0);
}

.offline-toast-success {
    background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
    box-shadow: 0 4px 12px rgba(17, 153, 142, 0.4);
}

.offline-toast-warning {
    background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
    box-shadow: 0 4px 12px rgba(240, 147, 251, 0.4);
}

.offline-toast-error {
    background: linear-gradient(135deg, #fa709a 0%, #fee140 100%);
    box-shadow: 0 4px 12px rgba(250, 112, 154, 0.4);
}

.offline-toast-info {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
}

/* Mobile Responsive */
@media (max-width: 768px) {
    .offline-toast {
        top: 80px;
        bottom: auto;
        left: 50%;
        transform: translateX(-50%) translateY(-100px);
        max-width: 85%;
        padding: 10px 20px;
        font-size: 13px;
        border-radius: 6px;
    }
    
    .offline-toast.show {
        transform: translateX(-50%) translateY(0);
    }
}

/* Small mobile screens */
@media (max-width: 480px) {
    .offline-toast {
        top: 70px;
        max-width: 90%;
        padding: 8px 16px;
        font-size: 12px;
    }
}

body.offline-mode::before {
    content: '🔴 OFFLINE MODE';
    position: fixed;
    top: 10px;
    right: 10px;
    background: rgba(255, 0, 0, 0.8);
    color: white;
    padding: 8px 16px;
    border-radius: 20px;
    font-size: 12px;
    font-weight: bold;
    z-index: 9998;
    animation: pulse 2s infinite;
}

@keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.5; }
}

.cache-info {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 13px;
    color: rgba(255, 255, 255, 0.9);
    margin-bottom: 8px;
}

.cache-progress {
    width: 100%;
    height: 4px;
    background: rgba(255, 255, 255, 0.2);
    border-radius: 2px;
    overflow: hidden;
}

.cache-progress-bar {
    height: 100%;
    background: linear-gradient(90deg, #11998e 0%, #38ef7d 100%);
    transition: width 0.3s ease;
}
`;
document.head.appendChild(style);

// Export
window.OfflineManager = OfflineManager;

