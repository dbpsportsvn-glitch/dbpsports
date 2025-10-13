# 🎯 Cập Nhật Hệ Thống: Vai Trò Huấn Luyện Viên & Sân Bóng

## ✨ Tính Năng Mới

### 1️⃣ Huấn Luyện Viên (COACH)
- 📋 Hồ sơ đầy đủ: kinh nghiệm, chứng chỉ, thành tích
- 🔑 **Quyền như đội trưởng**: quản lý đội, cầu thủ, đăng ký giải
- 🤝 Tính năng chiêu mộ từ đội bóng
- 📍 Tìm kiếm theo khu vực và kinh nghiệm

### 2️⃣ Sân Bóng (STADIUM)
- 🏟️ Hồ sơ chi tiết: địa chỉ, loại sân, tiện ích
- 💼 Đăng tin tuyển dụng (BLV, Trọng tài, Media...)
- 🤝 Có thể được BTC thêm vào nhà tài trợ/nhân sự
- 💰 Thông tin thanh toán & QR code

---

## 📦 Files Đã Thay Đổi

### Models
- ✅ `backend/users/models.py` - CoachProfile, StadiumProfile
- ✅ `backend/tournaments/models.py` - CoachRecruitment, Team.coach
- ✅ `backend/organizations/models.py` - JobPosting cập nhật

### Forms
- ✅ `backend/tournaments/forms.py` - TeamCreationForm, CoachProfileForm, CoachRecruitmentForm

### Admin
- ✅ `backend/users/admin.py` - CoachProfileAdmin, StadiumProfileAdmin
- ✅ `backend/tournaments/admin.py` - CoachRecruitmentAdmin
- ✅ `backend/organizations/admin.py` - JobPostingAdmin cập nhật

### Utils
- ✅ `backend/tournaments/utils.py` - user_can_manage_team()

### Migrations
- ✅ 5 migration files đã được tạo

---

## 🚀 Hướng Dẫn Sử Dụng Ngay

### Bước 1: Chạy Migrations
```bash
cd backend
venv\Scripts\python.exe manage.py migrate
```

### Bước 2: Tạo Vai Trò (Tự động)
Migration đã tự động tạo 2 vai trò mới:
- **COACH** - Huấn luyện viên
- **STADIUM** - Sân bóng

### Bước 3: Sử Dụng Admin Panel

#### A. Tạo Hồ Sơ Huấn Luyện Viên
1. Vào `/admin/users/coachprofile/add/`
2. Chọn user
3. Điền thông tin:
   - Họ tên, ảnh, giới thiệu
   - Kinh nghiệm, chứng chỉ
   - Khu vực hoạt động
   - ☑️ Đánh dấu "Đang tìm đội" nếu cần

#### B. Tạo Đội Với Huấn Luyện Viên
1. Vào form tạo đội
2. Chọn HLV từ dropdown (những HLV đang tìm đội)
3. Hoặc nhập tên HLV (dữ liệu cũ)

#### C. Sân Bóng Đăng Tin
1. Tạo StadiumProfile trước
2. Vào `/admin/organizations/jobposting/add/`
3. Chọn:
   - **Đăng bởi**: Sân bóng
   - **Sân bóng**: Chọn sân của bạn
   - Vai trò cần tuyển, mô tả...

---

## 🔐 Phân Quyền Mới

### Đội Trưởng & Huấn Luyện Viên
Cả hai đều có **TOÀN BỘ** quyền:
- ✅ Thêm/Xóa/Sửa cầu thủ
- ✅ Đăng ký giải đấu
- ✅ Quản lý đội hình
- ✅ Chiêu mộ cầu thủ
- ✅ Chuyển nhượng
- ✅ Gửi ghi chú cho BLV

### Kiểm tra quyền trong code:
```python
from tournaments.utils import user_can_manage_team

if user_can_manage_team(request.user, team):
    # Cho phép thao tác
```

---

## 📚 Tài Liệu Chi Tiết

### 1. `HUONG_DAN_VAI_TRO_MOI.md`
- Hướng dẫn đầy đủ về models, forms, admin
- Chi tiết về tính năng
- Testing checklist

