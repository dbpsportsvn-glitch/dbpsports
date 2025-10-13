# Hướng Dẫn Vai Trò Mới: Huấn Luyện Viên & Sân Bóng

## Tổng Quan

Hệ thống đã được mở rộng với 2 vai trò mới:

### 1. Huấn Luyện Viên (COACH)
- **Mô tả**: Huấn luyện viên của đội bóng, có tất cả quyền quản lý đội như đội trưởng
- **Icon**: `bi-clipboard-check`

### 2. Sân Bóng (STADIUM)
- **Mô tả**: Chủ sân bóng, có thể đăng tin tuyển dụng và được BTC thêm vào nhân sự/nhà tài trợ
- **Icon**: `bi-house`

---

## Chi Tiết Thay Đổi

### A. Models Mới

#### 1. **CoachProfile** (users/models.py)
Hồ sơ chi tiết cho Huấn luyện viên:
- **Thông tin cơ bản**: Họ tên, ảnh đại diện, ngày sinh, giới thiệu
- **Kinh nghiệm**: Số năm kinh nghiệm, chứng chỉ HLV, chuyên môn
- **Thành tích**: Thành tích nổi bật, lịch sử huấn luyện
- **Liên hệ**: Số điện thoại, email, khu vực
- **Trạng thái**: Đang tìm đội (is_available)

#### 2. **StadiumProfile** (users/models.py)
Hồ sơ chi tiết cho Sân bóng:
- **Thông tin cơ bản**: Tên sân, logo, mô tả
- **Địa chỉ**: Địa chỉ chi tiết, khu vực, liên hệ
- **Thông tin sân**: Loại sân, sức chứa, số sân, tiện ích
- **Thanh toán**: Thông tin ngân hàng, QR code
- **Giờ hoạt động**: Lịch mở cửa

#### 3. **CoachRecruitment** (tournaments/models.py)
Quản lý chiêu mộ huấn luyện viên:
- **Trạng thái**: PENDING, ACCEPTED, REJECTED, CANCELED
- **Thông tin**: Mức lương, thời hạn hợp đồng, lời nhắn

---

### B. Cập Nhật Models Hiện Có

#### 1. **Team Model** (tournaments/models.py)
```python
# Trước:
coach_name = models.CharField(max_length=100, blank=True)

# Sau:
coach_name = models.CharField(max_length=100, blank=True, help_text="Tên HLV (dữ liệu cũ)")
coach = models.ForeignKey('users.CoachProfile', on_delete=models.SET_NULL, null=True, blank=True)
```

#### 2. **JobPosting Model** (organizations/models.py)
Thêm khả năng cho Sân bóng đăng tin:
```python
posted_by = models.CharField(choices=PostedBy.choices)  # TOURNAMENT hoặc STADIUM
tournament = models.ForeignKey(Tournament, null=True, blank=True)
stadium = models.ForeignKey(StadiumProfile, null=True, blank=True)
```

---

### C. Utility Functions

#### **user_can_manage_team(user, team)** (tournaments/utils.py)
Kiểm tra quyền quản lý đội:
```python
# Trả về True nếu user là:
# - Đội trưởng (team.captain)
# - Huấn luyện viên (team.coach.user)
```

---

## Hướng Dẫn Sử Dụng

### 1. Chạy Migrations

```bash
cd backend
venv\Scripts\python.exe manage.py migrate
```

### 2. Tạo Vai Trò Trong Admin

Migrations đã tự động tạo 2 vai trò mới. Bạn có thể kiểm tra tại:
- **Admin Panel** → **Users** → **Roles**

### 3. Tạo Hồ Sơ Huấn Luyện Viên

#### Qua Admin:
1. Vào **Users** → **Hồ sơ Huấn luyện viên** → **Thêm mới**
2. Chọn tài khoản người dùng
3. Điền đầy đủ thông tin
4. Có thể gán vào đội ngay hoặc để trống

#### Tính năng chiêu mộ (TODO - cần implement views):
1. Đội trưởng vào khu vực "Chiêu mộ HLV"
2. Tìm kiếm HLV (filter theo khu vực, kinh nghiệm...)
3. Gửi lời mời với mức lương, thời hạn
4. HLV nhận thông báo và chấp nhận/từ chối

### 4. Tạo Hồ Sơ Sân Bóng

#### Qua Admin:
1. Vào **Users** → **Hồ sơ Sân bóng** → **Thêm mới**
2. Điền thông tin sân bóng
3. Cập nhật giá thuê, tiện ích, giờ hoạt động

#### Đăng tin tuyển dụng:
1. Vào **Organizations** → **Tin Tuyển dụng** → **Thêm mới**
2. Chọn **Đăng bởi** = "Sân bóng"
3. Chọn sân bóng của bạn
4. Điền thông tin công việc cần tuyển

### 5. Phân Quyền Huấn Luyện Viên

Huấn luyện viên có **TẤT CẢ** quyền của đội trưởng:
- ✅ Thêm/Xóa/Sửa cầu thủ
- ✅ Đăng ký giải đấu
- ✅ Quản lý đội hình
- ✅ Chiêu mộ cầu thủ
- ✅ Gửi ghi chú cho BLV
- ✅ Quản lý tài chính đội

