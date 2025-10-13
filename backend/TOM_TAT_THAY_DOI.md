# Tóm Tắt Các Thay Đổi - Vai Trò Mới: Huấn Luyện Viên & Sân Bóng

## ✅ Đã Hoàn Thành

### 1. **Models Mới**
- ✅ `CoachProfile` - Hồ sơ Huấn luyện viên (users/models.py)
- ✅ `StadiumProfile` - Hồ sơ Sân bóng (users/models.py)
- ✅ `CoachRecruitment` - Chiêu mộ HLV (tournaments/models.py)

### 2. **Cập Nhật Models**
- ✅ `Role.ROLE_CHOICES` - Thêm COACH và STADIUM (users/models.py)
- ✅ `Team.coach` - ForeignKey đến CoachProfile (tournaments/models.py)
- ✅ `JobPosting` - Cho phép Sân bóng đăng tin (organizations/models.py)

### 3. **Forms**
- ✅ `TeamCreationForm` - Thêm trường chọn HLV (tournaments/forms.py)
- ✅ `CoachProfileForm` - Form tạo/sửa hồ sơ HLV (tournaments/forms.py)
- ✅ `CoachRecruitmentForm` - Form chiêu mộ HLV (tournaments/forms.py)

### 4. **Admin**
- ✅ `CoachProfileAdmin` (users/admin.py)
- ✅ `StadiumProfileAdmin` (users/admin.py)
- ✅ `CoachRecruitmentAdmin` (tournaments/admin.py)
- ✅ `JobPostingAdmin` - Cập nhật hiển thị (organizations/admin.py)

### 5. **Utils & Permissions**
- ✅ `user_can_manage_team()` - Helper function kiểm tra quyền (tournaments/utils.py)

### 6. **Migrations**
- ✅ `users/0019_alter_role_id_stadiumprofile_coachprofile.py`
- ✅ `users/0020_add_coach_stadium_roles.py` (data migration)
- ✅ `tournaments/0062_coachrecruitment.py`
- ✅ `tournaments/0063_team_coach_alter_team_coach_name_and_more.py`
- ✅ `organizations/0007_jobposting_posted_by_jobposting_stadium_and_more.py`

### 7. **Tài Liệu**
- ✅ `HUONG_DAN_VAI_TRO_MOI.md` - Hướng dẫn chi tiết
- ✅ `TOM_TAT_THAY_DOI.md` - File này

---

## 🚀 Cách Áp Dụng

### Bước 1: Chạy Migrations
```bash
cd D:\dbpsports\backend
venv\Scripts\python.exe manage.py migrate
```

### Bước 2: Kiểm Tra Admin
1. Mở `http://localhost:8000/admin/`
2. Vào **Users** → **Roles** → Kiểm tra COACH và STADIUM đã có
3. Tạo thử CoachProfile và StadiumProfile

### Bước 3: Test Tính Năng
1. **Tạo đội với HLV**: Vào form tạo đội, chọn HLV từ dropdown
2. **Chiêu mộ HLV**: (cần implement view - xem phần TODO bên dưới)
3. **Sân bóng đăng tin**: Vào JobPosting admin, chọn posted_by=STADIUM

---

## 📋 TODO - Cần Implement Thêm (Views & Templates)

### 1. Views cho Huấn luyện viên

#### a. View tạo/cập nhật CoachProfile
```python
# users/views.py
@login_required
def create_coach_profile(request):
    if hasattr(request.user, 'coach_profile'):
        coach_profile = request.user.coach_profile
        form = CoachProfileForm(request.POST or None, instance=coach_profile)
    else:
        form = CoachProfileForm(request.POST or None)
    
    if form.is_valid():
        coach = form.save(commit=False)
        coach.user = request.user
        coach.save()
        messages.success(request, "Hồ sơ HLV đã được lưu!")
        return redirect('coach_profile_detail', pk=coach.pk)
    
    return render(request, 'users/coach_profile_form.html', {'form': form})
```

