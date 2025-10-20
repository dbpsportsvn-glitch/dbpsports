from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.db import models
import os
import json
import mimetypes
from .models import Playlist, Track


@staff_member_required
def music_admin(request):
    """Trang quản lý music player cho admin"""
    playlists = Playlist.objects.all().order_by('name')
    
    context = {
        'playlists': playlists,
        'title': 'Quản lý Music Player'
    }
    
    return render(request, 'music_player/admin/music_admin.html', context)


@staff_member_required
def create_playlist(request):
    """Tạo playlist mới"""
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description', '')
        folder_path = request.POST.get('folder_path')
        
        if not name:
            messages.error(request, 'Tên playlist là bắt buộc.')
            return redirect('music_player:admin')
        
        try:
            # Tạo thư mục playlist nếu chưa có
            playlist_folder = os.path.join('media', 'music', 'playlist', name.lower().replace(' ', '_'))
            os.makedirs(playlist_folder, exist_ok=True)
            
            playlist = Playlist.objects.create(
                name=name,
                description=description,
                folder_path=os.path.abspath(playlist_folder),
                is_active=True
            )
            messages.success(request, f'Đã tạo playlist "{name}" thành công.')
        except Exception as e:
            messages.error(request, f'Lỗi khi tạo playlist: {str(e)}')
        
        return redirect('music_player:admin')
    
    return redirect('music_player:admin')


@staff_member_required
@csrf_exempt
@require_http_methods(["POST"])
def upload_music_files(request, playlist_id):
    """Upload file nhạc vào playlist"""
    try:
        playlist = Playlist.objects.get(id=playlist_id)
        
        if 'files' not in request.FILES:
            return JsonResponse({
                'success': False,
                'error': 'Không có file nào được chọn'
            }, status=400)
        
        files = request.FILES.getlist('files')
        uploaded_count = 0
        errors = []
        
        # Lấy thứ tự hiện tại
        max_order = Track.objects.filter(playlist=playlist).aggregate(
            max_order=models.Max('order')
        )['max_order'] or 0
        
        for file in files:
            try:
                # Kiểm tra định dạng file
                if not file.name.lower().endswith(('.mp3', '.wav', '.ogg', '.m4a', '.aac')):
                    errors.append(f'{file.name}: Định dạng file không được hỗ trợ')
                    continue
                
                # Lưu file vào thư mục playlist
                file_path = os.path.join(playlist.folder_path, file.name)
                with open(file_path, 'wb') as destination:
                    for chunk in file.chunks():
                        destination.write(chunk)
                
                # Tách tên file thành title và artist
                name_without_ext = os.path.splitext(file.name)[0]
                if ' - ' in name_without_ext:
                    artist, title = name_without_ext.split(' - ', 1)
                else:
                    artist = ''
                    title = name_without_ext
                
                # Tạo track record
                Track.objects.create(
                    playlist=playlist,
                    title=title.strip(),
                    artist=artist.strip() if artist else None,
                    file_path=file_path,
                    order=max_order + uploaded_count + 1,
                    duration=0  # Sẽ được cập nhật sau
                )
                
                uploaded_count += 1
                
            except Exception as e:
                errors.append(f'{file.name}: {str(e)}')
                continue
        
        return JsonResponse({
            'success': True,
            'message': f'Đã upload thành công {uploaded_count} file',
            'uploaded_count': uploaded_count,
            'errors': errors
        })
        
    except Playlist.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Playlist không tồn tại'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@staff_member_required
def scan_playlist(request, playlist_id):
    """Scan thư mục playlist và tự động thêm tracks"""
    playlist = get_object_or_404(Playlist, id=playlist_id)
    
    try:
        folder_path = playlist.folder_path
        
        if not os.path.exists(folder_path):
            messages.error(request, 'Thư mục không tồn tại.')
            return redirect('music_player:admin')
        
        # Lấy danh sách file nhạc
        audio_extensions = ['.mp3', '.wav', '.ogg', '.m4a', '.aac']
        files = []
        
        for file in os.listdir(folder_path):
            if any(file.lower().endswith(ext) for ext in audio_extensions):
                files.append(file)
        
        files.sort()
        
        # Xóa tracks cũ
        Track.objects.filter(playlist=playlist).delete()
        
        # Thêm tracks mới
        added_count = 0
        for i, file in enumerate(files):
            try:
                # Tách tên file thành title và artist
                name_without_ext = os.path.splitext(file)[0]
                if ' - ' in name_without_ext:
                    artist, title = name_without_ext.split(' - ', 1)
                else:
                    artist = ''
                    title = name_without_ext
                
                Track.objects.create(
                    playlist=playlist,
                    title=title.strip(),
                    artist=artist.strip() if artist else None,
                    file_path=os.path.join(folder_path, file),
                    order=i + 1
                )
                added_count += 1
            except Exception as e:
                # Error adding track
                continue
        
        messages.success(request, f'Đã scan thành công {added_count} bài hát từ playlist "{playlist.name}".')
        
    except Exception as e:
        messages.error(request, f'Lỗi khi scan playlist: {str(e)}')
    
    return redirect('music_player:admin')


