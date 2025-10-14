# Phân biệt các Khu vực trong hệ thống

## 📍 Tổng quan các khu vực

### 1. **Khu vực Chuyên môn** (Professional Dashboard)
**URL:** `/users/professional/dashboard/`

**Dành cho:** Huấn luyện viên, Bình luận viên, Media, Nhiếp ảnh gia, Trọng tài

**Chức năng:**
- ✅ Đăng tin TÌM VIỆC (chuyên gia tìm công việc)
- ✅ Quản lý tin tìm việc của mình (xem, sửa, xóa)
- ✅ Nhận và xử lý lời mời từ BTC/Sân bóng
- ✅ Xem thống kê tin đăng

**Cách truy cập:**
- Dashboard → Sidebar bên trái → Click "Khu vực Chuyên môn" (icon briefcase)
- Hoặc Dashboard → Tab "Hồ sơ công khai" → Nút xanh "Khu vực Chuyên môn (Đăng tin & Quản lý)"

---

### 2. **Khu vực Sân bóng** (Stadium Dashboard)
**URL:** `/users/stadium/dashboard/`

**Dành cho:** Chủ sân bóng

**Chức năng:**
- ✅ Đăng tin TUYỂN DỤNG (sân bóng cần tuyển chuyên gia)
- ✅ Quản lý tin tuyển dụng của sân
- ✅ Nhận và xử lý đơn ứng tuyển
- ✅ Xem thống kê tin đăng

**Cách truy cập:**
- Dashboard → Sidebar → Click "Hồ sơ Sân bóng"

---

### 3. **Chỉnh sửa Thông tin Chuyên môn** (Unified Form)
**URL:** `/users/professional/edit/`

**Dành cho:** Tất cả vai trò chuyên gia

**Chức năng:**
- ✅ Cập nhật thông tin cá nhân (bio, location, experience)
- ✅ Cập nhật thông tin chuyên môn theo vai trò
- ✅ KHÔNG phải nơi đăng tin tuyển dụng

**Cách truy cập:**
- Dashboard → Tab "Hồ sơ công khai" → Nút "Chỉnh sửa Hồ sơ Chuyên môn"

---

### 4. **Thị trường Việc làm** (Job Market)
**URL:** `/tournaments/job-market/`

**Dành cho:** Tất cả mọi người

**Chức năng:**
- ✅ Xem TẤT CẢ tin tuyển dụng/tìm việc
- ✅ Filter theo vai trò, khu vực
- ✅ Ứng tuyển/Gửi lời mời

**Cách truy cập:**
- Menu chính → "Việc làm" (hoặc tương tự)

---

## 🔄 So sánh: Đăng tin TÌM VIỆC vs TUYỂN DỤNG

### Đăng tin TÌM VIỆC (Professional Dashboard)
- **Ai đăng?** Chuyên gia (COACH, COMMENTATOR, MEDIA, PHOTOGRAPHER, REFEREE)
- **Mục đích?** Tìm kiếm cơ hội làm việc
- **Nội dung?** "Tôi có kỹ năng X, tìm công việc Y"
- **Ví dụ:** "Bình luận viên 5 năm kinh nghiệm tìm giải đấu"

### Đăng tin TUYỂN DỤNG (Stadium Dashboard / Tournament)
- **Ai đăng?** Sân bóng, BTC giải đấu
- **Mục đích?** Tuyển dụng chuyên gia
- **Nội dung?** "Chúng tôi cần tuyển người có kỹ năng X"
- **Ví dụ:** "Sân ABC cần tuyển bình luận viên cho giải U19"

---

## 📋 Flow hoạt động

### Scenario 1: Chuyên gia tìm việc
```
1. Chuyên gia vào "Khu vực Chuyên môn"
2. Click "Đăng tin tìm việc"
3. Điền thông tin về kỹ năng, kinh nghiệm
4. Đăng tin
5. Tin xuất hiện trên "Thị trường Việc làm"
6. BTC/Sân bóng xem tin và gửi lời mời
7. Chuyên gia nhận lời mời trong "Lời mời nhận được"
8. Chấp nhận/Từ chối
```

### Scenario 2: Sân bóng tuyển dụng
```
1. Chủ sân vào "Khu vực Sân bóng" 
2. Click "Đăng tin tuyển dụng"
3. Điền thông tin công việc cần tuyển
4. Đăng tin
5. Tin xuất hiện trên "Thị trường Việc làm"
6. Chuyên gia xem tin và ứng tuyển
7. Chủ sân nhận đơn trong "Đơn Ứng Tuyển"
8. Chấp nhận/Từ chối
```

---

## 🎯 Checklist kiểm tra

Nếu bạn thấy link bị sai, hãy kiểm tra:

### Bạn là Chuyên gia (COACH, COMMENTATOR, v.v.)
- [ ] Vào Dashboard → Sidebar → Thấy link "Khu vực Chuyên môn" ✅
- [ ] Click vào → Đến `/users/professional/dashboard/` ✅
- [ ] Trong đó có nút "Đăng tin tìm việc" ✅
- [ ] Click "Đăng tin tìm việc" → Đến form đăng tin TÌM VIỆC ✅
- [ ] KHÔNG dẫn đến Stadium Dashboard ❌

### Bạn là Chủ sân bóng
- [ ] Vào Dashboard → Sidebar → Thấy link "Hồ sơ Sân bóng" ✅
- [ ] Click vào → Đến `/users/stadium/dashboard/` ✅
- [ ] Trong đó có nút "Đăng tin tuyển dụng" ✅
- [ ] Click "Đăng tin tuyển dụng" → Đến form đăng tin TUYỂN DỤNG ✅

---

## ⚠️ Các lỗi thường gặp

### Lỗi 1: "Khu vực Chuyên môn" dẫn đến Stadium Dashboard
**Nguyên nhân:** Bạn có cả 2 vai trò và click nhầm link

**Giải pháp:** 
- Link "Khu vực Chuyên môn" → Professional Dashboard (cho chuyên gia)
- Link "Hồ sơ Sân bóng" → Stadium Dashboard (cho sân bóng)

### Lỗi 2: "Đăng tin" dẫn đến Thị trường Việc làm
**Nguyên nhân:** Có thể click vào link khác

**Giải pháp:**
- Trong Professional Dashboard, nút "Đăng tin tìm việc" → Form đăng tin
- Trong Stadium Dashboard, nút "Đăng tin tuyển dụng" → Form tuyển dụng
- Không có link trực tiếp đến Thị trường

---

## 🔧 Nếu vẫn gặp vấn đề

Hãy cho mình biết:
1. Bạn đang ở vai trò nào? (COACH, STADIUM, v.v.)
2. Bạn click vào link nào?
3. Nó dẫn bạn đến URL nào?
4. Bạn mong muốn đến đâu?

Ví dụ: "Tôi là COACH, click 'Đăng tin tìm việc', nó dẫn đến `/users/stadium/job/create/` thay vì `/users/professional/job/create/`"

