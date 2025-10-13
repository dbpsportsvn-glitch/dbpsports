# 🚀 Hướng Dẫn Sử Dụng - Vai Trò Huấn Luyện Viên & Sân Bóng

## ✅ Đã Hoàn Thành Backend

Hệ thống đã có đầy đủ views và URLs để sử dụng ngay. Dưới đây là hướng dẫn chi tiết.

---

## 📍 Lối Vào Các Chức Năng

### 1. Đội Trưởng - Tìm Kiếm & Chiêu Mộ HLV

#### 🔹 Bước 1: Vào Trang Chi Tiết Đội
- URL: `/team/<team_id>/`
- Ví dụ: `/team/1/`

#### 🔹 Bước 2: Tìm Kiếm HLV
- **Nếu đội chưa có HLV**, click button **"Chiêu mộ HLV"** (cần thêm vào template team_detail.html)
- Hoặc truy cập trực tiếp: `/team/<team_id>/recruit-coach/`
- Ví dụ: `/team/1/recruit-coach/`

#### 🔹 Bước 3: Filter & Tìm Kiếm
Trang danh sách HLV hỗ trợ:
- ✅ Filter theo **khu vực**: `?region=MIEN_BAC`
- ✅ Filter theo **kinh nghiệm**: `?experience=5+` hoặc `?experience=10+`
- ✅ Tìm kiếm theo **tên/chứng chỉ**: `?q=AFC`

Ví dụ đầy đủ:
```
/team/1/recruit-coach/?region=MIEN_BAC&experience=5+&q=AFC
```

#### 🔹 Bước 4: Gửi Lời Mời
- Click button "Gửi lời mời" trên thẻ HLV
- Modal hiện ra với form:
  - Mức lương (VNĐ)
  - Thời hạn hợp đồng
  - Lời nhắn
- Submit → HLV nhận thông báo

#### 🔹 Bước 5: Loại Bỏ HLV (nếu cần)
```javascript
// POST request
fetch('/team/<team_id>/remove-coach/', {
    method: 'POST',
    headers: {
        'X-CSRFToken': csrfToken,
    }
})
```

### 2. Huấn Luyện Viên - Quản Lý Lời Mời

#### 🔹 Tạo Hồ Sơ HLV
- URL: `/coach/create/`
- Form đầy đủ các trường:
  - Thông tin cơ bản: Tên, ảnh, giới thiệu
  - Kinh nghiệm: Số năm, chứng chỉ, chuyên môn
  - Khu vực: Miền Bắc/Trung/Nam
  - ☑️ Đang tìm đội

#### 🔹 Dashboard HLV
- URL: `/coach/dashboard/`
- Hiển thị:
  - **Lời mời đang chờ** (PENDING)
  - **Lịch sử lời mời** (ACCEPTED/REJECTED)
  - Nút Accept/Reject cho mỗi lời mời

#### 🔹 Xem Chi Tiết Lời Mời
- URL: `/recruitment/<recruitment_id>/`
- Ví dụ: `/recruitment/1/`
- Hiển thị:
  - Thông tin đội
  - Mức lương đề nghị
  - Lời nhắn từ đội trưởng
  - Buttons: Chấp nhận / Từ chối

#### 🔹 Chấp Nhận/Từ Chối Lời Mời
```javascript
// POST request
fetch('/recruitment/<recruitment_id>/accept/', {
    method: 'POST',
    headers: {
        'X-CSRFToken': csrfToken,
    }
})

// Hoặc từ chối
fetch('/recruitment/<recruitment_id>/reject/', {
    method: 'POST',
    headers: {
        'X-CSRFToken': csrfToken,
    }
})
```

#### 🔹 Xem Hồ Sơ HLV
- URL: `/coach/<coach_id>/`
- Ví dụ: `/coach/1/`
- Hiển thị:
  - Thông tin đầy đủ
  - Đội đang huấn luyện (nếu có)
  - Lịch sử chiêu mộ (chỉ chính HLV đó xem được)

### 3. Sân Bóng - Đăng Tin & Quản Lý

#### 🔹 Tạo Hồ Sơ Sân Bóng
- URL: `/stadium/create/`
- Form gồm:
  - Thông tin cơ bản: Tên sân, logo, mô tả
  - Địa chỉ & liên hệ
  - Loại sân, sức chứa, tiện ích
  - Thông tin thanh toán

