# 🐛 Debug Guide - Global Discovery

## Checklist để kiểm tra:

### ✅ 1. Playlist có đúng trạng thái public không?

Vào Django Admin:
```
http://localhost:8000/admin/music_player/userplaylist/
```

Tìm playlist của bạn và kiểm tra:
- ☑️ **"Công khai" (is_public)** = ✅ Checked
- ☑️ **"Kích hoạt" (is_active)** = ✅ Checked

### ✅ 2. Test API trực tiếp

Mở trình duyệt và vào:
```
http://localhost:8000/music/global/playlists/
```

**Kết quả mong đợi:**
```json
{
  "success": true,
  "playlists": [
    {
      "id": 1,
      "name": "Tên playlist của bạn",
      "tracks_count": X,
      "owner": {
        "full_name": "Tên bạn"
      }
    }
  ],
  "count": 1
}
```

**Nếu count = 0**, có nghĩa là:
- Playlist chưa được set `is_public=True` trong database
- Hoặc `is_active=False`

### ✅ 3. Kiểm tra Browser Console

1. Mở Music Player
2. Nhấn F12 → Tab Console
3. Click "Global Discovery"
4. Xem logs:

```
🔍 Loading global playlists... all
✅ Created playlists container
📊 API Response: { success: true, playlists: [...], count: X }
✅ Found X public playlists
  - "Playlist Name" by User Name (Y tracks)
```

### ✅ 4. Clear Browser Cache

Có thể JS cũ đang được cache:
- **Chrome/Edge**: Ctrl + Shift + Delete → Clear cache
- **Hoặc**: Ctrl + F5 để hard reload

### ✅ 5. Kiểm tra Network Tab

1. F12 → Tab **Network**
2. Click "Global Discovery"
3. Tìm request đến `/music/global/playlists/`
4. Click vào request → Tab **Response**
5. Xem response có data không?

## 🔧 Quick Fix Commands

### Kiểm tra playlist trong Django Shell:

```bash
cd backend
python manage.py shell
```

Trong shell:
```python
from music_player.models import UserPlaylist

# Xem tất cả user playlists
playlists = UserPlaylist.objects.all()
for p in playlists:
    print(f"{p.id}: {p.name} - Public:{p.is_public}, Active:{p.is_active}, Tracks:{p.get_tracks_count()}")

# Set một playlist thành public
playlist = UserPlaylist.objects.get(id=1)  # Thay 1 bằng ID của bạn
playlist.is_public = True
playlist.is_active = True
playlist.save()
print(f"✅ Set playlist '{playlist.name}' to public!")

# Kiểm tra lại
public_playlists = UserPlaylist.objects.filter(is_public=True, is_active=True)
print(f"\n📊 Total public playlists: {public_playlists.count()}")
for p in public_playlists:
    print(f"  - {p.name} by {p.user.username}")
```

### Force reload JavaScript trong browser:

1. Mở Developer Tools (F12)
2. Right-click vào nút Refresh
3. Chọn **"Empty Cache and Hard Reload"**

## 🎯 Các vấn đề thường gặp:

### Vấn đề 1: Playlist không có bài hát
- **Hiện tượng**: API trả về playlist nhưng UI không hiển thị
- **Nguyên nhân**: Code có thể skip playlist không có tracks
- **Giải pháp**: Vẫn sẽ hiển thị với "0 bài • 0 phút"

### Vấn đề 2: JavaScript không load
- **Hiện tượng**: Không thấy logs trong console
- **Nguyên nhân**: Browser cache hoặc JS file cũ
- **Giải pháp**: Hard reload (Ctrl + Shift + R)

### Vấn đề 3: Tab không switch
- **Hiện tượng**: Click "Global Discovery" không có gì xảy ra
- **Nguyên nhân**: Event listener chưa được bind
- **Giải pháp**: Check console có lỗi JS không

### Vấn đề 4: is_public=True nhưng API không trả về
- **Nguyên nhân**: is_active=False hoặc có exception trong loop
- **Giải pháp**: Check Django logs hoặc test API trực tiếp

## 📞 Nếu vẫn không work:

Hãy gửi cho mình:
1. Screenshot của Browser Console
2. Response từ `/music/global/playlists/`
3. Output của Django Shell command ở trên

