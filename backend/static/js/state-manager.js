/**
 * State Manager for Music Player
 * Quản lý state persistence với debouncing và guaranteed saves
 */

class StateManager {
    constructor() {
        this.state = {};
        this.pendingSave = null;
        this.lastSaveTime = 0;
        this.minSaveInterval = 1000; // 1 second
    }
    
    /**
     * Update state
     */
    setState(updates) {
        this.state = {
            ...this.state,
            ...updates,
            lastUpdated: Date.now()
        };
        
        // Queue save
        this.queueSave();
    }
    
    /**
     * Get current state
     */
    getState() {
        return { ...this.state };
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
            // Note: Endpoint này có thể implement sau nếu cần sync state lên server
            // Hiện tại localStorage là đủ cho music player
            
            /* Uncomment khi cần server sync:
            await fetch('/music/user/save-state/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: JSON.stringify(state)
            });
            */
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
    
    /**
     * Check if user is logged in
     */
    isLoggedIn() {
        // Check if user is logged in by looking for user-related element
        return document.querySelector('[data-user-id]') !== null;
    }
    
    /**
     * Get CSRF token
     */
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

// Export to global scope
window.StateManager = StateManager;