#### 🔹 Dashboard Sân Bóng
- URL: `/stadium/dashboard/`
- Hiển thị:
  - **Danh sách tin tuyển dụng** đã đăng
  - **Số ứng viên** cho mỗi tin
  - **Ứng viên mới** (status = PENDING)

#### 🔹 Đăng Tin Tuyển Dụng
- URL: `/stadium/job/create/`
- Form:
  - Chọn vai trò cần tuyển
  - Tiêu đề công việc
  - Mô tả chi tiết
  - Mức kinh phí
  - Địa điểm (mặc định lấy từ sân)

#### 🔹 Quản Lý Ứng Viên
- Vào `/admin/organizations/jobapplication/`
- Filter theo sân bóng
- Duyệt/Từ chối ứng viên

---

## 🔧 Cách Tích Hợp Vào Templates

### Template 1: `team_detail.html`

Thêm section hiển thị HLV:

```html
{% load static %}

<!-- Phần hiển thị HLV -->
<div class="card mb-4">
    <div class="card-header">
        <h5><i class="bi bi-clipboard-check"></i> Huấn luyện viên</h5>
    </div>
    <div class="card-body">
        {% if team.coach %}
            <!-- Đội có HLV -->
            <div class="d-flex align-items-center mb-3">
                {% if team.coach.avatar %}
                <img src="{{ team.coach.avatar.url }}" class="rounded-circle me-3" width="80" height="80" style="object-fit: cover;">
                {% else %}
                <div class="rounded-circle me-3 bg-secondary d-flex align-items-center justify-content-center" style="width: 80px; height: 80px;">
                    <i class="bi bi-person-badge text-white" style="font-size: 2rem;"></i>
                </div>
                {% endif %}
                
                <div class="flex-grow-1">
                    <h6 class="mb-1">{{ team.coach.full_name }}</h6>
                    {% if team.coach.coaching_license %}
                    <p class="mb-1 text-muted"><i class="bi bi-award"></i> {{ team.coach.coaching_license }}</p>
                    {% endif %}
                    {% if team.coach.years_of_experience %}
                    <p class="mb-0 text-muted"><i class="bi bi-calendar-check"></i> {{ team.coach.years_of_experience }} năm kinh nghiệm</p>
                    {% endif %}
                </div>
                
                <!-- Chỉ đội trưởng mới thấy nút loại bỏ -->
                {% if user == team.captain %}
                <button class="btn btn-sm btn-outline-danger" onclick="removeCoach({{ team.pk }})">
                    <i class="bi bi-x-circle"></i> Loại bỏ
                </button>
                {% endif %}
            </div>
            
            <a href="{% url 'coach_profile_detail' team.coach.pk %}" class="btn btn-sm btn-outline-primary">
                <i class="bi bi-eye"></i> Xem hồ sơ
            </a>
            
        {% else %}
            <!-- Đội chưa có HLV -->
            <p class="text-muted text-center mb-3">Đội chưa có huấn luyện viên</p>
            
            <!-- Chỉ đội trưởng/HLV mới thấy nút chiêu mộ -->
            {% if user == team.captain %}
            <a href="{% url 'recruit_coach_list' team.pk %}" class="btn btn-primary w-100">
                <i class="bi bi-search"></i> Tìm & Chiêu mộ HLV
            </a>
            {% endif %}
        {% endif %}
    </div>
</div>

<script>
function removeCoach(teamId) {
    if (confirm('Bạn có chắc muốn loại bỏ HLV khỏi đội?')) {
        fetch(`/team/${teamId}/remove-coach/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': '{{ csrf_token }}',
                'Content-Type': 'application/json'
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                location.reload();
            } else {
                alert(data.error || 'Có lỗi xảy ra');
            }
        });
    }
}
</script>
```

### Template 2: `recruit_coach_list.html` (MỚI)

File: `backend/tournaments/templates/tournaments/recruit_coach_list.html`

```html
{% extends 'base.html' %}
{% load static %}

{% block title %}Chiêu mộ Huấn luyện viên - {{ team.name }}{% endblock %}