### 2. `TOM_TAT_THAY_DOI.md`
- Tóm tắt các thay đổi
- TODO views & templates cần implement
- Code examples cho views

---

## ⚙️ Tính Năng Backend Đã Hoàn Thành

### ✅ Models & Database
- [x] CoachProfile model với đầy đủ fields
- [x] StadiumProfile model với đầy đủ fields
- [x] CoachRecruitment model
- [x] Team.coach ForeignKey
- [x] JobPosting cập nhật cho sân bóng
- [x] Migrations hoàn chỉnh

### ✅ Forms
- [x] TeamCreationForm với dropdown HLV
- [x] CoachProfileForm
- [x] CoachRecruitmentForm
- [x] Validation đầy đủ

### ✅ Admin Interface
- [x] Admin panel cho CoachProfile
- [x] Admin panel cho StadiumProfile
- [x] Admin panel cho CoachRecruitment
- [x] JobPosting admin cập nhật
- [x] Fieldsets & filters

### ✅ Permissions
- [x] user_can_manage_team() helper
- [x] Logic kiểm tra captain hoặc coach

---

## 🎨 Frontend Cần Implement (TODO)

### Views Cần Tạo
1. **Chiêu mộ HLV**
   - `recruit_coach` - Danh sách HLV
   - `send_coach_offer` - Gửi lời mời
   - `respond_to_recruitment` - Accept/Reject

2. **Hồ sơ HLV**
   - `create_coach_profile` - Tạo hồ sơ
   - `coach_profile_detail` - Chi tiết

3. **Sân bóng**
   - `create_stadium_profile` - Tạo hồ sơ
   - `create_stadium_job_posting` - Đăng tin

### Templates Cần Tạo
- `tournaments/recruit_coach.html`
- `tournaments/coach_recruitment_detail.html`
- `users/coach_profile_form.html`
- `organizations/stadium_job_posting_form.html`

### Templates Cần Cập Nhật
- `tournaments/team_detail.html` - Hiển thị HLV
- `tournaments/team_form.html` - Dropdown chọn HLV

👉 **Chi tiết code examples** trong `TOM_TAT_THAY_DOI.md`

---

## 🧪 Testing

### Kiểm tra ngay:
```bash
# 1. Chạy migrations
venv\Scripts\python.exe manage.py migrate

# 2. Kiểm tra roles đã được tạo
venv\Scripts\python.exe manage.py shell
>>> from users.models import Role
>>> Role.objects.filter(id__in=['COACH', 'STADIUM'])
# Should return 2 objects

# 3. Test tạo CoachProfile trong admin
# Vào /admin/users/coachprofile/add/

# 4. Test TeamCreationForm
# Tạo đội mới, kiểm tra dropdown HLV
```

---

## 🐛 Troubleshooting

### Migration errors?
```bash
venv\Scripts\python.exe manage.py showmigrations
```

### Role không xuất hiện?
Chạy lại migration:
```bash
venv\Scripts\python.exe manage.py migrate users 0020
```

### Import errors?
Kiểm tra:
- `from users.models import CoachProfile` ✅
- `from tournaments.models import CoachRecruitment` ✅

---

## 📊 Tổng Kết

### Đã Hoàn Thành (Backend) ✅
- 3 Models mới
- 3 Models cập nhật
- 3 Forms mới
- 4 Admin panels
- 1 Utils function
- 5 Migration files
- 2 Data migrations
- Full documentation

### Cần Làm Tiếp (Frontend) 📝
- ~8 Views
- ~6 Templates
- URL routing
- JavaScript interactions (optional)
- Email notifications (optional)

---

## 📞 Next Steps

1. **Ngay bây giờ**: Chạy `migrate` để áp dụng thay đổi
2. **Test trong Admin**: Tạo thử CoachProfile, StadiumProfile
3. **Implement Views**: Theo hướng dẫn trong `TOM_TAT_THAY_DOI.md`
4. **Tạo Templates**: UI cho các tính năng mới
5. **Notification System**: Thông báo khi có lời mời chiêu mộ

---

**🎉 Backend đã sẵn sàng! Giờ là lúc build giao diện người dùng.**

---

*Được tạo bởi AI Assistant - 13/10/2024*

