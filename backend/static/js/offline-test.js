/**
 * Test Script for Offline Playback Feature
 * 
 * Usage:
 * 1. Mở DevTools Console
 * 2. Copy/paste toàn bộ file này vào Console
 * 3. Hoặc load script: <script src="/static/js/offline-test.js"></script>
 */

(async function testOfflinePlayback() {
    console.log('🧪 Starting Offline Playback Tests...\n');
    
    const results = {
        passed: 0,
        failed: 0,
        warnings: 0
    };
    
    // Helper functions
    const pass = (msg) => {
        console.log(`✅ PASS: ${msg}`);
        results.passed++;
    };
    
    const fail = (msg) => {
        console.error(`❌ FAIL: ${msg}`);
        results.failed++;
    };
    
    const warn = (msg) => {
        console.warn(`⚠️ WARN: ${msg}`);
        results.warnings++;
    };
    
    const section = (title) => {
        console.log(`\n━━━ ${title} ━━━`);
    };
    
    // Test 1: Browser Support
    section('Test 1: Browser Support');
    
    if ('serviceWorker' in navigator) {
        pass('Service Worker supported');
    } else {
        fail('Service Worker NOT supported in this browser');
        return;
    }
    
    if ('caches' in window) {
        pass('Cache API supported');
    } else {
        fail('Cache API NOT supported');
    }
    
    // Test 2: HTTPS/Localhost Check
    section('Test 2: Security Context');
    
    const isSecureContext = window.isSecureContext;
    const protocol = window.location.protocol;
    const hostname = window.location.hostname;
    
    if (isSecureContext) {
        pass(`Secure context: ${protocol}//${hostname}`);
    } else {
        fail(`NOT secure context! Service Workers require HTTPS or localhost`);
        warn(`Current: ${protocol}//${hostname}`);
    }
    
    // Test 3: Service Worker Registration
    section('Test 3: Service Worker Registration');
    
    try {
        const registrations = await navigator.serviceWorker.getRegistrations();
        
        if (registrations.length === 0) {
            warn('No Service Workers registered yet');
            warn('Service Worker should register on page load');
        } else {
            pass(`Found ${registrations.length} Service Worker(s)`);
            
            registrations.forEach((reg, index) => {
                console.log(`\n📍 Service Worker #${index + 1}:`);
                console.log(`   Scope: ${reg.scope}`);
                console.log(`   Active: ${reg.active ? '✅ Yes' : '❌ No'}`);
                console.log(`   Installing: ${reg.installing ? '🔄 Yes' : 'No'}`);
                console.log(`   Waiting: ${reg.waiting ? '⏳ Yes' : 'No'}`);
                
                if (reg.active) {
                    pass(`Service Worker is active`);
                } else if (reg.installing) {
                    warn(`Service Worker is installing...`);
                } else if (reg.waiting) {
                    warn(`Service Worker is waiting to activate`);
                } else {
                    fail(`Service Worker is not active`);
                }
            });
        }
    } catch (error) {
        fail(`Error checking Service Worker: ${error.message}`);
    }
    
    // Test 4: Cache Storage
    section('Test 4: Cache Storage');
    
    try {
        const cacheNames = await caches.keys();
        
        if (cacheNames.length === 0) {
            warn('No caches found yet');
            warn('Cache will be created when you play music');
        } else {
            pass(`Found ${cacheNames.length} cache(s)`);
            
            for (const cacheName of cacheNames) {
                const cache = await caches.open(cacheName);
                const cachedRequests = await cache.keys();
                
                console.log(`\n📦 Cache: "${cacheName}"`);
                console.log(`   Files: ${cachedRequests.length}`);
                
                if (cacheName === 'dbp-music-v3-final') {
                    pass(`Correct cache name: ${cacheName}`);
                    
                    if (cachedRequests.length > 0) {
                        pass(`${cachedRequests.length} tracks cached`);
                        
                        // Show first 3 cached files
                        console.log('\n   📄 Cached files:');
                        cachedRequests.slice(0, 3).forEach(req => {
                            const url = new URL(req.url);
                            console.log(`      - ${url.pathname}`);
                        });
                        
                        if (cachedRequests.length > 3) {
                            console.log(`      ... and ${cachedRequests.length - 3} more`);
                        }
                    } else {
                        warn('No tracks cached yet');
                    }
                } else if (cacheName.startsWith('dbp-music-')) {
                    warn(`Old cache version found: ${cacheName}`);
                    warn('Consider clearing old caches');
                }
            }
        }
    } catch (error) {
        fail(`Error checking caches: ${error.message}`);
    }
    
    // Test 5: Offline Manager
    section('Test 5: Offline Manager');
    
    if (typeof OfflineManager !== 'undefined') {
        pass('OfflineManager class loaded');
        
        if (window.musicPlayer && window.musicPlayer.offlineManager) {
            pass('OfflineManager initialized in Music Player');
        } else {
            warn('OfflineManager not initialized in Music Player yet');
        }
    } else {
        fail('OfflineManager class NOT loaded');
        fail('Check if /static/js/offline-manager.js is loaded');
    }
    
    // Test 6: localStorage Check
    section('Test 6: localStorage - Cached Tracks');
    
    try {
        const cachedTracksStr = localStorage.getItem('dbp_cached_tracks');
        
        if (cachedTracksStr) {
            const cachedTracks = JSON.parse(cachedTracksStr);
            pass(`${cachedTracks.length} tracks in localStorage`);
            console.log(`   Track IDs: ${cachedTracks.join(', ')}`);
        } else {
            warn('No cached tracks in localStorage yet');
        }
    } catch (error) {
        fail(`Error reading localStorage: ${error.message}`);
    }
    
    // Test 7: Check Service Worker Script
    section('Test 7: Service Worker Script Accessibility');
    
    try {
        const response = await fetch('/service-worker.js', { cache: 'no-cache' });
        
        if (response.ok) {
            pass(`Service Worker script accessible: ${response.status}`);
            
            const contentType = response.headers.get('content-type');
            if (contentType && contentType.includes('javascript')) {
                pass(`Correct content-type: ${contentType}`);
            } else {
                warn(`Content-type: ${contentType}`);
            }
        } else {
            fail(`Service Worker script returned: ${response.status}`);
        }
    } catch (error) {
        fail(`Cannot fetch Service Worker script: ${error.message}`);
    }
    
    // Test 8: Check Manifest
    section('Test 8: PWA Manifest');
    
    try {
        const response = await fetch('/manifest.json', { cache: 'no-cache' });
        
        if (response.ok) {
            pass(`Manifest accessible: ${response.status}`);
            
            const manifest = await response.json();
            console.log(`   Name: ${manifest.name || manifest.short_name}`);
            console.log(`   Start URL: ${manifest.start_url}`);
            console.log(`   Display: ${manifest.display}`);
            console.log(`   Theme Color: ${manifest.theme_color}`);
            
            if (manifest.icons && manifest.icons.length > 0) {
                pass(`${manifest.icons.length} icon(s) defined`);
            } else {
                warn('No icons defined in manifest');
            }
        } else {
            warn(`Manifest returned: ${response.status}`);
        }
    } catch (error) {
        warn(`Cannot fetch manifest: ${error.message}`);
    }
    
    // Test 9: Simulate Offline
    section('Test 9: Offline Simulation (Optional)');
    
    console.log('To test offline mode:');
    console.log('1. DevTools → Network tab');
    console.log('2. Check "Offline" checkbox');
    console.log('3. Play a previously cached track');
    console.log('4. If it plays → Offline playback works! ✅');
    
    // Summary
    section('Test Summary');
    
    const total = results.passed + results.failed + results.warnings;
    
    console.log(`\n📊 Results:`);
    console.log(`   ✅ Passed: ${results.passed}`);
    console.log(`   ❌ Failed: ${results.failed}`);
    console.log(`   ⚠️ Warnings: ${results.warnings}`);
    console.log(`   📝 Total: ${total}`);
    
    if (results.failed === 0 && results.warnings === 0) {
        console.log(`\n🎉 ALL TESTS PASSED! Offline Playback is ready to use!`);
    } else if (results.failed === 0) {
        console.log(`\n✅ Tests passed with ${results.warnings} warning(s)`);
        console.log(`Check warnings above for potential issues`);
    } else {
        console.log(`\n❌ ${results.failed} test(s) failed. Fix these issues first!`);
    }
    
    console.log(`\n💡 Next Steps:`);
    if (results.failed > 0) {
        console.log(`1. Fix failed tests (read OFFLINE_PLAYBACK_FIXES.md)`);
        console.log(`2. Hard refresh (Ctrl + Shift + R)`);
        console.log(`3. Run this test again`);
    } else {
        console.log(`1. Open Music Player`);
        console.log(`2. Play some tracks`);
        console.log(`3. Enable Offline mode (DevTools → Network → Offline)`);
        console.log(`4. Try playing cached tracks`);
    }
    
    return results;
})();

