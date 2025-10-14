# Phân biệt Khu vực Sân bóng và Khu vực Chuyên môn

## 🚫 KHÔNG phải giống nhau!

### 1. **Khu vực Sân bóng** (Stadium Dashboard)
**Dành cho:** Chủ sân bóng (vai trò STADIUM)

**Chức năng:**
- ✅ **Đăng tin TUYỂN DỤNG** (sân bóng cần tuyển chuyên gia)
- ✅ Quản lý tin tuyển dụng của sân
- ✅ Nhận và xử lý đơn ứng tuyển từ chuyên gia
- ✅ Xem thống kê tin đăng

**URL:** `/users/stadium/dashboard/`

**Ví dụ tin đăng:**
> "Sân bóng ABC cần tuyển bình luận viên cho giải U19"
> "Sân bóng XYZ cần tuyển nhiếp ảnh gia cho giải đấu"

---

### 2. **Khu vực Chuyên môn** (Professional Dashboard)  
**Dành cho:** Chuyên gia (COACH, COMMENTATOR, MEDIA, PHOTOGRAPHER, REFEREE)

**Chức năng:**
- ✅ **Đăng tin TÌM VIỆC** (chuyên gia tìm cơ hội làm việc)
- ✅ Quản lý tin tìm việc của mình
- ✅ Nhận và xử lý lời mời từ sân bóng/BTC
- ✅ Xem thống kê tin đăng

**URL:** `/users/professional/dashboard/`

**Ví dụ tin đăng:**
> "Bình luận viên 5 năm kinh nghiệm tìm giải đấu"
> "Nhiếp ảnh gia chuyên nghiệp tìm công việc"

---

## 🔄 Flow hoạt động

### Scenario 1: Chủ sân bóng tuyển dụng
```
1. Chủ sân vào "Khu vực Sân bóng"
2. Đăng tin "Cần tuyển bình luận viên"
3. Tin xuất hiện trên Thị trường Việc làm
4. Chuyên gia xem tin và ứng tuyển
5. Chủ sân nhận đơn ứng tuyển
6. Chấp nhận/Từ chối
```

### Scenario 2: Chuyên gia tìm việc
```
1. Chuyên gia vào "Khu vực Chuyên môn"
2. Đăng tin "Tìm kiếm cơ hội bình luận"
3. Tin xuất hiện trên Thị trường Việc làm
4. Sân bóng/BTC xem tin và gửi lời mời
5. Chuyên gia nhận lời mời
6. Chấp nhận/Từ chối
```

---

## 🎯 Sự khác biệt chính

| Tiêu chí | Khu vực Sân bóng | Khu vực Chuyên môn |
|----------|------------------|-------------------|
| **Đối tượng** | Chủ sân bóng (STADIUM) | Chuyên gia (COACH, COMMENTATOR, v.v.) |
| **Mục đích** | Tuyển dụng chuyên gia | Tìm kiếm việc làm |
| **Tin đăng** | "Cần tuyển..." | "Tìm kiếm..." |
| **Nhận gì** | Đơn ứng tuyển | Lời mời hợp tác |
| **URL** | `/users/stadium/dashboard/` | `/users/professional/dashboard/` |

---

## 🔍 Kiểm tra trong Dashboard

### Nếu bạn là Chủ sân bóng (STADIUM):
```
Dashboard → Sidebar → Thấy link "Hồ sơ Sân bóng"
↓
Click → Stadium Dashboard
↓
Có nút "Đăng tin tuyển dụng" (màu xanh lá)
```

### Nếu bạn là Chuyên gia (COACH, COMMENTATOR, v.v.):
```
Dashboard → Sidebar → Thấy link "Khu vực Chuyên môn"
↓
Click → Professional Dashboard  
↓
Có nút "Đăng tin tìm việc" (màu xanh lá)
```

### Nếu bạn có CẢ HAI vai trò:
```
Dashboard → Sidebar → Thấy CẢ HAI links:
- "Hồ sơ Sân bóng" (cho vai trò sân bóng)
- "Khu vực Chuyên môn" (cho vai trò chuyên gia)
```

---

## 📱 Templates khác nhau

### Stadium Dashboard Template:
- File: `stadium_dashboard.html`
- Tiêu đề: "Dashboard Sân bóng"
- Nút chính: "Đăng tin tuyển dụng"
- Thống kê: "Tin đã đăng", "Ứng viên mới"

### Professional Dashboard Template:
- File: `professional_dashboard.html`  
- Tiêu đề: "Dashboard Chuyên gia"
- Nút chính: "Đăng tin tìm việc"
- Thống kê: "Tin đã đăng", "Lời mời mới"

---

## ⚠️ Lưu ý quan trọng

### KHÔNG có sự trùng lặp:
- ❌ Không phải 2 khu vực giống nhau
- ❌ Không phải cùng 1 dashboard
- ❌ Không phải cùng 1 template
- ❌ Không phải cùng 1 URL

### CÓ sự phân biệt rõ ràng:
- ✅ 2 khu vực riêng biệt
- ✅ 2 mục đích khác nhau  
- ✅ 2 flow hoạt động khác nhau
- ✅ 2 templates khác nhau
- ✅ 2 URLs khác nhau

---

## 🧪 Test để kiểm tra

### Test 1: User có vai trò STADIUM
```
1. Login với user có role STADIUM
2. Vào Dashboard
3. Kiểm tra sidebar có link "Hồ sơ Sân bóng"
4. Click vào → Đến Stadium Dashboard
5. Thấy nút "Đăng tin tuyển dụng"
6. KHÔNG thấy link "Khu vực Chuyên môn"
```

### Test 2: User có vai trò COACH
```
1. Login với user có role COACH  
2. Vào Dashboard
3. Kiểm tra sidebar có link "Khu vực Chuyên môn"
4. Click vào → Đến Professional Dashboard
5. Thấy nút "Đăng tin tìm việc"
6. KHÔNG thấy link "Hồ sơ Sân bóng"
```

### Test 3: User có CẢ HAI vai trò
```
1. Login với user có cả STADIUM và COACH
2. Vào Dashboard  
3. Kiểm tra sidebar có CẢ HAI links
4. Click "Hồ sơ Sân bóng" → Stadium Dashboard
5. Click "Khu vực Chuyên môn" → Professional Dashboard
6. 2 dashboard khác nhau hoàn toàn
```

---

## ✅ Kết luận

**KHÔNG**, sân bóng và chuyên gia KHÔNG có cùng khu vực!

- 🏟️ **Sân bóng** → Khu vực riêng → Đăng tin tuyển dụng
- 👨‍💼 **Chuyên gia** → Khu vực riêng → Đăng tin tìm việc

Đây là 2 hệ thống riêng biệt, phục vụ 2 mục đích khác nhau trong hệ thống tuyển dụng!