{% block content %}
<div class="container my-5">
    <div class="row">
        <div class="col-12">
            <h2><i class="bi bi-search"></i> Tìm Huấn luyện viên cho {{ team.name }}</h2>
            <p class="text-muted">Tìm kiếm và gửi lời mời cho HLV phù hợp với đội bóng của bạn</p>
        </div>
    </div>
    
    <!-- Filters -->
    <div class="row mb-4">
        <div class="col-md-12">
            <form method="get" class="row g-3">
                <div class="col-md-3">
                    <label class="form-label">Khu vực</label>
                    <select name="region" class="form-select">
                        <option value="">Tất cả</option>
                        {% for value, label in region_choices %}
                        <option value="{{ value }}" {% if current_region == value %}selected{% endif %}>{{ label }}</option>
                        {% endfor %}
                    </select>
                </div>
                
                <div class="col-md-3">
                    <label class="form-label">Kinh nghiệm</label>
                    <select name="experience" class="form-select">
                        <option value="">Tất cả</option>
                        <option value="5+" {% if current_exp == '5+' %}selected{% endif %}>5+ năm</option>
                        <option value="10+" {% if current_exp == '10+' %}selected{% endif %}>10+ năm</option>
                    </select>
                </div>
                
                <div class="col-md-4">
                    <label class="form-label">Tìm kiếm</label>
                    <input type="text" name="q" class="form-control" placeholder="Tên, chứng chỉ..." value="{{ search_query }}">
                </div>
                
                <div class="col-md-2 d-flex align-items-end">
                    <button type="submit" class="btn btn-primary w-100">
                        <i class="bi bi-funnel"></i> Lọc
                    </button>
                </div>
            </form>
        </div>
    </div>
    
    <!-- Danh sách HLV -->
    <div class="row">
        {% if coaches %}
            {% for coach in coaches %}
            <div class="col-md-6 col-lg-4 mb-4">
                <div class="card h-100">
                    <div class="card-body">
                        <div class="d-flex align-items-center mb-3">
                            {% if coach.avatar %}
                            <img src="{{ coach.avatar.url }}" class="rounded-circle me-3" width="60" height="60" style="object-fit: cover;">
                            {% else %}
                            <div class="rounded-circle me-3 bg-secondary d-flex align-items-center justify-content-center" style="width: 60px; height: 60px;">
                                <i class="bi bi-person-badge text-white fs-4"></i>
                            </div>
                            {% endif %}
                            
                            <div>
                                <h6 class="mb-0">{{ coach.full_name }}</h6>
                                <small class="text-muted">{{ coach.get_region_display }}</small>
                            </div>
                        </div>
                        
                        {% if coach.coaching_license %}
                        <p class="mb-1"><i class="bi bi-award text-warning"></i> {{ coach.coaching_license }}</p>
                        {% endif %}
                        
                        {% if coach.years_of_experience %}
                        <p class="mb-1"><i class="bi bi-calendar-check text-info"></i> {{ coach.years_of_experience }} năm kinh nghiệm</p>
                        {% endif %}
                        
                        {% if coach.specialization %}
                        <p class="mb-2 text-muted small">{{ coach.specialization }}</p>
                        {% endif %}
                        
                        <div class="d-flex gap-2 mt-3">
                            <a href="{% url 'coach_profile_detail' coach.pk %}" class="btn btn-sm btn-outline-primary flex-grow-1">
                                <i class="bi bi-eye"></i> Xem hồ sơ
                            </a>
                            
                            {% if coach.id in sent_offers %}
                            <button class="btn btn-sm btn-secondary flex-grow-1" disabled>
                                <i class="bi bi-check-circle"></i> Đã gửi lời mời
                            </button>
                            {% else %}
                            <button class="btn btn-sm btn-success flex-grow-1" onclick="sendOffer({{ coach.pk }})">
                                <i class="bi bi-envelope"></i> Gửi lời mời
                            </button>
                            {% endif %}
                        </div>
                    </div>
                </div>
            </div>
            {% endfor %}
        {% else %}
            <div class="col-12">
                <div class="alert alert-info text-center">
                    <i class="bi bi-info-circle fs-3 d-block mb-2"></i>
                    <p class="mb-0">Không tìm thấy HLV phù hợp. Thử thay đổi bộ lọc hoặc tạo tin tuyển dụng.</p>
                </div>
            </div>
        {% endif %}
    </div>
</div>

