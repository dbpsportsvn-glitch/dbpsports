from django.contrib import admin
from django.utils.html import format_html
from django.forms import ModelForm, FileField, MultipleChoiceField
from django import forms
from django.shortcuts import render
from django.http import HttpResponseRedirect
from django.urls import path
from django.contrib import messages
import os
from .models import Playlist, Track, MusicPlayerSettings, UserPlaylist, UserTrack, UserPlaylistTrack
from .utils import get_audio_duration


class PlaylistForm(ModelForm):
    """Custom form cho Playlist với tính năng tự động tạo thư mục"""
    
    class Meta:
        model = Playlist
        fields = '__all__'
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Ẩn trường folder_path vì sẽ tự động tạo
        if 'folder_path' in self.fields:
            self.fields['folder_path'].widget = forms.HiddenInput()
            self.fields['folder_path'].required = False
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        
        # Tự động tạo thư mục nếu chưa có
        if not instance.folder_path:
            playlist_folder = os.path.join('media', 'music', 'playlist', instance.name.lower().replace(' ', '_'))
            os.makedirs(playlist_folder, exist_ok=True)
            instance.folder_path = os.path.abspath(playlist_folder)
        
        if commit:
            instance.save()
        return instance


class TrackForm(ModelForm):
    """Custom form cho Track với tính năng upload file"""
    music_file = FileField(
        required=False,
        help_text="Upload file nhạc (.mp3, .wav, .ogg, .m4a, .aac)",
        widget=forms.FileInput(attrs={'accept': '.mp3,.wav,.ogg,.m4a,.aac'})
    )
    
    class Meta:
        model = Track
        fields = '__all__'
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Ẩn trường file_path vì sẽ tự động tạo từ upload
        if 'file_path' in self.fields:
            self.fields['file_path'].widget = forms.HiddenInput()
            self.fields['file_path'].required = False
        
        # Không bắt buộc nhập title nếu có music_file
        if 'title' in self.fields:
            self.fields['title'].required = False
            self.fields['title'].help_text = "Tự động lấy từ tên file nếu không nhập"
    
    def clean(self):
        cleaned_data = super().clean()
        music_file = cleaned_data.get('music_file')
        
        if music_file:
            # Kiểm tra định dạng file
            allowed_extensions = ['.mp3', '.wav', '.ogg', '.m4a', '.aac']
            file_extension = os.path.splitext(music_file.name)[1].lower()
            
            if file_extension not in allowed_extensions:
                raise forms.ValidationError(f"Định dạng file không được hỗ trợ. Chỉ chấp nhận: {', '.join(allowed_extensions)}")
        
        return cleaned_data
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        music_file = self.cleaned_data.get('music_file')
        
        if music_file:
            # Lưu file vào thư mục playlist
            playlist = instance.playlist
            if playlist and playlist.folder_path:
                file_path = os.path.join(playlist.folder_path, music_file.name)
                
                # Kiểm tra xem track với file_path này đã tồn tại chưa
                existing_track = Track.objects.filter(playlist=playlist, file_path=file_path).first()
                if existing_track:
                    # Nếu đã tồn tại, cập nhật track hiện tại thay vì tạo mới
                    existing_track.title = instance.title or existing_track.title
                    existing_track.artist = instance.artist or existing_track.artist
                    existing_track.order = instance.order
                    existing_track.is_active = instance.is_active
                    
                    # Ghi đè file cũ
                    with open(file_path, 'wb') as destination:
                        for chunk in music_file.chunks():
                            destination.write(chunk)
                    
                    # Đọc duration từ file nhạc mới
                    existing_track.duration = get_audio_duration(file_path)
                    
                    # Tự động phân tách tên file thành title và artist
                    name_without_ext = os.path.splitext(music_file.name)[0]
                    if ' - ' in name_without_ext:
                        artist, title = name_without_ext.split(' - ', 1)
                        existing_track.artist = artist.strip()
                        existing_track.title = title.strip()
                    else:
                        existing_track.title = name_without_ext
                    
                    if commit:
                        existing_track.save()
                    return existing_track
                
                # Lưu file
                with open(file_path, 'wb') as destination:
                    for chunk in music_file.chunks():
                        destination.write(chunk)
                
                instance.file_path = file_path
                
                # Đọc duration từ file nhạc
                instance.duration = get_audio_duration(file_path)
                
                # Tự động phân tách tên file thành title và artist
                name_without_ext = os.path.splitext(music_file.name)[0]
                if ' - ' in name_without_ext:
                    artist, title = name_without_ext.split(' - ', 1)
                    instance.artist = artist.strip()
                    instance.title = title.strip()
                else:
                    instance.title = name_without_ext
        
        # Nếu không có title và không có music_file, lấy từ file_path hiện tại
        if not instance.title and instance.file_path and os.path.exists(instance.file_path):
            filename = os.path.basename(instance.file_path)
            name_without_ext = os.path.splitext(filename)[0]
            if ' - ' in name_without_ext:
                artist, title = name_without_ext.split(' - ', 1)
                instance.artist = artist.strip()
                instance.title = title.strip()
            else:
                instance.title = name_without_ext
        
        if commit:
            instance.save()
        return instance


