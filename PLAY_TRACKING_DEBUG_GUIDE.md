# Hướng Dẫn Debug Thống Kê Lượt Nghe Music Player

## 📋 Tổng Quan

Đã thêm debug logging vào hệ thống tracking lượt nghe để chẩn đoán vấn đề. Tracking chỉ hoạt động khi:

1. ✅ User đã đăng nhập (`@login_required`)
2. ✅ Nghe đủ thời gian: tối thiểu 30 giây hoặc 50% thời lượng bài (nếu bài ngắn)
3. ✅ Không bị spam: cùng user + track trong 5 phút gần nhất sẽ không tính

## 🔍 Các Log Messages

Khi phát nhạc, bạn sẽ thấy các log messages sau trong Console (F12):

### 1. Bắt đầu tracking
```
🎵 [Tracking] Started play tracking
```

### 2. Khi đủ thời gian để record
```
🎵 [Tracking] Recording play: {
  track_id: X,
  track_type: 'global' hoặc 'user',
  listen_duration: 30,
  track_duration: 180
}
```

### 3. Gửi API request
```
🎵 [Tracking] Sending API request: {
  track_id: X,
  track_type: 'global',
  listen_duration: 30
}
```

### 4. Nhận API response
```
🎵 [Tracking] API response: {
  success: true,
  counted: true,
  play_count: 10,
  ...
}
```

### 5. Thành công
```
✅ [Tracking] Play count updated: 10
```

### 6. Không tính lượt nghe (spam protection)
```
⚠️ [Tracking] Play not counted: Đã ghi nhận (không tính trùng)
```

## 🧪 Cách Test

1. **Mở trình duyệt và login**
   - Đảm bảo bạn đã đăng nhập vào hệ thống

2. **Mở Developer Console**
   - Nhấn F12 hoặc Right-click → Inspect
   - Chuyển sang tab "Console"

3. **Phát một bài hát**
   - Click vào bất kỳ bài hát nào trong playlist
   - Để phát ít nhất 30 giây

4. **Quan sát logs**
   - Xem các log messages ở trên
   - Kiểm tra xem có lỗi nào không

## ❌ Các Lỗi Có Thể Gặp

### 1. User chưa đăng nhập
**Triệu chứng:** API trả về 403 hoặc redirect đến trang login

**Giải pháp:** Đăng nhập vào hệ thống

### 2. CSRF Token missing
**Triệu chứng:** Console error về CSRF

**Giải pháp:** Reload trang để lấy CSRF token mới

### 3. Track không tồn tại
**Triệu chứng:** 
```
❌ [Tracking] Error recording play: Track không tồn tại
```

**Giải pháp:** Kiểm tra database xem track có tồn tại không

### 4. Không đủ thời gian
**Triệu chứng:**
```
🎵 [Tracking] Skipped - not enough duration: {
  listened: 15,
  minDuration: 30
}
```

**Giải pháp:** Nghe đủ 30 giây hoặc 50% thời lượng bài

### 5. Bị spam protection
**Triệu chứng:**
```
⚠️ [Tracking] Play not counted: Đã ghi nhận (không tính trùng)
```

**Giải pháp:** Đây là hành vi bình thường, đợi 5 phút trước khi phát lại cùng một bài

## 🔧 Những Gì Đã Thay Đổi

### music_player.js (v1.2.29)
- ✅ Thêm console.log cho `startPlayTracking()`
- ✅ Thêm console.log cho `recordCurrentTrackPlay()`
- ✅ Log chi tiết API request và response
- ✅ Log khi skip tracking và lý do

### Cache Busting
- ✅ Cập nhật version từ v1.2.36 → v1.2.37 trong `base.html`

## 📊 Database Queries

Để kiểm tra tracking có hoạt động không:

```python
from music_player.models import TrackPlayHistory, Track, UserTrack

# Xem lịch sử nghe
history = TrackPlayHistory.objects.all().order_by('-played_at')[:10]
for h in history:
    print(f"{h.user.username} - {h.track_title} - {h.played_at}")

# Xem play_count của tracks
tracks = Track.objects.filter(is_active=True)[:10]
for t in tracks:
    print(f"{t.title} - {t.play_count} lượt nghe")
```

## ✅ Kết Quả Mong Đợi

Sau khi test, bạn sẽ thấy:

1. Console logs hiển thị đầy đủ quá trình tracking
2. Số lượt nghe được cập nhật trong UI (icon tai nghe)
3. Số lượt nghe được tăng lên trong database
4. Không có lỗi nào trong console

## 🆘 Nếu Vẫn Không Hoạt Động

Nếu sau khi test mà vẫn không thấy tracking hoạt động:

1. **Copy toàn bộ console logs** và gửi cho developer
2. **Kiểm tra Network tab** xem API call có được gửi không
3. **Kiểm tra Response** từ API có lỗi gì không
4. **Kiểm tra database** xem có record nào trong `TrackPlayHistory` không

## ✅ ĐÃ FIX - Version 1.2.30

**Vấn đề:** Tracking flags không được reset khi chuyển track mới, khiến các track tiếp theo bị skip.

**Giải pháp:**
- ✅ Reset `hasRecordedPlay` và `currentTrackListenDuration` trong `stopPlayTracking()`
- ✅ Gọi `stopPlayTracking()` khi chuyển sang track mới trong `playTrack()`
- ✅ Đảm bảo mỗi track được track riêng biệt

**Kết quả:** Mỗi track giờ sẽ được tracking độc lập, không còn bị skip!

---

## ⚠️ LƯU Ý: Spam Protection

**Tính năng:** Cùng user + track trong vòng **5 phút** gần nhất sẽ **không được tính** lượt nghe mới.

**Log example:**
```
🎵 [Tracking] API response: {success: true, message: 'Đã ghi nhận (không tính trùng)', counted: false}
⚠️ [Tracking] Play not counted: Đã ghi nhận (không tính trùng)
```

**Cách test:**
1. ✅ Nghe **track khác** (track chưa được nghe trong 5 phút gần nhất)
2. ✅ Đợi **5 phút** sau khi nghe track đó, sau đó nghe lại
3. ✅ Kiểm tra **play_count** trong database

**Đây KHÔNG phải lỗi** - đây là tính năng bảo vệ chống spam lượt nghe!

---

**Version:** 1.2.30
**Date:** 2025-01-29
**Status:** Fixed - Tracking Now Works Correctly ✅
