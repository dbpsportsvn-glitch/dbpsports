/**
 * YouTube Import Handler - Simple Version
 * Xử lý import audio từ YouTube videos/playlists
 */

// YouTube Import functionality
console.log('📦 [YouTube Import] Script loading...');
console.log('📦 [YouTube Import] Script version: 1.9.0');
console.log('📦 [YouTube Import] Current time:', new Date().toISOString());

document.addEventListener('DOMContentLoaded', () => {
    console.log('🚀 [YouTube Import] DOM loaded, initializing...');
    
    // Get elements
    const youtubeImportBtn = document.getElementById('youtube-import-btn');
    const youtubeImportModal = document.getElementById('youtube-import-modal');
    const youtubeImportCloseBtn = document.getElementById('youtube-import-close-btn');
    const youtubeCancelBtn = document.getElementById('youtube-cancel-btn');
    const youtubeUrlInput = document.getElementById('youtube-url');
    const youtubePlaylistSelect = document.getElementById('youtube-playlist-select');
    const youtubePreviewBtn = document.getElementById('youtube-preview-btn');
    const youtubeImportStartBtn = document.getElementById('youtube-import-start-btn');
    const youtubePreviewSection = document.getElementById('youtube-preview');
    const youtubePreviewContent = document.getElementById('youtube-preview-content');
    const youtubeImportProgress = document.getElementById('youtube-import-progress');
    const youtubeProgressFill = document.getElementById('youtube-progress-fill');
    const youtubeProgressText = document.getElementById('youtube-progress-text');
    const youtubeProgressDetails = document.getElementById('youtube-progress-details');
    const extractAudioOnlyCheckbox = document.getElementById('extract-audio-only');
    const importPlaylistCheckbox = document.getElementById('import-playlist');
    
    // Cookie management elements
    const cookieStatus = document.getElementById('cookie-status');
    const cookieFileInput = document.getElementById('cookie-file-input');
    const uploadCookieBtn = document.getElementById('upload-cookie-btn');
    const deleteCookieBtn = document.getElementById('delete-cookie-btn');
    
    // Import control elements
    const cancelImportBtn = document.getElementById('cancel-import-btn');
    
    // Paste button element
    const pasteUrlBtn = document.getElementById('paste-url-btn');

    let currentImportInfo = null;

    // Check if elements exist
    
    // Test all elements
    const allElements = {
        'youtubeImportBtn': youtubeImportBtn,
        'youtubeImportModal': youtubeImportModal,
        'youtubeImportCloseBtn': youtubeImportCloseBtn,
        'youtubeUrlInput': youtubeUrlInput,
        'youtubePlaylistSelect': youtubePlaylistSelect,
        'youtubePreviewBtn': youtubePreviewBtn,
        'youtubeImportStartBtn': youtubeImportStartBtn,
        'youtubeCancelBtn': youtubeCancelBtn,
        'youtubePreviewSection': youtubePreviewSection,
        'youtubePreviewContent': youtubePreviewContent,
        'youtubeImportProgress': youtubeImportProgress,
        'youtubeProgressFill': youtubeProgressFill,
        'youtubeProgressText': youtubeProgressText,
        'youtubeProgressDetails': youtubeProgressDetails,
        'extractAudioOnlyCheckbox': extractAudioOnlyCheckbox,
        'importPlaylistCheckbox': importPlaylistCheckbox,
        'cookieStatus': cookieStatus,
        'cookieFileInput': cookieFileInput,
        'uploadCookieBtn': uploadCookieBtn,
        'deleteCookieBtn': deleteCookieBtn,
        'cancelImportBtn': cancelImportBtn,
        'pasteUrlBtn': pasteUrlBtn
    };
    
    // Check all elements silently
    for (const [name, element] of Object.entries(allElements)) {
        if (!element) {
            console.error(`❌ [YouTube Import] Missing element: ${name}`);
        }
    }
    
    if (!youtubeImportBtn || !youtubeImportModal) {
        console.error('❌ [YouTube Import] Critical elements not found!');
        console.error('youtubeImportBtn:', youtubeImportBtn);
        console.error('youtubeImportModal:', youtubeImportModal);
        return;
    }

    // --- Event Listeners ---
    youtubeImportBtn.addEventListener('click', () => {
        console.log('🎯 [YouTube Import] Import button clicked!');
        // ✅ CRITICAL: Reset modal BEFORE opening to clear old info
        resetYouTubeImportModal();
        youtubeImportModal.classList.remove('hidden');
        populateYouTubePlaylistDropdown();
        loadCookieStatus(); // Load cookie status when modal opens
        console.log('✅ [YouTube Import] Modal opened successfully');
    });

    youtubeImportCloseBtn.addEventListener('click', () => {
        youtubeImportModal.classList.add('hidden');
    });

    youtubeCancelBtn.addEventListener('click', () => {
        youtubeImportModal.classList.add('hidden');
    });

    youtubePreviewBtn.addEventListener('click', async () => {
        const url = youtubeUrlInput.value.trim();
        
        console.log('🔍 [YouTube Import] Starting preview for URL:', url);
        
        if (!url) {
            console.warn('⚠️ [YouTube Import] No URL provided');
            showToast('Vui lòng nhập URL YouTube.', 'error');
            return;
        }
        
        if (!isValidYouTubeUrl(url)) {
            console.warn('⚠️ [YouTube Import] Invalid YouTube URL:', url);
            showToast('URL YouTube không hợp lệ.', 'error');
            return;
        }
        
        console.log('✅ [YouTube Import] URL validation passed');
        
        youtubePreviewBtn.disabled = true;
        youtubePreviewBtn.innerHTML = '<i class="bi bi-hourglass-split"></i> Đang tải...';
        youtubePreviewSection.classList.add('hidden');
        youtubeImportStartBtn.disabled = true;

        try {
            const importPlaylist = importPlaylistCheckbox.checked;
            console.log('📋 [YouTube Import] Request data:', {
                url: url,
                import_playlist: importPlaylist
            });
            
            console.log('🌐 [YouTube Import] Sending request to /music/youtube/info/');
            
            // Thêm timeout cho request
            const controller = new AbortController();
            const timeoutId = setTimeout(() => {
                controller.abort();
                console.error('⏰ [YouTube Import] Request timeout after 30 seconds');
            }, 30000);
            
            const response = await fetch('/music/youtube/info/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCsrfToken()
                },
                body: JSON.stringify({ 
                    url: url,
                    import_playlist: importPlaylist
                }),
                signal: controller.signal
            });
            
            clearTimeout(timeoutId);

            console.log('📡 [YouTube Import] Response received:', {
                status: response.status,
                statusText: response.statusText,
                ok: response.ok
            });

            const data = await response.json();
            console.log('📊 [YouTube Import] Response data:', data);

            if (data.success) {
                console.log('✅ [YouTube Import] Success! Info:', data.info);
                currentImportInfo = data.info;
                renderYouTubePreview(data.info);
                youtubePreviewSection.classList.remove('hidden');
                youtubeImportStartBtn.disabled = false;
                showToast('Đã tải thông tin thành công!', 'success');
            } else {
                console.error('❌ [YouTube Import] API Error:', data.error);
                showToast(data.error || 'Lỗi khi tải thông tin YouTube.', 'error');
            }
        } catch (error) {
            console.error('💥 [YouTube Import] Network/JS Error:', error);
            console.error('💥 [YouTube Import] Error details:', {
                name: error.name,
                message: error.message,
                stack: error.stack
            });
            
            // Xử lý các loại lỗi khác nhau
            if (error.name === 'AbortError') {
                showToast('Request timeout! Server có thể đang bị treo. Vui lòng thử lại sau.', 'error');
            } else if (error.message.includes('Failed to fetch')) {
                showToast('Không thể kết nối đến server. Vui lòng kiểm tra kết nối internet.', 'error');
            } else {
                showToast('Lỗi mạng hoặc server khi tải thông tin YouTube.', 'error');
            }
        } finally {
            console.log('🏁 [YouTube Import] Preview request completed');
            youtubePreviewBtn.disabled = false;
            youtubePreviewBtn.innerHTML = '<i class="bi bi-eye"></i> Xem Trước';
        }
    });

    youtubeImportStartBtn.addEventListener('click', async () => {
        const url = youtubeUrlInput.value.trim();
        
        console.log('🚀 [YouTube Import] Starting import process...');
        
        if (!url) {
            showToast('Vui lòng nhập URL YouTube.', 'error');
            return;
        }
        
        if (!isValidYouTubeUrl(url)) {
            showToast('URL YouTube không hợp lệ.', 'error');
            return;
        }

        const playlistId = youtubePlaylistSelect.value || null;
        const audioOnly = extractAudioOnlyCheckbox.checked;
        const importPlaylist = importPlaylistCheckbox.checked;

        // Disable buttons and show progress
        youtubeImportStartBtn.disabled = true;
        youtubePreviewBtn.disabled = true;
        youtubeCancelBtn.disabled = true;
        youtubeImportProgress.classList.remove('hidden');
        youtubeProgressFill.style.width = '0%';
        youtubeProgressText.textContent = 'Đang lấy thông tin...';
        youtubeProgressDetails.textContent = '';

        // Start progress tracking
        let progressValue = 0;
        let isCompleted = false;
        const progressInterval = setInterval(() => {
            if (isCompleted) {
                clearInterval(progressInterval);
                return;
            }
            
            progressValue += Math.random() * 8; // Slower progress for better UX
            if (progressValue > 90) progressValue = 90; // Don't reach 100% until completion
            
            youtubeProgressFill.style.width = `${progressValue}%`;
            
            // Update progress text based on current step
            if (progressValue < 30) {
                youtubeProgressText.textContent = 'Đang lấy thông tin...';
            } else if (progressValue < 70) {
                youtubeProgressText.textContent = 'Đang download audio...';
            } else {
                youtubeProgressText.textContent = 'Đang xử lý file...';
            }
            youtubeProgressDetails.textContent = `Tiến trình: ${Math.round(progressValue)}%`;
        }, 1000);

        // Thêm timeout cho toàn bộ process
        const importController = new AbortController();
        window.importController = importController; // Lưu để cancel button có thể access
        const importTimeoutId = setTimeout(() => {
            importController.abort();
            console.error('⏰ [YouTube Import] Import timeout after 5 minutes');
            clearInterval(progressInterval);
            showToast('Import timeout! File có thể quá lớn hoặc network chậm.', 'error');
        }, 300000); // 5 minutes timeout

        try {
            // Step 1: Get YouTube info (preview) if not already available
            if (!currentImportInfo) {
                console.log('📋 [YouTube Import] Getting YouTube info first...');
                youtubeProgressText.textContent = 'Đang lấy thông tin YouTube...';
                
                const infoResponse = await fetch('/music/youtube/info/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': getCsrfToken()
                    },
                    body: JSON.stringify({ 
                        url: url,
                        import_playlist: importPlaylist
                    }),
                    signal: importController.signal
                });
                
                const infoData = await infoResponse.json();
                
                if (infoData.success) {
                    console.log('✅ [YouTube Import] Info retrieved successfully');
                    currentImportInfo = infoData.info;
                    
                    // Show preview info during import
                    renderYouTubePreview(infoData.info);
                    youtubePreviewSection.classList.remove('hidden');
                    
                    // Update progress
                    youtubeProgressFill.style.width = '30%';
                    youtubeProgressText.textContent = 'Thông tin đã lấy, bắt đầu download...';
                } else {
                    throw new Error(infoData.error || 'Không thể lấy thông tin từ YouTube');
                }
            }

            // Step 2: Start actual import
            console.log('🚀 [YouTube Import] Starting import request...');
            youtubeProgressText.textContent = 'Đang download audio...';
            
            const response = await fetch('/music/youtube/import/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCsrfToken()
                },
                body: JSON.stringify({
                    url: url,
                    playlist_id: playlistId,
                    extract_audio_only: audioOnly,
                    import_playlist: importPlaylist
                }),
                signal: importController.signal
            });
            
            clearTimeout(importTimeoutId);
            clearInterval(progressInterval);
            isCompleted = true; // ✅ Mark as completed to stop progress interval

            console.log('📡 [YouTube Import] Import response received:', {
                status: response.status,
                statusText: response.statusText,
                ok: response.ok
            });

            const data = await response.json();
            console.log('📊 [YouTube Import] Import response data:', data);

            if (data.success) {
                console.log('✅ [YouTube Import] Import successful!');
                youtubeProgressFill.style.width = '100%';
                youtubeProgressText.textContent = 'Import thành công!';
                youtubeProgressDetails.textContent = 'Đang cập nhật playlist...';
                
                // ✅ Hiển thị thông tin chi tiết về import
                let successMessage = 'Import thành công!';
                if (data.limit_info && data.limit_info.was_limited) {
                    successMessage = `Import thành công ${data.limit_info.imported_count}/${data.limit_info.max_limit} video đầu tiên (từ ${data.limit_info.original_count} video)`;
                }
                
                showToast(successMessage, 'success');
                
                // Refresh playlists and user music
                setTimeout(() => {
                    console.log('🔄 [YouTube Import] Refreshing playlists and user music...');
                    if (typeof window.musicPlayer.refreshPlaylists === 'function') {
                        window.musicPlayer.refreshPlaylists();
                    }
                    
                    if (typeof window.musicPlayer.loadUserTracks === 'function') {
                        window.musicPlayer.loadUserTracks();
                    } else if (typeof window.musicPlayer.loadUserMusic === 'function') {
                        window.musicPlayer.loadUserMusic();
                    }
                    
                    if (typeof window.musicPlayer.loadUserPlaylists === 'function') {
                        window.musicPlayer.loadUserPlaylists();
                    }
                    
                    // ✅ CRITICAL: Reload user playlists in main player to show new albums immediately
                    if (typeof window.musicPlayer.loadUserPlaylistsInMainPlayer === 'function') {
                        window.musicPlayer.loadUserPlaylistsInMainPlayer();
                    }
                    
                    // Refresh settings modal if exists
                    if (window.userMusicManager && typeof window.userMusicManager.refreshSettingsModal === 'function') {
                        window.userMusicManager.refreshSettingsModal();
                    }
                }, 1000);
                
                setTimeout(() => {
                    console.log('🏁 [YouTube Import] Closing modal and resetting...');
                    youtubeImportModal.classList.add('hidden');
                    resetYouTubeImportModal();
                }, 2000);
            } else {
                console.error('❌ [YouTube Import] Import failed:', data.error);
                
                // Kiểm tra nếu import bị hủy
                if (data.cancelled) {
                    console.log('🚫 [YouTube Import] Import was cancelled');
                    showToast('Import đã được hủy', 'warning');
                } else {
                    showToast(data.error || 'Lỗi khi import từ YouTube.', 'error');
                }
            }
        } catch (error) {
            console.error('💥 [YouTube Import] Import Error:', error);
            clearTimeout(importTimeoutId);
            clearInterval(progressInterval);
            isCompleted = true; // ✅ Mark as completed to stop progress interval
            
            // Xử lý các loại lỗi khác nhau
            if (error.name === 'AbortError') {
                // Kiểm tra nếu đây là cancel từ user
                console.log('🚫 [YouTube Import] Request was aborted');
                showToast('Import đã được hủy', 'warning');
            } else if (error.message.includes('Failed to fetch')) {
                showToast('Không thể kết nối đến server. Vui lòng kiểm tra kết nối internet.', 'error');
            } else if (error.message.includes('Không thể lấy thông tin')) {
                showToast('Không thể lấy thông tin từ YouTube. Vui lòng kiểm tra URL hoặc thử lại.', 'error');
            } else {
                showToast('Lỗi khi import từ YouTube. Vui lòng thử lại.', 'error');
            }
        } finally {
            clearTimeout(importTimeoutId);
            clearInterval(progressInterval);
            isCompleted = true; // ✅ Ensure completed flag is set
            youtubeImportStartBtn.disabled = false;
            youtubePreviewBtn.disabled = false;
            youtubeCancelBtn.disabled = false;
            // Don't hide progress immediately - let success/error handling do it
        }
    });

    // Cookie management event listeners
    uploadCookieBtn.addEventListener('click', () => {
        cookieFileInput.click();
    });

    cookieFileInput.addEventListener('change', async (event) => {
        const file = event.target.files[0];
        if (file) {
            await uploadCookieFile(file);
        }
    });

    deleteCookieBtn.addEventListener('click', async () => {
        await deleteCookieFile();
    });

    // Cancel import event listener
    cancelImportBtn.addEventListener('click', async () => {
        if (confirm('Bạn có chắc chắn muốn hủy import?')) {
            console.log('🚫 [YouTube Import] User requested cancellation');
            
            try {
                // Gọi API cancel thay vì chỉ abort request
                const response = await fetch('/music/youtube/cancel/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': getCsrfToken()
                    }
                });
                
                const data = await response.json();
                
                if (data.success) {
                    console.log('✅ [YouTube Import] Import cancelled successfully');
                    showToast('Import đã được hủy thành công', 'warning');
                    
                    // Reset UI
                    youtubeImportProgress.classList.add('hidden');
                    youtubeImportStartBtn.disabled = false;
                    youtubePreviewBtn.disabled = false;
                    youtubeCancelBtn.disabled = false;
                    
                    // Reset progress
                    youtubeProgressFill.style.width = '0%';
                    youtubeProgressText.textContent = '';
                    youtubeProgressDetails.textContent = '';
                } else {
                    console.error('❌ [YouTube Import] Cancel failed:', data.error);
                    showToast(data.error || 'Không thể hủy import', 'error');
                }
            } catch (error) {
                console.error('💥 [YouTube Import] Cancel error:', error);
                showToast('Lỗi khi hủy import', 'error');
            }
            
            // Fallback: vẫn abort request nếu có
            if (window.importController) {
                window.importController.abort();
            }
        }
    });

    // Paste button event listener
    pasteUrlBtn.addEventListener('click', async () => {
        try {
            console.log('📋 [Paste] Attempting to paste URL...');
            const text = await navigator.clipboard.readText();
            
            if (text && text.trim()) {
                // Check if it's a valid YouTube URL
                if (isValidYouTubeUrl(text.trim())) {
                    youtubeUrlInput.value = text.trim();
                    youtubeUrlInput.focus();
                    showToast('Đã dán URL thành công!', 'success');
                    console.log('✅ [Paste] URL pasted successfully:', text.trim());
                } else {
                    showToast('URL không hợp lệ. Vui lòng dán URL YouTube.', 'warning');
                    console.warn('⚠️ [Paste] Invalid URL pasted:', text.trim());
                }
            } else {
                showToast('Clipboard trống hoặc không có text.', 'warning');
                console.warn('⚠️ [Paste] Empty clipboard');
            }
        } catch (error) {
            console.error('💥 [Paste] Error reading clipboard:', error);
            showToast('Không thể đọc clipboard. Vui lòng copy URL và paste thủ công.', 'error');
        }
    });

    // Keyboard shortcut event listener
    document.addEventListener('keydown', (event) => {
        // Ctrl+I or Cmd+I to open import modal
        if ((event.ctrlKey || event.metaKey) && event.key === 'i') {
            event.preventDefault();
            console.log('⌨️ [Keyboard] Ctrl+I pressed - opening import modal');
            
            if (youtubeImportModal && youtubeImportModal.classList.contains('hidden')) {
                youtubeImportBtn.click();
                showToast('Mở Import từ YouTube', 'info');
            }
        }
        
        // Escape to close modal
        if (event.key === 'Escape') {
            if (youtubeImportModal && !youtubeImportModal.classList.contains('hidden')) {
                youtubeImportModal.classList.add('hidden');
                console.log('⌨️ [Keyboard] Escape pressed - closing modal');
            }
        }
        
        // Ctrl+V to paste in URL input when focused
        if ((event.ctrlKey || event.metaKey) && event.key === 'v') {
            if (document.activeElement === youtubeUrlInput) {
                // Let the default paste behavior happen, then validate
                setTimeout(() => {
                    const url = youtubeUrlInput.value.trim();
                    if (url && !isValidYouTubeUrl(url)) {
                        showToast('URL không hợp lệ. Vui lòng nhập URL YouTube.', 'warning');
                    }
                }, 100);
            }
        }
    });

    // --- Helper Functions ---
    function isValidYouTubeUrl(url) {
        const youtubePatterns = [
            /^https?:\/\/(www\.)?youtube\.com\/watch\?v=[\w-]+/,  // Single video (có thể có &list= cho radio mode)
            /^https?:\/\/(www\.)?youtube\.com\/playlist\?list=[\w-]+/,  // Playlist
            /^https?:\/\/youtu\.be\/[\w-]+/,  // Short URL
            /^https?:\/\/(www\.)?youtube\.com\/channel\/[\w-]+/,  // Channel
            /^https?:\/\/(www\.)?youtube\.com\/c\/[\w-]+/,  // Custom URL
            /^https?:\/\/(www\.)?youtube\.com\/user\/[\w-]+/,  // User URL
        ];
        return youtubePatterns.some(pattern => pattern.test(url));
    }

    async function populateYouTubePlaylistDropdown() {
        try {
            console.log('📋 [Playlist] Loading user playlists...');
            
            // Try different API endpoints
            const endpoints = [
                '/music/user/playlists/',  // ✅ Correct endpoint
                '/music/api/user-playlists/',
                '/music/api/playlists/',
                '/music/playlists/',
                '/api/user-playlists/',
                '/api/playlists/'
            ];
            
            let response = null;
            let data = null;
            
            for (const endpoint of endpoints) {
                try {
                    console.log(`📋 [Playlist] Trying endpoint: ${endpoint}`);
                    response = await fetch(endpoint);
                    if (response.ok) {
                        data = await response.json();
                        console.log(`✅ [Playlist] Success with endpoint: ${endpoint}`);
                        break;
                    }
                } catch (error) {
                    console.log(`❌ [Playlist] Failed endpoint: ${endpoint}`, error.message);
                    continue;
                }
            }
            
            if (!data) {
                console.warn('⚠️ [Playlist] No valid endpoint found, using fallback');
                // Fallback: create empty dropdown
                youtubePlaylistSelect.innerHTML = '<option value="">Không thêm vào playlist</option>';
                return;
            }
            
            function renderPlaylists(playlists) {
                youtubePlaylistSelect.innerHTML = '<option value="">Không thêm vào playlist</option>';
                if (playlists && playlists.length > 0) {
                    playlists.forEach(playlist => {
                        const option = document.createElement('option');
                        option.value = playlist.id;
                        option.textContent = playlist.name;
                        youtubePlaylistSelect.appendChild(option);
                    });
                }
            }
            
            if (data.success && data.playlists) {
                renderPlaylists(data.playlists);
            } else if (data.playlists) {
                renderPlaylists(data.playlists);
            } else {
                console.warn('⚠️ [Playlist] No playlists data found');
                youtubePlaylistSelect.innerHTML = '<option value="">Không thêm vào playlist</option>';
            }
        } catch (error) {
            console.error('💥 [Playlist] Error loading playlists:', error);
            // Fallback: create empty dropdown
            youtubePlaylistSelect.innerHTML = '<option value="">Không thêm vào playlist</option>';
        }
    }

    function renderYouTubePreview(info) {
        youtubePreviewContent.innerHTML = '';
        
        // ✅ Hiển thị cảnh báo nếu có
        if (info.warning) {
            const warningDiv = document.createElement('div');
            warningDiv.className = 'youtube-warning';
            warningDiv.innerHTML = `
                <div class="warning-content">
                    <i class="bi bi-exclamation-triangle"></i>
                    <span>${info.warning}</span>
                </div>
            `;
            youtubePreviewContent.appendChild(warningDiv);
        }
        
        if (info.type === 'video') {
            const videoDiv = document.createElement('div');
            videoDiv.className = 'youtube-preview-item';
            videoDiv.innerHTML = `
                <div class="preview-thumbnail">
                    <img src="${info.thumbnail}" alt="${info.title}" onerror="this.style.display='none'">
                </div>
                <div class="preview-info">
                    <h4>${info.title}</h4>
                    <p><strong>Kênh:</strong> ${info.uploader}</p>
                    <p><strong>Thời lượng:</strong> ${info.duration_formatted}</p>
                    <p><strong>Loại:</strong> Video đơn lẻ</p>
                </div>
            `;
            youtubePreviewContent.appendChild(videoDiv);
        } else if (info.type === 'playlist') {
            const playlistDiv = document.createElement('div');
            playlistDiv.className = 'youtube-preview-item';
            playlistDiv.innerHTML = `
                <div class="preview-thumbnail">
                    <img src="${info.thumbnail}" alt="${info.title}" onerror="this.style.display='none'">
                </div>
                <div class="preview-info">
                    <h4>${info.title}</h4>
                    <p><strong>Kênh:</strong> ${info.uploader}</p>
                    <p><strong>Số video:</strong> ${info.entry_count}</p>
                    <p><strong>Loại:</strong> Playlist</p>
                </div>
            `;
            youtubePreviewContent.appendChild(playlistDiv);
            
            // Show first 5 videos
            if (info.entries && info.entries.length > 0) {
                const entriesDiv = document.createElement('div');
                entriesDiv.className = 'playlist-entries';
                entriesDiv.innerHTML = '<h5>Danh sách video:</h5>';
                
                info.entries.slice(0, 5).forEach(entry => {
                    const entryDiv = document.createElement('div');
                    entryDiv.className = 'playlist-entry';
                    entryDiv.innerHTML = `
                        <div class="entry-thumbnail">
                            <img src="${entry.thumbnail}" alt="${entry.title}" onerror="this.style.display='none'">
                        </div>
                        <div class="entry-info">
                            <h6>${entry.title}</h6>
                            <p><strong>Kênh:</strong> ${entry.uploader}</p>
                            <p><strong>Thời lượng:</strong> ${entry.duration_formatted}</p>
                        </div>
                    `;
                    entriesDiv.appendChild(entryDiv);
                });
                
                if (info.entry_count > 5) {
                    const moreDiv = document.createElement('div');
                    moreDiv.className = 'more-entries';
                    moreDiv.textContent = `... và ${info.entry_count - 5} video khác`;
                    entriesDiv.appendChild(moreDiv);
                }
                
                youtubePreviewContent.appendChild(entriesDiv);
            }
        }
    }

    function resetYouTubeImportModal() {
        youtubeUrlInput.value = '';
        youtubePlaylistSelect.value = '';
        youtubePreviewSection.classList.add('hidden');
        youtubeImportProgress.classList.add('hidden');
        youtubeImportStartBtn.disabled = false; // ✅ Enable Import button by default
        youtubePreviewBtn.disabled = false;
        youtubeCancelBtn.disabled = false;
        currentImportInfo = null;
        
        // ✅ CRITICAL: Clear preview content to remove old info
        if (youtubePreviewContent) {
            youtubePreviewContent.innerHTML = '';
        }
        
        // ✅ CRITICAL: Reset progress bar to 0%
        if (youtubeProgressFill) {
            youtubeProgressFill.style.width = '0%';
        }
        if (youtubeProgressText) {
            youtubeProgressText.textContent = '';
        }
        if (youtubeProgressDetails) {
            youtubeProgressDetails.textContent = '';
        }
    }

    async function loadCookieStatus() {
        try {
            console.log('🍪 [Cookie] Loading cookie status...');
            const response = await fetch('/music/youtube/cookie/status/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCsrfToken()
                }
            });
            
            console.log('🍪 [Cookie] Status response:', {
                status: response.status,
                ok: response.ok
            });
            
            const data = await response.json();
            console.log('🍪 [Cookie] Status data:', data);
            
            if (data.success) {
                updateCookieStatusUI(data);
                console.log('✅ [Cookie] Status loaded successfully');
            } else {
                console.error('❌ [Cookie] Status error:', data.error);
            }
        } catch (error) {
            console.error('💥 [Cookie] Status error:', error);
        }
    }

    function updateCookieStatusUI(status) {
        const statusText = cookieStatus.querySelector('.cookie-status-text span');
        const deleteBtn = deleteCookieBtn;
        
        if (status.has_cookie && status.is_valid) {
            cookieStatus.className = 'cookie-status success';
            statusText.innerHTML = `
                <i class="bi bi-check-circle"></i>
                Cookie hợp lệ
                <span>${status.file_name}</span>
            `;
            deleteBtn.style.display = 'inline-flex';
        } else if (status.has_cookie && !status.is_valid) {
            cookieStatus.className = 'cookie-status warning';
            statusText.innerHTML = `
                <i class="bi bi-exclamation-triangle"></i>
                Cookie không hợp lệ hoặc đã hết hạn
            `;
            deleteBtn.style.display = 'inline-flex';
        } else {
            cookieStatus.className = 'cookie-status info';
            statusText.innerHTML = `
                Chưa có cookie. Upload cookie để tránh bị YouTube chặn.
            `;
            deleteBtn.style.display = 'none';
        }
    }

    async function uploadCookieFile(file) {
        try {
            console.log('🍪 [Cookie] Uploading file:', file.name);
            const formData = new FormData();
            formData.append('cookie_file', file);
            
            const response = await fetch('/music/youtube/cookie/upload/', {
                method: 'POST',
                headers: {
                    'X-CSRFToken': getCsrfToken()
                },
                body: formData
            });
            
            const data = await response.json();
            
            if (data.success) {
                showToast('Cookie đã được upload thành công!', 'success');
                loadCookieStatus(); // Reload status
            } else {
                showToast(data.error || 'Lỗi khi upload cookie.', 'error');
            }
        } catch (error) {
            console.error('💥 [Cookie] Upload error:', error);
            showToast('Lỗi khi upload cookie.', 'error');
        }
    }

    async function deleteCookieFile() {
        try {
            console.log('🍪 [Cookie] Deleting cookie file');
            const response = await fetch('/music/youtube/cookie/delete/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCsrfToken()
                }
            });
            
            const data = await response.json();
            
            if (data.success) {
                showToast('Cookie đã được xóa!', 'success');
                loadCookieStatus(); // Reload status
            } else {
                showToast(data.error || 'Lỗi khi xóa cookie.', 'error');
            }
        } catch (error) {
            console.error('💥 [Cookie] Delete error:', error);
            showToast('Lỗi khi xóa cookie.', 'error');
        }
    }

    function getCsrfToken() {
        const csrfElement = document.querySelector('[name=csrfmiddlewaretoken]');
        if (csrfElement) {
            return csrfElement.value;
        }
        
        // Fallback: try to get from meta tag
        const metaCsrf = document.querySelector('meta[name=csrf-token]');
        if (metaCsrf) {
            return metaCsrf.getAttribute('content');
        }
        
        // Fallback: try to get from cookie
        const cookies = document.cookie.split(';');
        for (let cookie of cookies) {
            const [name, value] = cookie.trim().split('=');
            if (name === 'csrftoken') {
                return value;
            }
        }
        
        console.warn('⚠️ [CSRF] No CSRF token found');
        return '';
    }

    function showToast(message, type = 'info') {
        // Create toast notification
        const notification = document.createElement('div');
        notification.className = `toast-notification ${type}`;
        notification.innerHTML = `
            <div class="toast-content">
                <i class="bi bi-${type === 'success' ? 'check-circle' : type === 'error' ? 'x-circle' : type === 'warning' ? 'exclamation-triangle' : 'info-circle'}"></i>
                <span>${message}</span>
            </div>
        `;
        
        // Add to page
        document.body.appendChild(notification);
        
        // Animate in
        setTimeout(() => {
            notification.style.transform = 'translateX(-50%) translateY(0)';
            notification.style.opacity = '1';
        }, 10);
        
        // Animate out and remove
        setTimeout(() => {
            notification.style.transform = 'translateX(-50%) translateY(-100px)';
            notification.style.opacity = '0';
            setTimeout(() => notification.remove(), 300);
        }, 3000);
    }

});

// Fallback: Initialize immediately if DOM is already loaded
if (document.readyState === 'loading') {
    console.log('⏳ [YouTube Import] DOM still loading, waiting...');
} else {
    console.log('⚡ [YouTube Import] DOM already loaded, initializing immediately...');
    // Re-run the initialization
    setTimeout(() => {
        const youtubeImportBtn = document.getElementById('youtube-import-btn');
        if (youtubeImportBtn && !youtubeImportBtn.hasAttribute('data-initialized')) {
            console.log('🔄 [YouTube Import] Re-initializing...');
            youtubeImportBtn.setAttribute('data-initialized', 'true');
            youtubeImportBtn.addEventListener('click', () => {
                console.log('🎯 [YouTube Import] Import button clicked (fallback)!');
                const modal = document.getElementById('youtube-import-modal');
                if (modal) {
                    modal.classList.remove('hidden');
                    console.log('✅ [YouTube Import] Modal opened (fallback)');
                }
            });
        }
    }, 100);
}