class BulkTrackForm(forms.Form):
    """Form để upload nhiều track cùng lúc"""
    playlist = forms.ModelChoiceField(
        queryset=Playlist.objects.filter(is_active=True),
        empty_label="Chọn playlist...",
        help_text="Chọn playlist để thêm nhạc"
    )
    music_files = forms.FileField(
        widget=forms.FileInput(attrs={
            'accept': '.mp3,.wav,.ogg,.m4a,.aac',
            'class': 'form-control'
        }),
        help_text="Chọn nhiều file nhạc cùng lúc (.mp3, .wav, .ogg, .m4a, .aac)"
    )
    
    def clean_music_files(self):
        files = self.files.getlist('music_files')
        if not files:
            raise forms.ValidationError("Vui lòng chọn ít nhất một file nhạc.")
        
        # Kiểm tra định dạng file
        allowed_extensions = ['.mp3', '.wav', '.ogg', '.m4a', '.aac']
        for file in files:
            if not any(file.name.lower().endswith(ext) for ext in allowed_extensions):
                raise forms.ValidationError(f"File {file.name} không được hỗ trợ. Chỉ chấp nhận: {', '.join(allowed_extensions)}")
        
        return files


class EnhancedTrackForm(TrackForm):
    """Form nâng cao cho Track với tùy chọn upload hàng loạt"""
    upload_mode = forms.ChoiceField(
        choices=[
            ('single', 'Upload đơn lẻ'),
            ('bulk', 'Upload hàng loạt')
        ],
        initial='single',
        widget=forms.RadioSelect,
        help_text="Chọn chế độ upload"
    )
    bulk_files = forms.FileField(
        required=False,
        widget=forms.FileInput(attrs={
            'accept': '.mp3,.wav,.ogg,.m4a,.aac',
            'class': 'form-control'
        }),
        help_text="Chọn nhiều file nhạc cùng lúc (chỉ hiển thị khi chọn 'Upload hàng loạt')"
    )
    
    class Meta(TrackForm.Meta):
        fields = ['playlist', 'title', 'artist', 'music_file', 'duration', 'order', 'is_active']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Ẩn các trường không cần thiết cho bulk upload
        self.fields['title'].required = False
        self.fields['artist'].required = False
        self.fields['music_file'].required = False
        self.fields['bulk_files'].required = False
    
    def clean(self):
        cleaned_data = super().clean()
        upload_mode = cleaned_data.get('upload_mode')
        
        if upload_mode == 'single':
            if not cleaned_data.get('music_file'):
                raise forms.ValidationError("Vui lòng chọn file nhạc cho upload đơn lẻ.")
        elif upload_mode == 'bulk':
            bulk_files = self.files.getlist('bulk_files')
            if not bulk_files:
                raise forms.ValidationError("Vui lòng chọn ít nhất một file nhạc cho upload hàng loạt.")
            
            # Kiểm tra định dạng file
            allowed_extensions = ['.mp3', '.wav', '.ogg', '.m4a', '.aac']
            for file in bulk_files:
                if not any(file.name.lower().endswith(ext) for ext in allowed_extensions):
                    raise forms.ValidationError(f"File {file.name} không được hỗ trợ. Chỉ chấp nhận: {', '.join(allowed_extensions)}")
        
        return cleaned_data


