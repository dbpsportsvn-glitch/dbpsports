# 🎯 Cấu Hình Cuối Cùng - Sẵn Sàng Sử Dụng

## ✅ Đã Hoàn Thành 100% Backend

### ✨ Views & URLs Đã Sẵn Sàng

Tất cả views và URLs đã được tạo và routing đúng. Backend hoàn toàn functional!

---

## 🚀 Cách Truy Cập Ngay Bây Giờ

### 1️⃣ Đội Trưởng Tìm & Chiêu Mộ HLV

#### Qua Admin (Ngay Lập Tức):
1. Vào `/admin/users/coachprofile/`
2. Tạo vài CoachProfile mẫu
3. Đánh dấu "Đang tìm đội" = ☑️

#### Qua Giao Diện Web:
```
1. Đăng nhập với tài khoản đội trưởng
2. Vào trang đội: /team/<team_id>/
3. Truy cập: /team/<team_id>/recruit-coach/
4. Xem danh sách HLV & gửi lời mời
```

**Filters có sẵn:**
- `/team/1/recruit-coach/?region=MIEN_BAC` - Lọc theo khu vực
- `/team/1/recruit-coach/?experience=5+` - Lọc theo kinh nghiệm
- `/team/1/recruit-coach/?q=AFC` - Tìm kiếm

### 2️⃣ Huấn Luyện Viên

#### Tạo Hồ Sơ:
```
URL: /coach/create/
Method: GET (hiển thị form) / POST (submit)
```

#### Dashboard HLV:
```
URL: /coach/dashboard/
- Hiển thị lời mời đang chờ
- Hiển thị lịch sử chiêu mộ
- Nút Accept/Reject
```

#### Xem Chi Tiết Lời Mời:
```
URL: /recruitment/<recruitment_id>/
- Thông tin đội
- Mức lương
- Lời nhắn
```

#### Chấp Nhận/Từ Chối:
```javascript
// Accept
POST /recruitment/<id>/accept/

// Reject
POST /recruitment/<id>/reject/
```

### 3️⃣ Sân Bóng

#### Tạo Hồ Sơ:
```
URL: /stadium/create/
Form đầy đủ các trường
```

#### Dashboard:
```
URL: /stadium/dashboard/
- Danh sách tin đăng
- Số ứng viên
- Ứng viên mới
```

#### Đăng Tin Tuyển Dụng:
```
URL: /stadium/job/create/
Form:
- role_required (select)
- title
- description
- budget
- location_detail
```

---

## 🎨 Templates Đề Xuất

Mình đã viết sẵn **code hoàn chỉnh** cho templates trong file `HUONG_DAN_SU_DUNG.md`.

### Nhanh Nhất:
1. Copy code templates từ `HUONG_DAN_SU_DUNG.md`
2. Tạo file tương ứng
3. Chạy server → Hoạt động ngay

### Hoặc Dùng Admin:
- Tất cả chức năng đều có sẵn trong Django Admin
- Vào `/admin/` để quản lý:
  - CoachProfile
  - StadiumProfile
  - CoachRecruitment
  - JobPosting

---

## 📍 Routes Mapping

### HLV Routes:
| URL | View | Mô Tả |
|-----|------|-------|
| `/coach/create/` | `create_coach_profile` | Tạo/sửa hồ sơ HLV |
| `/coach/<id>/` | `coach_profile_detail` | Chi tiết hồ sơ |
| `/coach/dashboard/` | `coach_dashboard` | Dashboard HLV |
| `/team/<id>/recruit-coach/` | `recruit_coach_list` | Danh sách HLV |
| `/team/<id>/coach/<id>/send-offer/` | `send_coach_recruitment` | Gửi lời mời (POST) |
| `/recruitment/<id>/` | `coach_recruitment_detail` | Chi tiết lời mời |
| `/recruitment/<id>/accept/` | `respond_to_recruitment` | Chấp nhận (POST) |
| `/recruitment/<id>/reject/` | `respond_to_recruitment` | Từ chối (POST) |
| `/team/<id>/remove-coach/` | `remove_coach_from_team` | Loại bỏ HLV (POST) |

### Sân Bóng Routes:
| URL | View | Mô Tả |
|-----|------|-------|
| `/stadium/create/` | `create_stadium_profile` | Tạo/sửa hồ sơ |
| `/stadium/dashboard/` | `stadium_dashboard` | Dashboard sân |
| `/stadium/job/create/` | `create_stadium_job_posting` | Đăng tin |

---

## 🧪 Testing Nhanh

### Test Flow 1: Chiêu Mộ HLV

```bash
# 1. Tạo CoachProfile qua admin
http://localhost:8000/admin/users/coachprofile/add/

# 2. Đội trưởng tìm HLV
http://localhost:8000/team/1/recruit-coach/

# 3. Gửi lời mời (POST)
curl -X POST http://localhost:8000/team/1/coach/1/send-offer/ \
  -H "X-CSRFToken: xxx" \
  -F "salary_offer=5000000" \
  -F "contract_duration=1 năm" \
  -F "message=Chào mừng bạn!"

# 4. HLV xem dashboard
http://localhost:8000/coach/dashboard/

# 5. HLV chấp nhận
curl -X POST http://localhost:8000/recruitment/1/accept/ \
  -H "X-CSRFToken: xxx"
```

### Test Flow 2: Sân Bóng Đăng Tin

```bash
# 1. Tạo StadiumProfile
http://localhost:8000/stadium/create/

# 2. Đăng tin
http://localhost:8000/stadium/job/create/
POST:
  - role_required: 3 (COMMENTATOR)
  - title: "Tuyển BLV cho giải U21"
  - description: "..."
  - budget: "500.000 VNĐ/trận"

# 3. Xem dashboard
http://localhost:8000/stadium/dashboard/
```