<!-- Modal gửi lời mời -->
<div class="modal fade" id="offerModal" tabindex="-1">
    <div class="modal-dialog">
        <div class="modal-content">
            <div class="modal-header">
                <h5 class="modal-title">Gửi lời mời chiêu mộ</h5>
                <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
            </div>
            <div class="modal-body">
                <form id="offerForm">
                    {% csrf_token %}
                    <input type="hidden" id="coachId" name="coach_id">
                    
                    <div class="mb-3">
                        <label class="form-label">Mức lương đề nghị (VNĐ)</label>
                        <input type="number" name="salary_offer" class="form-control" placeholder="Ví dụ: 5000000">
                    </div>
                    
                    <div class="mb-3">
                        <label class="form-label">Thời hạn hợp đồng</label>
                        <input type="text" name="contract_duration" class="form-control" placeholder="Ví dụ: 1 năm, 6 tháng...">
                    </div>
                    
                    <div class="mb-3">
                        <label class="form-label">Lời nhắn</label>
                        <textarea name="message" class="form-control" rows="4" placeholder="Giới thiệu về đội và kế hoạch phát triển..."></textarea>
                    </div>
                </form>
            </div>
            <div class="modal-footer">
                <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Hủy</button>
                <button type="button" class="btn btn-primary" onclick="submitOffer()">Gửi lời mời</button>
            </div>
        </div>
    </div>
</div>

<script>
let currentCoachId = null;

function sendOffer(coachId) {
    currentCoachId = coachId;
    document.getElementById('coachId').value = coachId;
    const modal = new bootstrap.Modal(document.getElementById('offerModal'));
    modal.show();
}

function submitOffer() {
    const formData = new FormData(document.getElementById('offerForm'));
    
    fetch(`/team/{{ team.pk }}/coach/${currentCoachId}/send-offer/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': '{{ csrf_token }}'
        },
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert('Đã gửi lời mời thành công!');
            location.reload();
        } else {
            alert(data.error || 'Có lỗi xảy ra');
        }
    });
}
</script>
{% endblock %}
```

---

## 📱 Quick Links Reference

### Đội Trưởng:
```
/team/<team_id>/                     # Chi tiết đội
/team/<team_id>/recruit-coach/       # Tìm & chiêu mộ HLV
/team/<team_id>/remove-coach/        # Loại bỏ HLV (POST)
```

### Huấn Luyện Viên:
```
/coach/create/                       # Tạo/sửa hồ sơ HLV
/coach/<coach_id>/                   # Chi tiết hồ sơ HLV
/coach/dashboard/                    # Dashboard HLV
/recruitment/<id>/                   # Chi tiết lời mời
/recruitment/<id>/accept/            # Chấp nhận (POST)
/recruitment/<id>/reject/            # Từ chối (POST)
```

### Sân Bóng:
```
/stadium/create/                     # Tạo/sửa hồ sơ sân
/stadium/dashboard/                  # Dashboard sân
/stadium/job/create/                 # Đăng tin tuyển dụng
```

---

## ✅ Checklist Hoàn Thiện Frontend

### Templates Cần Tạo (4/4 - chưa tạo):
- [ ] `tournaments/recruit_coach_list.html` - Danh sách HLV
- [ ] `tournaments/coach_recruitment_detail.html` - Chi tiết lời mời
- [ ] `tournaments/coach_dashboard.html` - Dashboard HLV
- [ ] `users/coach_profile_detail.html` - Hồ sơ HLV
- [ ] `users/coach_profile_form.html` - Form tạo/sửa hồ sơ HLV
- [ ] `users/stadium_profile_form.html` - Form tạo/sửa sân
- [ ] `users/stadium_dashboard.html` - Dashboard sân
- [ ] `users/stadium_job_posting_form.html` - Form đăng tin

### Templates Cần Cập Nhật (1/1 - chưa update):
- [ ] `tournaments/team_detail.html` - Thêm section HLV

---

## 🎯 Next Steps

1. **Tạo các templates** theo mẫu ở trên
2. **Test tất cả flows**:
   - Đội trưởng tìm HLV
   - HLV nhận & chấp nhận lời mời
   - Sân bóng đăng tin tuyển dụng
3. **Styling**: Thêm CSS/Bootstrap cho đẹp
4. **Notifications**: Kiểm tra thông báo hoạt động đúng

---

**Backend đã 100% sẵn sàng! Chỉ cần tạo templates là có thể sử dụng ngay!** 🚀