**Cách kiểm tra trong code:**
```python
from tournaments.utils import user_can_manage_team

if user_can_manage_team(request.user, team):
    # Cho phép thao tác
    pass
```

### 6. Tính Năng Sân Bóng

#### BTC có thể:
1. **Thêm sân bóng vào Nhà tài trợ**:
   - Vào Sponsorship
   - Chọn sponsor (user có vai trò STADIUM)
   - Hoặc nhập tay thông tin

2. **Thêm sân bóng vào Nhân sự**:
   - Vào TournamentStaff
   - Chọn user có StadiumProfile
   - Gán vai trò phù hợp

#### Sân bóng có thể:
1. Đăng tin tuyển dụng (BLV, Trọng tài, Media...)
2. Được hiển thị trong danh sách nhà tài trợ
3. Được BTC mời vào đội ngũ tổ chức

---

## TODO - Cần Implement Thêm

### Views & Forms (TODO #10)

#### 1. Form thêm HLV khi tạo đội
```python
# tournaments/forms.py
class TeamCreationForm(forms.ModelForm):
    # Thêm field để chọn HLV
    coach = forms.ModelChoiceField(
        queryset=CoachProfile.objects.filter(team__isnull=True),
        required=False
    )
```

#### 2. View chiêu mộ HLV
```python
# tournaments/views.py
@login_required
def recruit_coach(request, team_pk):
    # Danh sách HLV available
    # Form gửi lời mời
    pass

@login_required
def respond_coach_recruitment(request, recruitment_pk):
    # HLV chấp nhận/từ chối lời mời
    pass
```

#### 3. View quản lý sân bóng đăng tin
```python
# organizations/views.py
@login_required
def create_stadium_job_posting(request):
    # Chỉ cho phép user có StadiumProfile
    pass
```

#### 4. Cập nhật template hiển thị
- Hiển thị HLV trong trang chi tiết đội
- Form chiêu mộ HLV cho đội trưởng
- Dashboard cho sân bóng
- Danh sách tin tuyển dụng từ sân bóng

---

## Testing

### 1. Test Migrations
```bash
venv\Scripts\python.exe manage.py migrate
venv\Scripts\python.exe manage.py migrate users zero  # Rollback
venv\Scripts\python.exe manage.py migrate users       # Re-apply
```

### 2. Test Admin
- Kiểm tra các admin panel mới
- Tạo CoachProfile, StadiumProfile
- Tạo CoachRecruitment
- Cập nhật Team với coach mới

### 3. Test Permissions
```python
# Trong Django shell
from django.contrib.auth.models import User
from tournaments.models import Team
from users.models import CoachProfile
from tournaments.utils import user_can_manage_team

user = User.objects.first()
team = Team.objects.first()
coach_profile = CoachProfile.objects.create(user=user, full_name="Test Coach")
team.coach = coach_profile
team.save()

# Test
user_can_manage_team(user, team)  # Should return True
```

---

## Migration Files

### Users App
1. `0019_alter_role_id_stadiumprofile_coachprofile.py`
   - Thay đổi Role choices
   - Tạo CoachProfile, StadiumProfile

2. `0020_add_coach_stadium_roles.py`
   - Data migration: Tạo 2 role mới

### Tournaments App
1. `0062_coachrecruitment.py`
   - Tạo model CoachRecruitment

2. `0063_team_coach_alter_team_coach_name_and_more.py`
   - Thêm field coach vào Team
   - Alter coach_name

### Organizations App
1. `0007_jobposting_posted_by_jobposting_stadium_and_more.py`
   - Cập nhật JobPosting cho sân bóng

---

## Lưu Ý Quan Trọng

### 1. Backward Compatibility
- Field `coach_name` trong Team vẫn giữ nguyên (cho dữ liệu cũ)
- Nên migrate dữ liệu cũ từ `coach_name` → `CoachProfile` nếu cần

### 2. Data Migration (Recommended)
Nếu đã có dữ liệu `coach_name`, tạo script migrate:
```python
# Script migrate dữ liệu cũ
for team in Team.objects.exclude(coach_name=''):
    # Tạo CoachProfile từ coach_name
    # Gán vào team.coach
    pass
```

### 3. Foreign Key Cascade
- CoachProfile → Team: `on_delete=SET_NULL`
- StadiumProfile → JobPosting: `on_delete=CASCADE`
- CoachRecruitment → Coach/Team: `on_delete=CASCADE`

---

## Hỗ Trợ

Nếu có vấn đề, kiểm tra:
1. **Migration logs**: `venv\Scripts\python.exe manage.py showmigrations`
2. **Database**: Kiểm tra tables mới đã được tạo
3. **Admin**: Roles COACH và STADIUM đã có trong database
4. **Permissions**: Function `user_can_manage_team` hoạt động đúng

---

**Ngày cập nhật**: 13/10/2024
**Phiên bản**: 1.0