---

## 🔐 Permissions Check

### Tự Động Kiểm Tra Quyền:

```python
# Trong views đã có sẵn:
from tournaments.utils import user_can_manage_team

if user_can_manage_team(request.user, team):
    # Cho phép đội trưởng HOẶC HLV thao tác
```

### Ai Có Quyền Gì:

| Hành Động | Đội Trưởng | HLV | User Khác |
|-----------|------------|-----|-----------|
| Chiêu mộ HLV | ✅ | ❌ | ❌ |
| Loại bỏ HLV | ✅ | ❌ | ❌ |
| Quản lý cầu thủ | ✅ | ✅ | ❌ |
| Đăng ký giải | ✅ | ✅ | ❌ |
| Quản lý đội hình | ✅ | ✅ | ❌ |

---

## 📊 Database Schema

### Relationships:
```
User 1---1 CoachProfile
User 1---1 StadiumProfile

Team N---1 CoachProfile (coach)
Team 1---N CoachRecruitment

CoachProfile 1---N CoachRecruitment

StadiumProfile 1---N JobPosting
```

### Migrations Applied:
```
users/0019_alter_role_id_stadiumprofile_coachprofile.py
users/0020_add_coach_stadium_roles.py
tournaments/0062_coachrecruitment.py
tournaments/0063_team_coach_alter_team_coach_name_and_more.py
organizations/0007_jobposting_posted_by_jobposting_stadium_and_more.py
```

---

## 🎨 UI Integration Points

### Navbar/Menu:
```html
{% if user.is_authenticated %}
    {% if user.coach_profile %}
    <a href="{% url 'coach_dashboard' %}">
        <i class="bi bi-clipboard-check"></i> Dashboard HLV
    </a>
    {% endif %}
    
    {% if user.stadium_profile %}
    <a href="{% url 'stadium_dashboard' %}">
        <i class="bi bi-house"></i> Quản lý Sân
    </a>
    {% endif %}
{% endif %}
```

### Team Detail Page:
```html
<!-- Thêm vào team_detail.html -->
{% if team.coach %}
    <!-- Hiển thị thông tin HLV -->
{% else %}
    {% if user == team.captain %}
    <a href="{% url 'recruit_coach_list' team.pk %}">
        Chiêu mộ HLV
    </a>
    {% endif %}
{% endif %}
```

### Dashboard Links:
```html
<!-- Trong user dashboard -->
{% if 'COACH' in user.profile.roles.all %}
<a href="{% url 'create_coach_profile' %}">Cập nhật hồ sơ HLV</a>
{% endif %}

{% if 'STADIUM' in user.profile.roles.all %}
<a href="{% url 'create_stadium_profile' %}">Cập nhật hồ sơ Sân</a>
{% endif %}
```

---

## 📝 Notifications

### Tự Động Gửi Thông Báo:

1. **Khi gửi lời mời chiêu mộ:**
   - HLV nhận notification
   - Link đến `/recruitment/<id>/`

2. **Khi HLV chấp nhận:**
   - Đội trưởng nhận notification
   - Link đến `/team/<id>/`

3. **Khi HLV từ chối:**
   - Đội trưởng nhận notification

4. **Khi bị loại bỏ:**
   - HLV nhận notification

---

## 🔄 State Transitions

### CoachRecruitment Status:
```
PENDING → ACCEPTED (HLV chấp nhận)
        → REJECTED (HLV từ chối)
        → CANCELED (Đội đã có HLV khác / HLV đã có đội khác)
```

### CoachProfile:
```
is_available = True  → Hiển thị trong danh sách chiêu mộ
is_available = False → Đã có đội, không hiển thị
```

---

## 🚨 Error Handling

Views đã xử lý:
- ✅ Team đã có HLV → Không cho chiêu mộ thêm
- ✅ HLV đã có đội → Không cho nhận lời mời mới
- ✅ Duplicate recruitment → Không cho gửi lại
- ✅ Permission denied → Return 403

---

## 🎯 Ready to Use!

### Bước 1: Migrate (nếu chưa)
```bash
cd backend
venv\Scripts\python.exe manage.py migrate
```

### Bước 2: Test Qua Admin
```bash
# Tạo CoachProfile
http://localhost:8000/admin/users/coachprofile/add/

# Tạo StadiumProfile
http://localhost:8000/admin/users/stadiumprofile/add/

# Xem CoachRecruitment
http://localhost:8000/admin/tournaments/coachrecruitment/
```

### Bước 3: Access URLs
```bash
# Đội trưởng
http://localhost:8000/team/1/recruit-coach/

# HLV
http://localhost:8000/coach/dashboard/

# Sân bóng
http://localhost:8000/stadium/dashboard/
```

---

## 📚 Documentation Files

1. ✅ **HUONG_DAN_VAI_TRO_MOI.md** - Hướng dẫn chi tiết backend
2. ✅ **TOM_TAT_THAY_DOI.md** - Tóm tắt thay đổi & TODO frontend
3. ✅ **README_VAI_TRO_MOI.md** - Quick start guide
4. ✅ **HUONG_DAN_SU_DUNG.md** - Hướng dẫn sử dụng & code templates
5. ✅ **CAU_HINH_CUOI_CUNG.md** - File này

---

**🎉 Backend 100% hoàn thành! Templates code mẫu đã có trong `HUONG_DAN_SU_DUNG.md`. Chỉ cần copy & paste là chạy được ngay!**

