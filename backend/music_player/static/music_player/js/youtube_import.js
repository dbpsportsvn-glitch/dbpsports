/**
 * YouTube Import Handler - Simple Version
 * Xử lý import audio từ YouTube videos/playlists
 */

document.addEventListener('DOMContentLoaded', () => {
    console.log('YouTube Import Handler loaded');
    
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

    let currentImportInfo = null;

    // Check if elements exist
    if (!youtubeImportBtn || !youtubeImportModal) {
        console.error('YouTube Import elements not found');
        return;
    }

    // --- Event Listeners ---
    youtubeImportBtn.addEventListener('click', () => {
        console.log('Opening YouTube Import modal');
        youtubeImportModal.classList.remove('hidden');
        populateYouTubePlaylistDropdown();
        resetYouTubeImportModal();
    });

    youtubeImportCloseBtn.addEventListener('click', () => {
        youtubeImportModal.classList.add('hidden');
    });

    youtubeCancelBtn.addEventListener('click', () => {
        youtubeImportModal.classList.add('hidden');
    });

    youtubeUrlInput.addEventListener('input', () => {
        youtubePreviewBtn.disabled = !youtubeUrlInput.value.trim();
        youtubeImportStartBtn.disabled = true;
        youtubePreviewSection.classList.add('hidden');
        youtubePreviewContent.innerHTML = '';
        youtubeImportProgress.classList.add('hidden');
    });

    youtubePreviewBtn.addEventListener('click', async () => {
        const url = youtubeUrlInput.value.trim();
        console.log('Preview clicked for URL:', url);
        
        if (!url) {
            showToast('Vui lòng nhập URL YouTube.', 'error');
            return;
        }
        
        if (!isValidYouTubeUrl(url)) {
            showToast('URL YouTube không hợp lệ.', 'error');
            return;
        }
        
        youtubePreviewBtn.disabled = true;
        youtubePreviewBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Đang tải...';
        youtubePreviewSection.classList.add('hidden');
        youtubePreviewContent.innerHTML = '';
        youtubeImportStartBtn.disabled = true;
        youtubeImportProgress.classList.add('hidden');

               try {
                   console.log('Fetching YouTube info for:', url);
                   const importPlaylist = importPlaylistCheckbox.checked;
                   console.log('Import playlist checkbox:', importPlaylist);
                   const response = await fetch('/music/youtube/info/', {
                       method: 'POST',
                       headers: {
                           'Content-Type': 'application/json',
                           'X-CSRFToken': getCsrfToken()
                       },
                       body: JSON.stringify({ 
                           url: url,
                           import_playlist: importPlaylist
                       })
                   });

            console.log('Response status:', response.status);
            const data = await response.json();
            console.log('Response data:', data);

            if (data.success) {
                currentImportInfo = data.info;
                renderYouTubePreview(data.info);
                youtubePreviewSection.classList.remove('hidden');
                youtubeImportStartBtn.disabled = false;
                showToast('Đã tải thông tin thành công!', 'success');
            } else {
                console.error('API Error:', data.error);
                showToast(data.error || 'Lỗi khi tải thông tin YouTube.', 'error');
            }
        } catch (error) {
            console.error('Error fetching YouTube info:', error);
            showToast('Lỗi mạng hoặc server khi tải thông tin YouTube.', 'error');
        } finally {
            youtubePreviewBtn.disabled = false;
            youtubePreviewBtn.innerHTML = '<i class="bi bi-eye"></i> Xem Trước';
        }
    });

    youtubeImportStartBtn.addEventListener('click', async () => {
        if (!currentImportInfo) {
            showToast('Vui lòng xem trước trước khi import.', 'error');
            return;
        }

               const url = youtubeUrlInput.value.trim();
               const playlistId = youtubePlaylistSelect.value || null;
               const audioOnly = extractAudioOnlyCheckbox.checked;
               const importPlaylist = importPlaylistCheckbox.checked;

        console.log('Starting import for:', url);

        youtubeImportStartBtn.disabled = true;
        youtubePreviewBtn.disabled = true;
        youtubeCancelBtn.disabled = true;
        youtubeImportProgress.classList.remove('hidden');
        youtubeProgressFill.style.width = '0%';
        youtubeProgressText.textContent = 'Đang chuẩn bị import...';
        youtubeProgressDetails.textContent = '';

        // Start progress tracking
        const progressInterval = setInterval(async () => {
            try {
                const response = await fetch('/music/youtube/progress/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': getCsrfToken()
                    },
                    body: JSON.stringify({})
                });
                const data = await response.json();
                if (data.success) {
                    youtubeProgressFill.style.width = `${data.progress}%`;
                    youtubeProgressText.textContent = data.message;
                    youtubeProgressDetails.textContent = `Tiến trình: ${data.progress}%`;
                }
            } catch (error) {
                console.error('Progress tracking error:', error);
            }
        }, 1000);

        try {
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
                       })
            });

            const data = await response.json();
            console.log('Import response:', data);

                   if (data.success) {
                       youtubeProgressFill.style.width = '100%';
                       youtubeProgressText.textContent = 'Hoàn thành!';
                       youtubeProgressDetails.textContent = 'Import thành công!';
                       
                       // Log errors if any
                       if (data.errors && data.errors.length > 0) {
                           console.error('Import errors:', data.errors);
                           data.errors.forEach(error => {
                               console.error('Error:', error);
                           });
                       }
                       
                       // Log debug info
                       if (data.debug_info) {
                           console.log('Debug info:', data.debug_info);
                           console.log('Downloaded files:', data.debug_info.downloaded_files);
                           console.log('Created tracks:', data.debug_info.created_count);
                           console.log('Errors:', data.debug_info.error_count);
                       }
                       
                       // Log album info
                       if (data.album) {
                           console.log('Album info:', data.album);
                           if (data.album.created) {
                               console.log(`✅ Created new album: ${data.album.name} (ID: ${data.album.id})`);
                           } else {
                               console.log(`📁 Added to existing playlist: ${data.album.name} (ID: ${data.album.id})`);
                           }
                       }
                       
                       setTimeout(async () => {
                           let successMessage = data.message || 'Import YouTube thành công!';
                           if (data.album && data.album.created) {
                               successMessage += ` Album "${data.album.name}" đã được tạo và hiển thị trong mục cá nhân.`;
                           }
                           showToast(successMessage, 'success');
                           youtubeImportModal.classList.add('hidden');
                           
                           // ✅ Trigger comprehensive UI refresh after YouTube import
                           try {
                               // Refresh music player data
                               if (window.musicPlayer) {
                                   // Refresh playlists first
                                   if (typeof window.musicPlayer.refreshPlaylists === 'function') {
                                       await window.musicPlayer.refreshPlaylists();
                                   }
                                   
                                   // Refresh user tracks
                                   if (typeof window.musicPlayer.loadUserTracks === 'function') {
                                       await window.musicPlayer.loadUserTracks();
                                   } else if (typeof window.musicPlayer.loadUserMusic === 'function') {
                                       await window.musicPlayer.loadUserMusic();
                                   }
                                   
                                   // Refresh user playlists
                                   if (typeof window.musicPlayer.loadUserPlaylists === 'function') {
                                       await window.musicPlayer.loadUserPlaylists();
                                   }
                                   
                                   console.log('✅ Music player UI refreshed after YouTube import');
                               }
                               
                               // ✅ Trigger Settings modal refresh if UserMusicManager exists
                               if (window.userMusicManager && typeof window.userMusicManager.refreshSettingsModal === 'function') {
                                   await window.userMusicManager.refreshSettingsModal();
                                   console.log('✅ Settings modal refreshed after YouTube import');
                               }
                               
                               // ✅ Dispatch custom event to notify other components
                               window.dispatchEvent(new CustomEvent('youtubeImportCompleted', {
                                   detail: { success: true, album: data.album }
                               }));
                               
                           } catch (error) {
                               console.error('❌ Error refreshing UI after YouTube import:', error);
                           }
                       }, 1000);
            } else {
                showToast(data.error || 'Lỗi khi import từ YouTube.', 'error');
            }
        } catch (error) {
            console.error('Error importing from YouTube:', error);
            showToast('Lỗi mạng hoặc server khi import từ YouTube.', 'error');
        } finally {
            clearInterval(progressInterval);
            youtubeImportStartBtn.disabled = false;
            youtubePreviewBtn.disabled = false;
            youtubeCancelBtn.disabled = false;
            youtubeImportProgress.classList.add('hidden');
            resetYouTubeImportModal();
        }
    });

    // --- Helper Functions ---
    function isValidYouTubeUrl(url) {
        const youtubePatterns = [
            /^https?:\/\/(www\.)?youtube\.com\/watch\?v=[\w-]+/,  // Single video (có thể có &list= cho radio mode)
            /^https?:\/\/(www\.)?youtube\.com\/playlist\?list=[\w-]+/,  // Playlist thực sự
            /^https?:\/\/(www\.)?youtu\.be\/[\w-]+/,  // Short URL
            /^https?:\/\/(www\.)?youtube\.com\/channel\/[\w-]+/,  // Channel
            /^https?:\/\/(www\.)?youtube\.com\/c\/[\w-]+/,  // Custom channel
            /^https?:\/\/(www\.)?youtube\.com\/user\/[\w-]+/  // User channel
        ];
        
        return youtubePatterns.some(pattern => pattern.test(url));
    }

    async function populateYouTubePlaylistDropdown() {
        try {
            const response = await fetch('/music/user/playlists/');
            const data = await response.json();
            if (data.success) {
                renderPlaylists(data.playlists);
            } else {
                console.error('Failed to load user playlists:', data.error);
            }
        } catch (error) {
            console.error('Network error loading user playlists:', error);
        }

        function renderPlaylists(playlists) {
            youtubePlaylistSelect.innerHTML = '<option value="">-- Không thêm vào playlist --</option>';
            playlists.forEach(playlist => {
                const option = document.createElement('option');
                option.value = playlist.id;
                option.textContent = playlist.name;
                youtubePlaylistSelect.appendChild(option);
            });
        }
    }

       function renderYouTubePreview(info) {
           youtubePreviewContent.innerHTML = '';
           
           if (info.type === 'video' || info.import_mode === 'single') {
               // Single video preview
               youtubePreviewContent.innerHTML = `
                   <div class="video-preview">
                       <div class="preview-thumbnail">
                           <img src="${info.thumbnail}" alt="Thumbnail" width="120">
                       </div>
                       <div class="preview-info">
                           <h6 class="text-white">${info.title}</h6>
                           <div class="preview-meta">
                               <span class="meta-item"><i class="bi bi-person-fill"></i> ${info.uploader}</span>
                               <span class="meta-item"><i class="bi bi-clock-fill"></i> ${info.duration_formatted}</span>
                           </div>
                           <div class="single-video-note">
                               <i class="bi bi-info-circle"></i>
                               <small>Chỉ import video đơn lẻ này</small>
                           </div>
                       </div>
                   </div>
               `;
           } else if (info.type === 'playlist' && info.import_mode === 'playlist') {
               // Playlist preview
               let entriesHtml = info.entries.map(entry => `
                   <div class="playlist-video-item">
                       <img src="${entry.thumbnail}" alt="Thumbnail" width="60" height="auto" style="border-radius: 4px;">
                       <div class="video-info">
                           <div class="video-title">${entry.title}</div>
                           <div class="video-meta">
                               <span>${entry.uploader}</span>
                               <span>•</span>
                               <span>${entry.duration_formatted}</span>
                           </div>
                       </div>
                   </div>
               `).join('');
   
               if (info.entry_count > info.entries.length) {
                   entriesHtml += `<div class="more-videos">Và ${info.entry_count - info.entries.length} video khác...</div>`;
               }
   
               youtubePreviewContent.innerHTML = `
                   <div class="playlist-preview">
                       <div class="playlist-header">
                           <h6 class="text-white">${info.title}</h6>
                           <div class="playlist-meta">
                               <span class="meta-item"><i class="bi bi-person-fill"></i> ${info.uploader}</span>
                               <span class="meta-item"><i class="bi bi-collection-play-fill"></i> ${info.entry_count} bài hát</span>
                           </div>
                           <div class="playlist-note">
                               <i class="bi bi-info-circle"></i>
                               <small>Tất cả bài hát sẽ được import với album: "${info.title}"</small>
                           </div>
                       </div>
                       <div class="playlist-videos">
                           ${entriesHtml}
                       </div>
                   </div>
               `;
           }
       }

       function resetYouTubeImportModal() {
           youtubeUrlInput.value = '';
           youtubePlaylistSelect.value = '';
           extractAudioOnlyCheckbox.checked = true;
           importPlaylistCheckbox.checked = false;  // Mặc định: import file đơn lẻ
           youtubePreviewBtn.disabled = true;
           youtubeImportStartBtn.disabled = true;
           youtubePreviewSection.classList.add('hidden');
           youtubePreviewContent.innerHTML = '';
           youtubeImportProgress.classList.add('hidden');
           currentImportInfo = null;
       }

    function getCsrfToken() {
        const token = document.querySelector('[name=csrfmiddlewaretoken]');
        return token ? token.value : '';
    }

    function showToast(message, type = 'info') {
        console.log(`Toast ${type}:`, message);
        
        // Create toast container if not exists
        let toastContainer = document.getElementById('toast-container');
        if (!toastContainer) {
            toastContainer = document.createElement('div');
            toastContainer.id = 'toast-container';
            Object.assign(toastContainer.style, {
                position: 'fixed',
                top: '20px',
                right: '20px',
                zIndex: '10001',
                display: 'flex',
                flexDirection: 'column',
                gap: '10px'
            });
            document.body.appendChild(toastContainer);
        }

        const toast = document.createElement('div');
        toast.className = `toast-notification toast-${type}`;
        toast.textContent = message;
        
        // Style the toast
        Object.assign(toast.style, {
            background: type === 'error' ? '#ff6b6b' : type === 'success' ? '#51cf66' : '#339af0',
            color: 'white',
            padding: '12px 20px',
            borderRadius: '8px',
            boxShadow: '0 4px 12px rgba(0,0,0,0.3)',
            fontSize: '14px',
            fontWeight: '500',
            maxWidth: '300px',
            wordWrap: 'break-word'
        });
        
        toastContainer.appendChild(toast);
        
        setTimeout(() => {
            toast.remove();
        }, 3000);
    }

    console.log('YouTube Import Handler initialized successfully');
});