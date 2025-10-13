# 🔧 Đã Sửa Bug NoReverseMatch - tournament.pk

## ❌ Vấn Đề Ban Đầu

**Lỗi:** `NoReverseMatch at /jobs/ Reverse for 'tournament_detail' with keyword arguments '{'pk': ''}' not found`

**Nguyên nhân:** Khi có `JobPosting` của stadium (`posted_by='STADIUM'`), field `tournament` sẽ là `None`, nhưng template vẫn cố gắng truy cập `job.tournament.pk`.

---

## ✅ Đã Sửa 4 Files

### 1. **job_market.html** - Template chính
**File:** `tournaments/templates/tournaments/job_market.html`

**Trước:**
```django
<h6 class="card-subtitle mb-2 text-muted">
    <a href="{% url 'tournament_detail' pk=job.tournament.pk %}">{{ job.tournament.name }}</a>
</h6>
```

**Sau:**
```django
<h6 class="card-subtitle mb-2 text-muted">
    {% if job.tournament %}
        <a href="{% url 'tournament_detail' pk=job.tournament.pk %}">{{ job.tournament.name }}</a>
    {% elif job.stadium %}
        <span class="text-info">
            <i class="bi bi-building"></i> {{ job.stadium.stadium_name }}
        </span>
    {% else %}
        <span class="text-muted">Tổ chức khác</span>
    {% endif %}
</h6>
```

### 2. **job_detail.html** - Chi tiết job
**File:** `tournaments/templates/tournaments/job_detail.html`

**Trước:**
```django
<h5 class="text-muted">
    <a href="{% url 'tournament_detail' pk=job.tournament.pk %}">{{ job.tournament.name }}</a>
</h5>
```

**Sau:**
```django
<h5 class="text-muted">
    {% if job.tournament %}
        <a href="{% url 'tournament_detail' pk=job.tournament.pk %}">{{ job.tournament.name }}</a>
    {% elif job.stadium %}
        <span class="text-info">
            <i class="bi bi-building"></i> {{ job.stadium.stadium_name }}
        </span>
    {% else %}
        <span class="text-muted">Tổ chức khác</span>
    {% endif %}
</h5>
```

### 3. **views.py** - Notification logic
**File:** `tournaments/views.py` - Function `apply_for_job`

**Trước:**
```python
notification_message = f"{applicant_name} vừa ứng tuyển vào vị trí của bạn trong giải đấu '{job.tournament.name}'."
notification_url = request.build_absolute_uri(
    reverse('organizations:manage_jobs', kwargs={'tournament_pk': job.tournament.pk})
)
```

**Sau:**
```python
# Xác định tên tổ chức và URL
if job.tournament:
    org_name = job.tournament.name
    notification_url = request.build_absolute_uri(
        reverse('organizations:manage_jobs', kwargs={'tournament_pk': job.tournament.pk})
    )
elif job.stadium:
    org_name = job.stadium.stadium_name
    notification_url = request.build_absolute_uri(reverse('stadium_dashboard'))
else:
    org_name = "Tổ chức khác"
    notification_url = request.build_absolute_uri(reverse('job_market'))

notification_message = f"{applicant_name} vừa ứng tuyển vào vị trí của bạn tại '{org_name}'."
```

### 4. **create_review.html** - Review form
**File:** `organizations/templates/organizations/create_review.html`

**Trước:**
```django
<a href="{% url 'organizations:manage_jobs' tournament_pk=application.job.tournament.pk %}" class="btn btn-secondary">Quay lại</a>
```

**Sau:**
```django
{% if application.job.tournament %}
    <a href="{% url 'organizations:manage_jobs' tournament_pk=application.job.tournament.pk %}" class="btn btn-secondary">Quay lại</a>
{% elif application.job.stadium %}
    <a href="{% url 'stadium_dashboard' %}" class="btn btn-secondary">Quay lại</a>
{% else %}
    <a href="{% url 'job_market' %}" class="btn btn-secondary">Quay lại</a>
{% endif %}
```

---

## 🎯 Logic Hiển Thị

### Job Posting Types:

| posted_by | tournament | stadium | Hiển thị |
|-----------|------------|---------|----------|
| `TOURNAMENT` | ✅ Có | ❌ None | Link đến tournament |
| `STADIUM` | ❌ None | ✅ Có | Tên stadium + icon |
| Khác | ❌ None | ❌ None | "Tổ chức khác" |

### Location Display:

| Priority | Source | Fallback |
|----------|--------|----------|
| 1 | `job.location_detail` | - |
| 2 | `job.tournament.location_detail` | `job.tournament.get_region_display` |
| 3 | `job.stadium.location_detail` | `job.stadium.get_region_display` |
| 4 | - | "Không xác định" |

---

## 🧪 Test Cases

### Test 1: Tournament Job
```bash
# 1. Vào job market
http://localhost:8000/jobs/

# 2. Tìm job của tournament
# ✅ Hiển thị tên tournament + link
# ✅ Click vào → Đến trang tournament detail
```

### Test 2: Stadium Job
```bash
# 1. Vào job market
# 2. Tìm job của stadium
# ✅ Hiển thị tên stadium + icon building
# ✅ Không có link (chỉ hiển thị)
```

### Test 3: Apply for Stadium Job
```bash
# 1. Apply cho job của stadium
# 2. Check notification
# ✅ Notification có tên stadium đúng
# ✅ Link dẫn đến stadium dashboard
```

---

## 🚀 Kết Quả

### Trước (Bug):
- ❌ NoReverseMatch error
- ❌ Trang /jobs/ không load được
- ❌ Stadium jobs không hiển thị

### Sau (Fixed):
- ✅ Tất cả job types hiển thị đúng
- ✅ Links hoạt động chính xác
- ✅ Notifications đúng recipient
- ✅ UI/UX tốt hơn với icons

---

## 📊 Visual Indicators

### Tournament Job:
```html
<a href="/tournament/123/">Giải Vô Địch 2025</a>
```

### Stadium Job:
```html
<span class="text-info">
    <i class="bi bi-building"></i> Sân Vận Động ABC
</span>
```

### Other Organization:
```html
<span class="text-muted">Tổ chức khác</span>
```

---

**Đã sửa xong! Refresh trang /jobs/ và test ngay!** ✨

**Test ngay:**
1. Vào `http://localhost:8000/jobs/`
2. Kiểm tra cả job của tournament và stadium
3. Click vào từng loại job để xem chi tiết
4. Apply cho job của stadium để test notification