@staff_member_required
def delete_playlist(request, playlist_id):
    """Xóa playlist"""
    playlist = get_object_or_404(Playlist, id=playlist_id)
    
    try:
        playlist_name = playlist.name
        playlist.delete()
        messages.success(request, f'Đã xóa playlist "{playlist_name}" thành công.')
    except Exception as e:
        messages.error(request, f'Lỗi khi xóa playlist: {str(e)}')
    
    return redirect('music_player:admin')


@staff_member_required
def toggle_playlist_status(request, playlist_id):
    """Bật/tắt playlist"""
    playlist = get_object_or_404(Playlist, id=playlist_id)
    
    try:
        playlist.is_active = not playlist.is_active
        playlist.save()
        status = "kích hoạt" if playlist.is_active else "tắt"
        messages.success(request, f'Đã {status} playlist "{playlist.name}".')
    except Exception as e:
        messages.error(request, f'Lỗi khi cập nhật trạng thái playlist: {str(e)}')
    
    return redirect('music_player:admin')


@staff_member_required
@csrf_exempt
@require_http_methods(["POST"])
def api_scan_playlist(request, playlist_id):
    """API endpoint để scan playlist"""
    try:
        playlist = Playlist.objects.get(id=playlist_id)
        folder_path = playlist.folder_path
        
        if not os.path.exists(folder_path):
            return JsonResponse({
                'success': False,
                'error': 'Folder not found'
            }, status=404)
        
        # Lấy danh sách file nhạc
        audio_extensions = ['.mp3', '.wav', '.ogg', '.m4a', '.aac']
        files = []
        
        for file in os.listdir(folder_path):
            if any(file.lower().endswith(ext) for ext in audio_extensions):
                files.append(file)
        
        files.sort()
        
        # Xóa tracks cũ
        Track.objects.filter(playlist=playlist).delete()
        
        # Thêm tracks mới
        added_count = 0
        for i, file in enumerate(files):
            try:
                # Tách tên file thành title và artist
                name_without_ext = os.path.splitext(file)[0]
                if ' - ' in name_without_ext:
                    artist, title = name_without_ext.split(' - ', 1)
                else:
                    artist = ''
                    title = name_without_ext
                
                Track.objects.create(
                    playlist=playlist,
                    title=title.strip(),
                    artist=artist.strip() if artist else None,
                    file_path=os.path.join(folder_path, file),
                    order=i + 1
                )
                added_count += 1
            except Exception as e:
                # Error adding track
                continue
        
        return JsonResponse({
            'success': True,
            'message': f'Scanned {added_count} tracks successfully',
            'tracks_count': added_count
        })
        
    except Playlist.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Playlist not found'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@staff_member_required
def music_admin(request):
    """Trang quản lý music player cho admin"""
    playlists = Playlist.objects.all().order_by('name')
    
    context = {
        'playlists': playlists,
        'title': 'Quản lý Music Player'
    }
    
    return render(request, 'music_player/admin/music_admin.html', context)


@staff_member_required
def create_playlist(request):
    """Tạo playlist mới"""
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description', '')
        folder_path = request.POST.get('folder_path')
        
        if not name or not folder_path:
            messages.error(request, 'Tên playlist và đường dẫn thư mục là bắt buộc.')
            return redirect('music_player:admin')
        
        if not os.path.exists(folder_path):
            messages.error(request, 'Thư mục không tồn tại.')
            return redirect('music_player:admin')
        
        try:
            playlist = Playlist.objects.create(
                name=name,
                description=description,
                folder_path=folder_path
            )
            messages.success(request, f'Đã tạo playlist "{name}" thành công.')
        except Exception as e:
            messages.error(request, f'Lỗi khi tạo playlist: {str(e)}')
        
        return redirect('music_player:admin')
    
    return redirect('music_player:admin')


