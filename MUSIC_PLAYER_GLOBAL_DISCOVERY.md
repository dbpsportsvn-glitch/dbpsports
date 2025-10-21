# Tính năng Global Discovery - Music Player

## 📋 Tổng quan

Đã hoàn thành tính năng **Global Discovery** cho Music Player, cho phép:
- ✅ Chia sẻ playlist cá nhân lên mục công khai (Global)
- ✅ Tìm kiếm playlist của người dùng khác
- ✅ Nghe nhạc từ playlist công khai của người khác
- ✅ Toggle public/private cho từng playlist

## 🎯 Các tính năng mới

### 1. **Toggle Public/Private cho User Playlist**

#### Backend API:
- **Endpoint**: `POST /music/user/playlists/<playlist_id>/toggle-public/`
- **Chức năng**: Chuyển đổi trạng thái công khai/riêng tư của playlist
- **Response**: 
  ```json
  {
    "success": true,
    "message": "Đã chuyển playlist sang chế độ công khai/riêng tư",
    "is_public": true/false
  }
  ```

#### Frontend UI:
- Nút toggle ở Settings Modal → tab "Playlist của tôi"
- Icon: 🔒 (Lock) khi private, 🌐 (Globe) khi public
- Badge màu xanh hiển thị trạng thái public bên cạnh tên playlist
- Màu nút: Xám khi private, xanh lá khi public

---

### 2. **Global Discovery Tab**

#### Backend API:
- **Admin Playlists**: `GET /music/api/` - Lấy tất cả playlists của admin
- **User Public Playlists**: `GET /music/global/playlists/` - Lấy tất cả public playlists của users
- **Query params**: `?search=<query>` (optional) - Tìm kiếm theo tên playlist hoặc người dùng

#### Frontend UI:
- Tab mới "Global Discovery" với icon 🔍 trong Playlists tab
- **Search bar toàn chiều rộng** ở đầu (không có icon search bên trái)
- **Gộp chung admin playlists và user playlists** vào 1 danh sách
- Layout grid đồng bộ với 2 tab khác (Personal & Admin Playlists)
- Scroll height: 415px (tương tự các tab khác)
- Mỗi playlist card hiển thị:
  - Cover image hoặc icon mặc định
  - Tên playlist
  - Số bài hát và thời lượng
  - Owner badge (chỉ cho user playlists, hiển thị khi hover)

---

### 3. **Play Public Playlist**

#### Backend API:
- **Endpoint**: `GET /music/global/playlists/<playlist_id>/`
- **Chức năng**: Lấy chi tiết và tracks của public playlist
- **Không cần đăng nhập** (public endpoint)
- **Response**:
  ```json
  {
    "success": true,
    "playlist": {
      "id": 1,
      "name": "Nhạc Chill",
      "description": "...",
      "cover_image": "/media/...",
      "tracks_count": 15,
      "total_duration": 3600,
      "owner": {...}
    },
    "tracks": [
      {
        "id": 1,
        "title": "Bài hát 1",
        "artist": "Ca sĩ A",
        "album": "Album A",
        "album_cover": "/media/...",
        "duration": 240,
        "duration_formatted": "04:00",
        "file_url": "/media/...",
        "play_count": 100
      }
    ]
  }
  ```

#### Frontend UI:
- Click vào playlist card trong Global Discovery sẽ:
  - Load tracks từ API
  - Chuyển sang tab "Danh sách bài hát"
  - Tự động phát bài đầu tiên
  - Hiển thị tên playlist với owner: "Playlist Name (by User Name)"

---

## 🧪 Hướng dẫn Test

### **Test 1: Toggle Public/Private**

1. Đăng nhập vào hệ thống
2. Mở Music Player → Click avatar/settings button
3. Vào tab "Playlist của tôi"
4. Tạo một playlist mới (nếu chưa có)
5. Click nút 🔒 (Lock) bên cạnh playlist
6. ✅ **Expected**: 
   - Icon chuyển thành 🌐 (Globe)
   - Nút đổi màu sang xanh lá
   - Badge 🌐 xuất hiện bên cạnh tên playlist
   - Notification: "Đã chuyển playlist sang chế độ công khai"

7. Click nút 🌐 lần nữa
8. ✅ **Expected**:
   - Icon chuyển về 🔒
   - Nút đổi về màu xám
   - Badge 🌐 biến mất
   - Notification: "Đã chuyển playlist sang chế độ riêng tư"

---

### **Test 2: Global Discovery - Xem danh sách**

1. Đảm bảo có ít nhất 1 playlist được set public (từ Test 1)
2. Mở Music Player → Tab "Playlist"
3. Click button "Global Discovery" (🔍 icon)
4. ✅ **Expected**:
   - Search bar toàn chiều rộng xuất hiện ở đầu (không có icon search bên trái)
   - **Tất cả playlists hiển thị chung** (admin + user) trong 1 grid
   - Layout đồng bộ với 2 tab khác
   - Mỗi card hiển thị:
     - Cover image (nếu có)
     - Tên playlist
     - "X bài • Y phút"
     - Owner badge khi hover (chỉ cho user playlists)

---

### **Test 3: Global Discovery - Search**

