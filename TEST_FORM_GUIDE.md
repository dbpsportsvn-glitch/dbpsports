# Hướng dẫn Test Form Đăng Tin

## 🔧 Vấn đề hiện tại
Form báo lỗi: `__all__: Phải chọn Giải đấu nếu đăng bởi BTC`

## ✅ Những gì đã sửa
1. **Thêm debug logging** trong model `clean()` method
2. **Set `posted_by = PROFESSIONAL`** trong form validation
3. **Thêm debug logging** trong view

## 🧪 Test ngay

### Bước 1: Đảm bảo có user test
```bash
cd D:\dbpsports\backend
python manage.py shell
```

Trong Django shell:
```python
from django.contrib.auth.models import User
from users.models import Profile, Role

# Tạo user nếu chưa có
try:
    user = User.objects.get(username='testuser')
    print("User đã tồn tại")
except User.DoesNotExist:
    user = User.objects.create_user(
        username='testuser',
        email='test@example.com', 
        password='test123'
    )
    print("Đã tạo user mới")

# Kiểm tra profile và roles
profile = user.profile
print(f"Profile: {profile}")
print(f"Roles: {list(profile.roles.values_list('id', flat=True))}")

# Thêm role MEDIA nếu chưa có
if not profile.roles.filter(id='MEDIA').exists():
    media_role = Role.objects.get(id='MEDIA')
    profile.roles.add(media_role)
    print("Đã thêm role MEDIA")
else:
    print("Đã có role MEDIA")

exit()
```

### Bước 2: Test form
1. **Khởi động server:**
   ```bash
   cd D:\dbpsports\backend
   python manage.py runserver
   ```

2. **Login:** `testuser` / `test123`

3. **Vào form đăng tin:**
   - Hồ sơ công khai → tab "Chuyên môn"
   - Click "Đăng tin" → "Đăng tin tìm việc"

4. **Điền form:**
   - Tiêu đề: "Test job"
   - Vai trò: MEDIA (tự động chọn)
   - Địa điểm: "Hà Nội"
   - Mô tả: "Test description"

5. **Submit form**

### Bước 3: Xem logs
Trong terminal sẽ hiển thị:
```
Posted by: PROFESSIONAL
Professional user: testuser
Tournament: None
Stadium: None
Role required: Media
Model clean() - posted_by: PROFESSIONAL
Model clean() - tournament: None
Model clean() - stadium: None
Model clean() - professional_user: testuser
```

## 🔍 Kỳ vọng
- **Thành công:** Redirect về professional dashboard với thông báo "Đã đăng tin tìm việc thành công!"
- **Thất bại:** Sẽ thấy lỗi cụ thể trong logs

## 📞 Báo cáo kết quả
Nếu vẫn lỗi, hãy copy paste:
1. **Terminal logs** khi submit form
2. **Error message** hiển thị trên web
3. **Form data** được submit (từ logs)