@admin.register(Playlist)
class PlaylistAdmin(admin.ModelAdmin):
    form = PlaylistForm
    list_display = ['cover_thumbnail', 'name', 'folder_path', 'tracks_count', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'updated_at', 'cover_preview']
    actions = ['scan_playlist_folder', 'create_from_folder']
    
    fieldsets = (
        ('Thông tin cơ bản', {
            'fields': ('name', 'description', 'folder_path')
        }),
        ('Ảnh bìa Playlist', {
            'fields': ('cover_image', 'cover_preview')
        }),
        ('Cài đặt', {
            'fields': ('is_active',)
        }),
        ('Thông tin hệ thống', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def cover_thumbnail(self, obj):
        """Hiển thị thumbnail của playlist cover trong danh sách"""
        if obj.cover_image:
            return format_html(
                '<img src="{}" style="width: 50px; height: 50px; object-fit: cover; border-radius: 4px;" />',
                obj.cover_image.url
            )
        return format_html('<span style="color: #999;">Không có ảnh</span>')
    cover_thumbnail.short_description = 'Ảnh bìa'
    
    def cover_preview(self, obj):
        """Hiển thị preview lớn của playlist cover trong form"""
        if obj.cover_image:
            return format_html(
                '<img src="{}" style="max-width: 300px; max-height: 300px; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);" />',
                obj.cover_image.url
            )
        return 'Chưa có ảnh bìa playlist'
    cover_preview.short_description = 'Preview Ảnh Bìa'
    
    def tracks_count(self, obj):
        return obj.get_tracks_count()
    tracks_count.short_description = 'Số bài hát'
    
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        # Thêm help text cho folder_path
        if 'folder_path' in form.base_fields:
            form.base_fields['folder_path'].help_text = "Thư mục sẽ được tạo tự động dựa trên tên playlist"
        return form
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('create-from-folder/', self.admin_site.admin_view(self.create_from_folder_view), name='music_player_playlist_create_from_folder'),
        ]
        return custom_urls + urls
    
    def create_from_folder_view(self, request):
        """View để tạo playlist từ thư mục"""
        if request.method == 'POST':
            folder_path = request.POST.get('folder_path')
            playlist_name = request.POST.get('playlist_name')
            description = request.POST.get('description', '')
            
            if not folder_path or not playlist_name:
                messages.error(request, 'Vui lòng nhập đầy đủ thông tin.')
                return render(request, 'admin/music_player/playlist/create_from_folder.html', {
                    'title': 'Tạo Playlist từ Thư mục',
                    'opts': self.model._meta,
                })
            
            if not os.path.exists(folder_path):
                messages.error(request, 'Thư mục không tồn tại.')
                return render(request, 'admin/music_player/playlist/create_from_folder.html', {
                    'title': 'Tạo Playlist từ Thư mục',
                    'opts': self.model._meta,
                })
            
            try:
                # Tạo playlist
                playlist = Playlist.objects.create(
                    name=playlist_name,
                    description=description,
                    folder_path=folder_path,
                    is_active=True
                )
                
                # Scan và thêm tracks
                audio_extensions = ['.mp3', '.wav', '.ogg', '.m4a', '.aac']
                files = []
                
                for file in os.listdir(folder_path):
                    if any(file.lower().endswith(ext) for ext in audio_extensions):
                        files.append(file)
                
                files.sort()
                
                # Thêm tracks
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
                        
                        full_file_path = os.path.join(folder_path, file)
                        duration = get_audio_duration(full_file_path)
                        
                        Track.objects.create(
                            playlist=playlist,
                            title=title.strip(),
                            artist=artist.strip() if artist else None,
                            file_path=full_file_path,
                            duration=duration,
                            order=i + 1
                        )
                        added_count += 1
                    except Exception as e:
                        # Error adding track
                        continue
                
                messages.success(request, f'Đã tạo playlist "{playlist_name}" với {added_count} bài hát thành công!')
                return HttpResponseRedirect(f'../{playlist.id}/change/')
                
            except Exception as e:
                messages.error(request, f'Lỗi khi tạo playlist: {str(e)}')
        
        return render(request, 'admin/music_player/playlist/create_from_folder.html', {
            'title': 'Tạo Playlist từ Thư mục',
            'opts': self.model._meta,
        })
    
    def create_from_folder(self, request, queryset):
        """Admin action để tạo playlist từ thư mục"""
        return HttpResponseRedirect('../create-from-folder/')
    
    create_from_folder.short_description = "Tạo playlist từ thư mục"
    
    def scan_playlist_folder(self, request, queryset):
        """Admin action để scan thư mục playlist"""
        scanned_count = 0
        for playlist in queryset:
            try:
                folder_path = playlist.folder_path
                
                if not os.path.exists(folder_path):
                    self.message_user(request, f"Thư mục không tồn tại: {playlist.name}", level='ERROR')
                    continue
                
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
                        
                        full_file_path = os.path.join(folder_path, file)
                        duration = get_audio_duration(full_file_path)
                        
                        Track.objects.create(
                            playlist=playlist,
                            title=title.strip(),
                            artist=artist.strip() if artist else None,
                            file_path=full_file_path,
                            duration=duration,
                            order=i + 1
                        )
                        added_count += 1
                    except Exception as e:
                        # Error adding track
                        continue
                
                scanned_count += 1
                self.message_user(request, f"Đã scan thành công {added_count} bài hát từ playlist '{playlist.name}'")
                
            except Exception as e:
                self.message_user(request, f"Lỗi khi scan playlist '{playlist.name}': {str(e)}", level='ERROR')
        
        if scanned_count > 0:
            self.message_user(request, f"Đã scan thành công {scanned_count} playlist(s)")
    
    scan_playlist_folder.short_description = "Scan thư mục playlist"


@admin.register(Track)
class TrackAdmin(admin.ModelAdmin):
    form = EnhancedTrackForm
    list_display = ['album_cover_thumbnail', 'title', 'artist', 'playlist', 'duration_formatted', 'order', 'is_active']
    list_filter = ['playlist', 'is_active', 'created_at']
    search_fields = ['title', 'artist', 'album']
    readonly_fields = ['created_at', 'album_cover_preview']
    list_editable = ['order', 'is_active']
    
    fieldsets = (
        ('Chế độ Upload', {
            'fields': ('upload_mode',),
            'description': 'Chọn chế độ upload: đơn lẻ hoặc hàng loạt'
        }),
        ('Thông tin cơ bản', {
            'fields': ('playlist', 'title', 'artist', 'album', 'music_file', 'bulk_files')
        }),
        ('Ảnh bìa Album', {
            'fields': ('album_cover', 'album_cover_preview')
        }),
        ('Cài đặt', {
            'fields': ('duration', 'order', 'is_active')
        }),
        ('Thông tin hệ thống', {
            'fields': ('file_path', 'created_at'),
            'classes': ('collapse',)
        }),
    )
    
    def duration_formatted(self, obj):
        return obj.get_duration_formatted()
    duration_formatted.short_description = 'Thời lượng'
    
    def album_cover_thumbnail(self, obj):
        """Hiển thị thumbnail của album cover trong danh sách"""
        if obj.album_cover:
            return format_html(
                '<img src="{}" style="width: 50px; height: 50px; object-fit: cover; border-radius: 4px;" />',
                obj.album_cover.url
            )
        return format_html('<span style="color: #999;">Không có ảnh</span>')
    album_cover_thumbnail.short_description = 'Ảnh bìa'
    
    def album_cover_preview(self, obj):
        """Hiển thị preview lớn của album cover trong form"""
        if obj.album_cover:
            return format_html(
                '<img src="{}" style="max-width: 300px; max-height: 300px; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);" />',
                obj.album_cover.url
            )
        return 'Chưa có ảnh bìa album'
    album_cover_preview.short_description = 'Preview Ảnh Bìa'
    
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        # Thêm help text cho các trường
        if 'music_file' in form.base_fields:
            form.base_fields['music_file'].help_text = "Upload file nhạc (.mp3, .wav, .ogg, .m4a, .aac). Tên file nên có định dạng 'Nghệ sĩ - Tên bài hát'. Nếu file đã tồn tại, sẽ được cập nhật."
        if 'file_path' in form.base_fields:
            form.base_fields['file_path'].help_text = "Đường dẫn file sẽ được tạo tự động khi upload"
        return form
    
    def save_model(self, request, obj, form, change):
        """Xử lý save model với hỗ trợ upload hàng loạt"""
        upload_mode = form.cleaned_data.get('upload_mode', 'single')
        
        if upload_mode == 'bulk':
            # Xử lý upload hàng loạt
            bulk_files = request.FILES.getlist('bulk_files')
            playlist = form.cleaned_data['playlist']
            
            added_count = 0
            updated_count = 0
            
            for file in bulk_files:
                try:
                    # Tạo đường dẫn file
                    file_path = os.path.join(playlist.folder_path, file.name)
                    
                    # Kiểm tra xem track đã tồn tại chưa
                    existing_track = Track.objects.filter(
                        playlist=playlist,
                        file_path=file_path
                    ).first()
                    
                    # Lưu file
                    with open(file_path, 'wb') as destination:
                        for chunk in file.chunks():
                            destination.write(chunk)
                    
                    # Parse title và artist từ tên file
                    name_without_ext = os.path.splitext(file.name)[0]
                    if ' - ' in name_without_ext:
                        artist, title = name_without_ext.split(' - ', 1)
                        artist = artist.strip()
                        title = title.strip()
                    else:
                        artist = ''
                        title = name_without_ext
                    
                    # Đọc duration từ file nhạc
                    duration = get_audio_duration(file_path)
                    
                    if existing_track:
                        # Cập nhật track hiện có
                        existing_track.title = title
                        existing_track.artist = artist
                        existing_track.duration = duration
                        existing_track.save()
                        updated_count += 1
                    else:
                        # Tạo track mới
                        Track.objects.create(
                            playlist=playlist,
                            title=title,
                            artist=artist,
                            file_path=file_path,
                            duration=duration,
                            order=Track.objects.filter(playlist=playlist).count() + 1
                        )
                        added_count += 1
                        
                except Exception as e:
                    self.message_user(request, f"Lỗi khi upload file '{file.name}': {str(e)}", level='ERROR')
                    continue
            
            if added_count > 0 or updated_count > 0:
                message = f"Đã upload thành công {added_count} bài hát mới"
                if updated_count > 0:
                    message += f" và cập nhật {updated_count} bài hát"
                self.message_user(request, message, level='SUCCESS')
            else:
                self.message_user(request, "Không có file nào được upload thành công", level='WARNING')
            
            # Redirect về changelist sau khi upload hàng loạt
            return HttpResponseRedirect(request.path.replace('/add/', '/'))
        
        else:
            # Xử lý upload đơn lẻ (giữ nguyên logic cũ)
            try:
                super().save_model(request, obj, form, change)
            except Exception as e:
                if "UNIQUE constraint failed" in str(e):
                    messages.warning(request, f"File '{obj.file_path}' đã tồn tại trong playlist này. Track đã được cập nhật.")
                else:
                    raise e


@admin.register(MusicPlayerSettings)
class MusicPlayerSettingsAdmin(admin.ModelAdmin):
    list_display = ['user', 'default_playlist', 'auto_play', 'volume', 'repeat_mode', 'shuffle', 'storage_usage_display', 'storage_quota_mb']
    list_filter = ['auto_play', 'repeat_mode', 'shuffle']
    search_fields = ['user__username', 'user__email']
    readonly_fields = ['created_at', 'updated_at', 'storage_usage_display']
    list_editable = ['storage_quota_mb']
    
    fieldsets = (
        ('Người dùng', {
            'fields': ('user',)
        }),
        ('Cài đặt Player', {
            'fields': ('default_playlist', 'auto_play', 'volume', 'repeat_mode', 'shuffle')
        }),
        ('Quota Upload', {
            'fields': ('storage_quota_mb', 'storage_usage_display'),
            'description': 'Giới hạn dung lượng (MB) user có thể upload'
        }),
        ('Thông tin hệ thống', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def storage_usage_display(self, obj):
        usage = obj.get_upload_usage()
        percentage = (usage['used'] / usage['total'] * 100) if usage['total'] > 0 else 0
        color = '#28a745' if percentage < 70 else '#ffc107' if percentage < 90 else '#dc3545'
        # Format numbers first, then use format_html
        used_mb = f"{usage['used']:.1f}"
        total_mb = usage['total']
        percent_display = f"{percentage:.0f}"
        tracks = usage['tracks_count']
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}/{} MB ({}%)</span><br><small>{} bài hát</small>',
            color, used_mb, total_mb, percent_display, tracks
        )
    storage_usage_display.short_description = 'Dung lượng đã dùng'


class UserPlaylistTrackInline(admin.TabularInline):
    model = UserPlaylistTrack
    extra = 0
    fields = ['user_track', 'order']
    autocomplete_fields = ['user_track']


@admin.register(UserPlaylist)
class UserPlaylistAdmin(admin.ModelAdmin):
    list_display = ['cover_thumbnail', 'name', 'user', 'tracks_count_display', 'is_public', 'is_active', 'created_at']
    list_filter = ['is_public', 'is_active', 'created_at', 'user']
    search_fields = ['name', 'user__username', 'description']
    readonly_fields = ['created_at', 'updated_at', 'tracks_count_display', 'cover_preview']
    list_editable = ['is_public', 'is_active']
    inlines = [UserPlaylistTrackInline]
    
    fieldsets = (
        ('Thông tin cơ bản', {
            'fields': ('user', 'name', 'description')
        }),
        ('Ảnh bìa Playlist', {
            'fields': ('cover_image', 'cover_preview')
        }),
        ('Cài đặt', {
            'fields': ('is_public', 'is_active')
        }),
        ('Thống kê', {
            'fields': ('tracks_count_display',),
            'classes': ('collapse',)
        }),
        ('Thông tin hệ thống', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def cover_thumbnail(self, obj):
        """Hiển thị thumbnail của playlist cover trong danh sách"""
        if obj.cover_image:
            return format_html(
                '<img src="{}" style="width: 50px; height: 50px; object-fit: cover; border-radius: 4px;" />',
                obj.cover_image.url
            )
        return format_html('<span style="color: #999;">Không có ảnh</span>')
    cover_thumbnail.short_description = 'Ảnh bìa'
    
    def cover_preview(self, obj):
        """Hiển thị preview lớn của playlist cover trong form"""
        if obj.cover_image:
            return format_html(
                '<img src="{}" style="max-width: 300px; max-height: 300px; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);" />',
                obj.cover_image.url
            )
        return 'Chưa có ảnh bìa playlist'
    cover_preview.short_description = 'Preview Ảnh Bìa'
    
    def tracks_count_display(self, obj):
        count = obj.get_tracks_count()
        total_duration = obj.get_total_duration()
        minutes = total_duration // 60
        return format_html(
            '<span style="font-weight: bold;">{} bài</span> ({} phút)',
            count, minutes
        )
    tracks_count_display.short_description = 'Số bài hát'


@admin.register(UserTrack)
class UserTrackAdmin(admin.ModelAdmin):
    list_display = ['album_cover_thumbnail', 'title', 'artist', 'user', 'duration_formatted', 'file_size_display', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at', 'user']
    search_fields = ['title', 'artist', 'album', 'user__username']
    readonly_fields = ['created_at', 'updated_at', 'file_size', 'duration', 'file_preview', 'album_cover_preview']
    list_editable = ['is_active']
    
    fieldsets = (
        ('Thông tin cơ bản', {
            'fields': ('user', 'title', 'artist', 'album')
        }),
        ('Ảnh bìa Album', {
            'fields': ('album_cover', 'album_cover_preview')
        }),
        ('File nhạc', {
            'fields': ('file', 'file_preview', 'file_size', 'duration')
        }),
        ('Cài đặt', {
            'fields': ('is_active',)
        }),
        ('Thông tin hệ thống', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def duration_formatted(self, obj):
        return obj.get_duration_formatted()
    duration_formatted.short_description = 'Thời lượng'
    
    def file_size_display(self, obj):
        return obj.get_file_size_formatted()
    file_size_display.short_description = 'Kích thước'
    
    def album_cover_thumbnail(self, obj):
        """Hiển thị thumbnail của album cover trong danh sách"""
        if obj.album_cover:
            return format_html(
                '<img src="{}" style="width: 50px; height: 50px; object-fit: cover; border-radius: 4px;" />',
                obj.album_cover.url
            )
        return format_html('<span style="color: #999;">Không có ảnh</span>')
    album_cover_thumbnail.short_description = 'Ảnh bìa'
    
    def album_cover_preview(self, obj):
        """Hiển thị preview lớn của album cover trong form"""
        if obj.album_cover:
            return format_html(
                '<img src="{}" style="max-width: 300px; max-height: 300px; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);" />',
                obj.album_cover.url
            )
        return 'Chưa có ảnh bìa album'
    album_cover_preview.short_description = 'Preview Ảnh Bìa'
    
    def file_preview(self, obj):
        if obj.file:
            return format_html(
                '<audio controls preload="none" style="width: 300px;"><source src="{}" type="audio/mpeg">Trình duyệt không hỗ trợ.</audio>',
                obj.get_file_url()
            )
        return "Chưa có file"
    file_preview.short_description = 'Preview'
    
    actions = ['delete_selected_with_files']
    
    def delete_selected_with_files(self, request, queryset):
        """Xóa tracks và files của chúng"""
        count = queryset.count()
        for track in queryset:
            track.delete()  # Sẽ tự động xóa file nhờ override delete()
        self.message_user(request, f'Đã xóa {count} bài hát và files của chúng.')
    delete_selected_with_files.short_description = "Xóa tracks đã chọn (bao gồm cả files)"