1. Ở tab Global Discovery
2. Gõ tên playlist hoặc tên người dùng vào search bar
3. ✅ **Expected**:
   - Kết quả tự động cập nhật sau 500ms
   - **Tìm kiếm trong cả admin và user playlists**:
     - Admin playlists: filter theo tên playlist
     - User playlists: filter theo tên playlist hoặc tên người dùng
   - Hiển thị kết quả merge trong 1 grid
   - Nếu không tìm thấy: hiển thị "Không tìm thấy playlist nào cho..."
4. Xóa search query
5. ✅ **Expected**: Hiển thị lại tất cả playlists (admin + user)

---

### **Test 4: Play Global Playlist**

1. Ở tab Global Discovery
2. Click vào một playlist card
3. ✅ **Expected**:
   - Player tự động chuyển sang tab "Danh sách bài hát"
   - Hiển thị tracks của playlist đó
   - Bài đầu tiên tự động phát
   - Playlist name hiển thị: "Tên Playlist (by Tên Owner)"
   - Notification: "🎵 Đang phát: Tên Playlist"

4. Tracks play bình thường (next, prev, repeat, shuffle)
5. ✅ **Expected**: Tất cả chức năng player hoạt động như bình thường

---

### **Test 5: Public Playlist từ người khác**

1. **User A**: 
   - Tạo playlist "Test Playlist"
   - Thêm vài bài hát vào
   - Set public

2. **User B** (hoặc chưa đăng nhập):
   - Mở Music Player → Global Discovery
   - Tìm "Test Playlist" của User A
   - Click play

3. ✅ **Expected**:
   - User B có thể nghe nhạc từ playlist của User A
   - Không cần đăng nhập vẫn có thể xem và nghe
   - Play count tăng lên khi nghe đủ 30s/50%

---

### **Test 6: Refresh sau khi toggle**

1. User A set playlist public
2. Ngay lập tức check tab Global Discovery
3. ✅ **Expected**: Playlist xuất hiện trong danh sách global

4. User A set playlist về private
5. Refresh tab Global Discovery
6. ✅ **Expected**: Playlist biến mất khỏi danh sách global

---

## 🎨 UI/UX Features

### **Search Bar**
- Background: Semi-transparent white với blur
- **Không có icon bên trái** (đã bỏ để thanh search dài hơn)
- Placeholder: "🔍 Tìm tên playlist hoặc tên người dùng..."
- Focus: Border và shadow màu tím (#f093fb)
- Debounce: 500ms
- Clear button (X) bên phải khi có text

### **Playlists Grid**
- Layout: Grid responsive (165px min-width, 145px mobile)
- Gap: 14px (12px mobile)
- Max height: 415px với scroll
- Padding: 8px 16px 16px 16px
- **Đồng bộ với Personal & Admin tabs**

### **Playlist Card**
- Height: 200px (185px mobile)
- Cover/Icon: 135px height (125px mobile)
- Border radius: 16px
- Hover effects: scale + shadow
- Owner Badge (chỉ user playlists):
  - Position: Bottom overlay trên cover
  - Show on hover
  - Icon: 👤 (person-circle)
  - Background: Dark gradient với blur
  - Color: Gold (#ffd700) icon + white text

### **Public Badge (User Playlists)**
- Color: Green (#22c55e)
- Icon: 🌐
- Position: Bên cạnh tên playlist
- Size: 12px

### **Toggle Button**
- Private state:
  - Icon: 🔒
  - Color: Gray (rgba(255,255,255,0.15))
- Public state:
  - Icon: 🌐
  - Color: Green (#22c55e)
- Hover: Scale 1.1x
- Transition: Smooth 0.2s

---

## 📊 Database

Không cần migration mới! Sử dụng field có sẵn:
- `UserPlaylist.is_public` (Boolean, default=False)

---

## 🔒 Security & Permissions

1. **Toggle Public/Private**: Chỉ owner của playlist mới được toggle
2. **View Public Playlists**: Ai cũng có thể xem (không cần đăng nhập)
3. **Play Public Playlists**: Ai cũng có thể nghe
4. **Edit/Delete**: Vẫn chỉ có owner mới được thực hiện

---

## 🚀 Performance

- **Caching**: Không cache (luôn lấy data mới nhất)
- **Search debounce**: 500ms để giảm API calls
- **Limit**: Top 100 public playlists (có thể tăng nếu cần)
- **Query optimization**: `select_related('user')` để giảm N+1 queries

---

## 📱 Mobile Responsive

- Search bar: Font-size giảm xuống 13px
- Playlist grid: Tự động điều chỉnh số cột
- Touch-friendly: Tất cả buttons có size tối thiểu 34px

---

## ✨ Workflow tổng quan

```
User A:
1. Tạo playlist "Nhạc Chill"
2. Upload/thêm tracks vào
3. Click nút 🔒 → 🌐 để set public
4. Playlist xuất hiện trong Global Discovery

User B (hoặc anonymous):
1. Mở Music Player
2. Tab Playlist → Click "Global Discovery"
3. Search "Nhạc Chill" hoặc "User A"
4. Click vào playlist card
5. Nghe nhạc ngay lập tức!
```

---

## 🐛 Known Issues / Future Enhancements

- [ ] Thêm sorting options (mới nhất, phổ biến nhất, etc.)
- [ ] Thêm filter by genre/mood
- [ ] Like/favorite public playlists
- [ ] Comment on playlists
- [ ] Share playlist link

---

## 🎉 Hoàn thành!

Tất cả tính năng đã được implement đầy đủ và sẵn sàng để test!