#### b. View chiêu mộ HLV
```python
# tournaments/views.py
@login_required
def recruit_coach(request, team_pk):
    team = get_object_or_404(Team, pk=team_pk)
    
    # Kiểm tra quyền
    from tournaments.utils import user_can_manage_team
    if not user_can_manage_team(request.user, team):
        return HttpResponseForbidden("Bạn không có quyền chiêu mộ HLV cho đội này.")
    
    # Danh sách HLV available
    available_coaches = CoachProfile.objects.filter(
        team__isnull=True,
        is_available=True
    )
    
    return render(request, 'tournaments/recruit_coach.html', {
        'team': team,
        'coaches': available_coaches
    })

@login_required
@require_POST
def send_coach_offer(request, team_pk, coach_pk):
    team = get_object_or_404(Team, pk=team_pk)
    coach = get_object_or_404(CoachProfile, pk=coach_pk)
    
    # Kiểm tra quyền
    from tournaments.utils import user_can_manage_team
    if not user_can_manage_team(request.user, team):
        return JsonResponse({'error': 'No permission'}, status=403)
    
    form = CoachRecruitmentForm(request.POST)
    if form.is_valid():
        recruitment = form.save(commit=False)
        recruitment.team = team
        recruitment.coach = coach
        recruitment.save()
        
        # Gửi thông báo cho HLV
        Notification.objects.create(
            user=coach.user,
            title=f"Lời mời từ đội {team.name}",
            message=f"Đội {team.name} muốn chiêu mộ bạn làm HLV!",
            notification_type='GENERIC',
            related_url=reverse('coach_recruitment_detail', args=[recruitment.pk])
        )
        
        return JsonResponse({'success': True})
    
    return JsonResponse({'error': form.errors}, status=400)

@login_required
def respond_to_recruitment(request, recruitment_pk, action):
    recruitment = get_object_or_404(CoachRecruitment, pk=recruitment_pk)
    
    # Chỉ HLV mới có thể trả lời
    if request.user != recruitment.coach.user:
        return HttpResponseForbidden()
    
    if action == 'accept':
        recruitment.status = CoachRecruitment.Status.ACCEPTED
        recruitment.team.coach = recruitment.coach
        recruitment.team.save()
        
        # Cập nhật coach profile
        recruitment.coach.team = recruitment.team
        recruitment.coach.is_available = False
        recruitment.coach.save()
        
        messages.success(request, f"Bạn đã trở thành HLV của đội {recruitment.team.name}!")
    
    elif action == 'reject':
        recruitment.status = CoachRecruitment.Status.REJECTED
        messages.info(request, "Đã từ chối lời mời.")
    
    recruitment.save()
    return redirect('coach_dashboard')
```

### 2. Views cho Sân bóng

```python
# organizations/views.py
@login_required
def create_stadium_job_posting(request):
    # Kiểm tra user có StadiumProfile
    if not hasattr(request.user, 'stadium_profile'):
        messages.error(request, "Bạn cần tạo hồ sơ Sân bóng trước.")
        return redirect('create_stadium_profile')
    
    stadium = request.user.stadium_profile
    
    if request.method == 'POST':
        # Tạo JobPosting với posted_by=STADIUM
        job = JobPosting.objects.create(
            posted_by=JobPosting.PostedBy.STADIUM,
            stadium=stadium,
            role_required_id=request.POST['role'],
            title=request.POST['title'],
            description=request.POST['description'],
            budget=request.POST.get('budget', ''),
            location_detail=request.POST.get('location_detail', '')
        )
        messages.success(request, "Đã đăng tin tuyển dụng!")
        return redirect('stadium_dashboard')
    
    roles = Role.objects.all()
    return render(request, 'organizations/stadium_job_posting_form.html', {
        'stadium': stadium,
        'roles': roles
    })
```

### 3. Templates cần tạo

#### a. `users/coach_profile_form.html`
- Form tạo/sửa hồ sơ HLV
- Hiển thị preview ảnh avatar
- Các trường thông tin đầy đủ

#### b. `tournaments/recruit_coach.html`
- Danh sách HLV available
- Filter theo khu vực, kinh nghiệm
- Button gửi lời mời
- Modal form nhập mức lương, hợp đồng

#### c. `tournaments/coach_recruitment_detail.html`
- Chi tiết lời mời chiêu mộ
- Buttons Accept/Reject cho HLV
- Hiển thị trạng thái

#### d. `organizations/stadium_job_posting_form.html`
- Form đăng tin tuyển dụng cho sân bóng
- Chọn vai trò cần tuyển
- Nhập mô tả công việc

### 4. URLs cần thêm

```python
# users/urls.py
path('coach/create/', views.create_coach_profile, name='create_coach_profile'),
path('coach/<int:pk>/', views.coach_profile_detail, name='coach_profile_detail'),
path('stadium/create/', views.create_stadium_profile, name='create_stadium_profile'),

# tournaments/urls.py
path('team/<int:team_pk>/recruit-coach/', views.recruit_coach, name='recruit_coach'),
path('team/<int:team_pk>/coach/<int:coach_pk>/offer/', views.send_coach_offer, name='send_coach_offer'),
path('recruitment/<int:recruitment_pk>/<str:action>/', views.respond_to_recruitment, name='respond_to_recruitment'),

# organizations/urls.py
path('stadium/job/create/', views.create_stadium_job_posting, name='create_stadium_job_posting'),
```

