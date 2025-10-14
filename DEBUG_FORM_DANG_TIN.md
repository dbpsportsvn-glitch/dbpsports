# Debug Form Đăng Tin Tìm Việc

## 🔧 Vấn đề hiện tại
Form đăng tin tìm việc vẫn bị reload liên tục khi submit.

## ✅ Những gì đã sửa

### 1. Tạo form riêng cho chuyên gia
- **File:** `backend/users/forms.py`
- **Form mới:** `ProfessionalJobSeekingForm`
- **Khác biệt:** Phù hợp với việc chuyên gia tìm việc thay vì tuyển dụng

### 2. Cập nhật views
- **File:** `backend/users/views.py`
- **Views cập nhật:**
  - `create_professional_job_posting`
  - `edit_professional_job_posting`

### 3. Thêm debug logging
- Thêm print statements để xem lỗi form
- Thêm error messages cho user

### 4. Cải thiện form logic
- Tự động chọn vai trò nếu user chỉ có 1 vai trò
- Validation cho field `role_required`
- Xử lý trường hợp user không có vai trò chuyên gia

## 🧪 Cách test và debug

### Bước 1: Kiểm tra server logs
1. Mở terminal
2. Chạy: `cd D:\dbpsports\backend && python manage.py runserver`
3. Để terminal mở để xem logs

### Bước 2: Test form
1. Vào hồ sơ công khai → tab "Chuyên môn"
2. Click "Đăng tin" → "Đăng tin tìm việc"
3. Điền form và submit
4. Xem terminal logs để thấy:
   - Form errors (nếu có)
   - Form data được gửi

### Bước 3: Kiểm tra vai trò user
```python
# Trong Django shell
python manage.py shell

from django.contrib.auth.models import User
user = User.objects.get(username='your_username')
print("User roles:", list(user.profile.roles.values_list('id', flat=True)))
```

## 🔍 Các lỗi có thể xảy ra

### 1. Lỗi vai trò không hợp lệ
**Triệu chứng:** Form reload với lỗi validation
**Nguyên nhân:** User không có vai trò chuyên gia
**Giải pháp:** Thêm vai trò COACH, COMMENTATOR, MEDIA, PHOTOGRAPHER, hoặc REFEREE

### 2. Lỗi field required
**Triệu chứng:** Form reload với lỗi "Vui lòng chọn vai trò tìm việc"
**Nguyên nhân:** Field `role_required` không được set
**Giải pháp:** Đã thêm auto-select nếu user chỉ có 1 vai trò

### 3. Lỗi database constraint
**Triệu chứng:** Form reload với lỗi database
**Nguyên nhân:** Model validation failed
**Giải pháp:** Kiểm tra JobPosting model constraints

## 📋 Checklist debug

- [ ] Server đang chạy
- [ ] User có vai trò chuyên gia (COACH, COMMENTATOR, MEDIA, PHOTOGRAPHER, REFEREE)
- [ ] Form fields được điền đầy đủ
- [ ] Xem terminal logs khi submit form
- [ ] Kiểm tra database có JobPosting được tạo không

## 🚀 Test case

### User có vai trò MEDIA:
1. Login với user có role MEDIA
2. Vào form đăng tin tìm việc
3. Điền:
   - Tiêu đề: "Tìm việc Media"
   - Vai trò: MEDIA (tự động chọn)
   - Địa điểm: "Hà Nội"
   - Mô tả: "Có kinh nghiệm quay phim"
4. Submit form
5. Kỳ vọng: Redirect về professional dashboard với thông báo thành công

## 🔧 Nếu vẫn lỗi

### Xem logs chi tiết:
```bash
# Trong terminal đang chạy server
# Khi submit form, sẽ thấy:
Form errors: {...}
Form data: {...}
```

### Kiểm tra database:
```python
python manage.py shell

from organizations.models import JobPosting
print("Total job postings:", JobPosting.objects.count())
print("Professional job postings:", JobPosting.objects.filter(posted_by='PROFESSIONAL').count())
```

## 📞 Báo cáo lỗi

Nếu vẫn lỗi, hãy cung cấp:
1. Screenshot form khi submit
2. Terminal logs khi submit
3. User roles của account test
4. Error message cụ thể (nếu có)