@staff_member_required
def scan_playlist(request, playlist_id):
    """Scan thư mục playlist và tự động thêm tracks"""
    playlist = get_object_or_404(Playlist, id=playlist_id)
    
    try:
        folder_path = playlist.folder_path
        
        if not os.path.exists(folder_path):
            messages.error(request, 'Thư mục không tồn tại.')
            return redirect('music_player:admin')
        
        # Lấy danh sách file nhạc
        audio_extensions = ['.mp3', '.wav', '.ogg', '.m4a', '.aac']
        files = []
        
        for file in os.listdir(folder_path):
            if any(file.lower().endswith(ext) for ext in audio_extensions):
                files.append(file)
        
        files.sort()
        
        # Xóa tracks cũ
        Track.objects.filter(playlist=playlist).delete()
        
        # Thêm tracks mới
        added_count = 0
        for i, file in enumerate(files):
            try:
                # Tách tên file thành title và artist
                name_without_ext = os.path.splitext(file)[0]
                if ' - ' in name_without_ext:
                    artist, title = name_without_ext.split(' - ', 1)
                else:
                    artist = ''
                    title = name_without_ext
                
                Track.objects.create(
                    playlist=playlist,
                    title=title.strip(),
                    artist=artist.strip() if artist else None,
                    file_path=os.path.join(folder_path, file),
                    order=i + 1
                )
                added_count += 1
            except Exception as e:
                # Error adding track
                continue
        
        messages.success(request, f'Đã scan thành công {added_count} bài hát từ playlist "{playlist.name}".')
        
    except Exception as e:
        messages.error(request, f'Lỗi khi scan playlist: {str(e)}')
    
    return redirect('music_player:admin')


@staff_member_required
def delete_playlist(request, playlist_id):
    """Xóa playlist"""
    playlist = get_object_or_404(Playlist, id=playlist_id)
    
    try:
        playlist_name = playlist.name
        playlist.delete()
        messages.success(request, f'Đã xóa playlist "{playlist_name}" thành công.')
    except Exception as e:
        messages.error(request, f'Lỗi khi xóa playlist: {str(e)}')
    
    return redirect('music_player:admin')


@staff_member_required
def toggle_playlist_status(request, playlist_id):
    """Bật/tắt playlist"""
    playlist = get_object_or_404(Playlist, id=playlist_id)
    
    try:
        playlist.is_active = not playlist.is_active
        playlist.save()
        status = "kích hoạt" if playlist.is_active else "tắt"
        messages.success(request, f'Đã {status} playlist "{playlist.name}".')
    except Exception as e:
        messages.error(request, f'Lỗi khi cập nhật trạng thái playlist: {str(e)}')
    
    return redirect('music_player:admin')


@staff_member_required
@csrf_exempt
@require_http_methods(["POST"])
def api_scan_playlist(request, playlist_id):
    """API endpoint để scan playlist"""
    try:
        playlist = Playlist.objects.get(id=playlist_id)
        folder_path = playlist.folder_path
        
        if not os.path.exists(folder_path):
            return JsonResponse({
                'success': False,
                'error': 'Folder not found'
            }, status=404)
        
        # Lấy danh sách file nhạc
        audio_extensions = ['.mp3', '.wav', '.ogg', '.m4a', '.aac']
        files = []
        
        for file in os.listdir(folder_path):
            if any(file.lower().endswith(ext) for ext in audio_extensions):
                files.append(file)
        
        files.sort()
        
        # Xóa tracks cũ
        Track.objects.filter(playlist=playlist).delete()
        
        # Thêm tracks mới
        added_count = 0
        for i, file in enumerate(files):
            try:
                # Tách tên file thành title và artist
                name_without_ext = os.path.splitext(file)[0]
                if ' - ' in name_without_ext:
                    artist, title = name_without_ext.split(' - ', 1)
                else:
                    artist = ''
                    title = name_without_ext
                
                Track.objects.create(
                    playlist=playlist,
                    title=title.strip(),
                    artist=artist.strip() if artist else None,
                    file_path=os.path.join(folder_path, file),
                    order=i + 1
                )
                added_count += 1
            except Exception as e:
                # Error adding track
                continue
        
        return JsonResponse({
            'success': True,
            'message': f'Scanned {added_count} tracks successfully',
            'tracks_count': added_count
        })
        
    except Playlist.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Playlist not found'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)