### 5. Cập nhật Template hiện có

#### `tournaments/team_detail.html`
```html
<!-- Thêm section hiển thị HLV -->
{% if team.coach %}
<div class="card mb-3">
    <div class="card-header">
        <h5><i class="bi bi-clipboard-check"></i> Huấn luyện viên</h5>
    </div>
    <div class="card-body">
        <div class="d-flex align-items-center">
            {% if team.coach.avatar %}
            <img src="{{ team.coach.avatar.url }}" class="rounded-circle me-3" width="60" height="60">
            {% endif %}
            <div>
                <h6 class="mb-1">{{ team.coach.full_name }}</h6>
                <small class="text-muted">
                    {% if team.coach.coaching_license %}{{ team.coach.coaching_license }}{% endif %}
                </small>
            </div>
        </div>
    </div>
</div>
{% elif user_can_manage_team %}
<div class="card mb-3">
    <div class="card-body text-center">
        <p class="text-muted">Đội chưa có HLV</p>
        <a href="{% url 'recruit_coach' team.pk %}" class="btn btn-primary">
            <i class="bi bi-search"></i> Chiêu mộ HLV
        </a>
    </div>
</div>
{% endif %}
```

### 6. Cập nhật views hiện có

#### `tournaments/views.py - team_detail`
```python
def team_detail(request, pk):
    # ... existing code ...
    
    # Thêm biến context
    user_can_manage = user_can_manage_team(request.user, team)
    
    context = {
        'team': team,
        'user_can_manage_team': user_can_manage,  # Thay vì chỉ check captain
        # ... other context
    }
```

#### `tournaments/views.py - Các view khác`
Thay thế tất cả:
```python
if request.user != team.captain:
    # Error
```

Bằng:
```python
from tournaments.utils import user_can_manage_team

if not user_can_manage_team(request.user, team):
    # Error
```

---

## 🧪 Testing Checklist

### Models
- [ ] Tạo CoachProfile qua admin
- [ ] Tạo StadiumProfile qua admin
- [ ] Tạo Team với coach
- [ ] Tạo CoachRecruitment
- [ ] JobPosting với posted_by=STADIUM

### Permissions
- [ ] Captain có thể quản lý đội
- [ ] Coach có thể quản lý đội
- [ ] User khác KHÔNG có quyền

### Migrations
- [ ] Chạy migrate thành công
- [ ] 2 Role mới đã được tạo
- [ ] Rollback hoạt động đúng

### Forms
- [ ] TeamCreationForm hiển thị dropdown HLV
- [ ] Validation: không được chọn cả coach và coach_name
- [ ] CoachRecruitmentForm hoạt động

---

## 📊 Thống Kê Thay Đổi

- **Models mới**: 3 (CoachProfile, StadiumProfile, CoachRecruitment)
- **Models cập nhật**: 3 (Role, Team, JobPosting)
- **Forms mới**: 3 (CoachProfileForm, CoachRecruitmentForm, TeamCreationForm updated)
- **Admin mới**: 4
- **Utils mới**: 1 (user_can_manage_team)
- **Migration files**: 5
- **Views cần thêm**: ~8
- **Templates cần thêm**: ~4

---

## 🔧 Các Bước Tiếp Theo (Theo Thứ Tự Ưu Tiên)

1. **Implement views chiêu mộ HLV** (cao)
   - recruit_coach view
   - send_coach_offer view
   - respond_to_recruitment view

2. **Tạo templates tương ứng** (cao)
   - recruit_coach.html
   - coach_recruitment_detail.html

3. **Cập nhật team_detail template** (trung bình)
   - Hiển thị thông tin HLV
   - Button chiêu mộ

4. **Views cho Sân bóng** (thấp)
   - create_stadium_job_posting
   - stadium_dashboard

5. **Notification system** (thấp)
   - Thông báo khi có lời mời chiêu mộ
   - Email notification

---

## 📞 Liên Hệ & Hỗ Trợ

Nếu gặp vấn đề:
1. Kiểm tra migrations: `venv\Scripts\python.exe manage.py showmigrations`
2. Xem logs database
3. Kiểm tra admin panel
4. Đọc file `HUONG_DAN_VAI_TRO_MOI.md` để biết chi tiết

---

**Ngày hoàn thành**: 13/10/2024  
**Tổng thời gian**: ~2 giờ  
**Status**: ✅ Backend hoàn tất, Frontend cần implement

