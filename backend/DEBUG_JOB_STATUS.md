# 🔍 Debug Job Status Auto-Close

## ❓ Vấn Đề

Job status không tự động chuyển từ "Đang mở" → "Đã đóng" sau khi accept application.

---

## ✅ Đã Sửa

### 1. **Improved Logic**
```python
# Trước
application.job.status = 'CLOSED'

# Sau  
job = application.job
job.status = JobPosting.Status.CLOSED  # ← Sử dụng enum
job.save()
```

### 2. **Better Redirect**
```python
# Trước: redirect('stadium_job_applications')
# Sau: redirect('stadium_dashboard')  # ← Về dashboard để thấy job status
```

### 3. **Enhanced Success Message**
```python
messages.success(request, f"Đã chấp nhận đơn ứng tuyển của {applicant}. Tin tuyển dụng '{job.title}' đã được đóng.")
```

---

## 🧪 Test Steps

### Step 1: Accept Application
```bash
# 1. Vào application detail
http://localhost:8000/users/stadium/application/6/

# 2. Click "Chấp nhận Ứng tuyển"
# 3. Confirm dialog
# ✅ Application status → APPROVED
# ✅ Job status → CLOSED (trong database)
```

### Step 2: Check Dashboard
```bash
# 1. Redirect về stadium dashboard
http://localhost:8000/users/stadium/dashboard/

# 2. Kiểm tra job status trong table
# ✅ "Đang mở" → "Đã đóng" (badge color change)
```

### Step 3: Verify Database
```python
# In Django shell:
from organizations.models import JobPosting
job = JobPosting.objects.get(pk=6)
print(f"Job status: {job.status}")
print(f"Status display: {job.get_status_display()}")
```

---

## 🔍 Debug Checklist

### ✅ Model Check:
- [x] JobPosting có field `status`
- [x] Status choices: OPEN, CLOSED
- [x] Default: OPEN

### ✅ Logic Check:
- [x] Accept application → set status APPROVED
- [x] Accept application → set job status CLOSED
- [x] Save both objects

### ✅ Template Check:
- [x] Dashboard template check `job.status == 'OPEN'`
- [x] Display "Đang mở" vs "Đã đóng"
- [x] Badge colors: Success (green) vs Secondary (gray)

### ✅ Redirect Check:
- [x] Redirect về dashboard sau accept
- [x] User thấy updated job status

---

## 🎯 Expected Behavior

### Before Accept:
```
Job Status: OPEN
Display: "Đang mở" (🟢 Green badge)
Applications: Can apply
```

### After Accept:
```
Job Status: CLOSED  
Display: "Đã đóng" (⚫ Gray badge)
Applications: Cannot apply (job closed)
```

---

## 🚨 Troubleshooting

### If Status Still Shows "Đang mở":

1. **Check Database:**
```python
from organizations.models import JobPosting
job = JobPosting.objects.get(pk=YOUR_JOB_ID)
print(f"Status in DB: {job.status}")
```

2. **Clear Browser Cache:**
- Hard refresh: Ctrl+F5
- Clear cache trong browser

3. **Check Template Logic:**
```django
<!-- Debug in template -->
<p>Debug: job.status = {{ job.status }}</p>
{% if job.status == 'OPEN' %}
    <span class="badge bg-success">Đang mở</span>
{% else %}
    <span class="badge bg-secondary">Đã đóng</span>
{% endif %}
```

4. **Check Application Status:**
```python
from organizations.models import JobApplication
app = JobApplication.objects.get(pk=YOUR_APP_ID)
print(f"Application status: {app.status}")
```

---

## 📊 Status Flow

```
Application: PENDING → APPROVED
     ↓
Job: OPEN → CLOSED (auto)
     ↓
UI: "Đang mở" → "Đã đóng"
```

---

**Test ngay và cho mình biết kết quả nhé!** 🔍
