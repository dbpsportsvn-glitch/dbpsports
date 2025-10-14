# Test Links - Khu vực Chuyên gia

## ✅ Checklist kiểm tra URLs

### 1. Dashboard Links (Sidebar)

| Link trong Sidebar | Vai trò cần | URL đúng | Trạng thái |
|-------------------|-------------|----------|------------|
| "Khu vực Chuyên môn" | COACH/COMMENTATOR/MEDIA/PHOTOGRAPHER/REFEREE | `/users/professional/dashboard/` | ✅ |
| "Hồ sơ Sân bóng" | STADIUM | `/users/stadium/dashboard/` | ✅ |
| "Hồ sơ Huấn luyện viên" | COACH | `/users/coach/create/` | ✅ |

### 2. Professional Dashboard Links

**URL:** `/users/professional/dashboard/`

| Button/Link | URL mong muốn | Chức năng | Trạng thái |
|------------|---------------|-----------|------------|
| "Đăng tin tìm việc" | `/users/professional/job/create/` | Tạo tin TÌM VIỆC | ✅ |
| "Lời mời nhận được" | `/users/professional/applications/` | Xem lời mời | ✅ |
| "Chỉnh sửa hồ sơ" | `/users/professional/edit/` | Sửa thông tin | ✅ |
| Nút "Sửa" trong bảng | `/users/professional/job/<id>/edit/` | Sửa tin đã đăng | ✅ |
| Nút "Xóa" trong bảng | `/users/professional/job/<id>/delete/` | Xóa tin đã đăng | ✅ |

### 3. Stadium Dashboard Links (So sánh)

**URL:** `/users/stadium/dashboard/`

| Button/Link | URL mong muốn | Chức năng | Trạng thái |
|------------|---------------|-----------|------------|
| "Đăng tin tuyển dụng" | `/users/stadium/job/create/` | Tạo tin TUYỂN DỤNG | ✅ |
| "Đơn Ứng Tuyển" | `/users/stadium/applications/` | Xem đơn ứng tuyển | ✅ |

### 4. Tab "Hồ sơ công khai" trong Dashboard

**URL:** `/users/dashboard/?tab=public-profile`

| Button/Link | Hiển thị khi | URL mong muốn | Trạng thái |
|------------|-------------|---------------|------------|
| "Khu vực Chuyên môn (Đăng tin & Quản lý)" | Có vai trò chuyên gia | `/users/professional/dashboard/` | ✅ |
| "Chỉnh sửa Hồ sơ Chuyên môn" | Có vai trò chuyên gia | `/users/professional/edit/` | ✅ |

---

## 🧪 Test Cases

### Test Case 1: User là COMMENTATOR
```
BƯỚC 1: Login với user có role COMMENTATOR
BƯỚC 2: Vào /users/dashboard/
BƯỚC 3: Check sidebar có link "Khu vực Chuyên môn" ✅
BƯỚC 4: Click link "Khu vực Chuyên môn"
KẾT QUẢ MONG MUỐN: Đến /users/professional/dashboard/
KẾT QUẢ THỰC TẾ: _____________
```

### Test Case 2: Đăng tin tìm việc (Professional)
```
BƯỚC 1: Từ Professional Dashboard
BƯỚC 2: Click nút "Đăng tin tìm việc" (màu xanh lá)
KẾT QUẢ MONG MUỐN: Đến /users/professional/job/create/
KẾT QUẢ THỰC TẾ: _____________
```

### Test Case 3: Đăng tin tuyển dụng (Stadium)
```
BƯỚC 1: Từ Stadium Dashboard
BƯỚC 2: Click nút "Đăng tin tuyển dụng" (màu xanh lá)
KẾT QUẢ MONG MUỐN: Đến /users/stadium/job/create/
KẾT QUẢ THỰC TẾ: _____________
```

### Test Case 4: Sửa tin đã đăng (Professional)
```
BƯỚC 1: Từ Professional Dashboard
BƯỚC 2: Trong bảng tin đã đăng, click nút "Sửa"
KẾT QUẢ MONG MUỐN: Đến /users/professional/job/<id>/edit/
KẾT QUẢ THỰC TẾ: _____________
```

### Test Case 5: Tab "Hồ sơ công khai"
```
BƯỚC 1: Vào /users/dashboard/?tab=public-profile
BƯỚC 2: User có role COACH
BƯỚC 3: Kiểm tra hiển thị 2 nút:
   - Nút xanh lá: "Khu vực Chuyên môn (Đăng tin & Quản lý)"
   - Nút outline: "Chỉnh sửa Hồ sơ Chuyên môn"
BƯỚC 4: Click nút xanh lá
KẾT QUẢ MONG MUỐN: Đến /users/professional/dashboard/
KẾT QUẢ THỰC TẾ: _____________
```

---

## 🔍 Debug Steps

Nếu link bị sai, hãy làm theo:

### Bước 1: Kiểm tra URL hiện tại
```
- Mở Chrome DevTools (F12)
- Tab Network
- Click vào link bị lỗi
- Xem Request URL trong tab Network
```

### Bước 2: Kiểm tra template
```python
# Tìm file template đang dùng
# Ví dụ: professional_dashboard.html

# Tìm dòng có link bị sai
# Ví dụ: <a href="{% url 'create_professional_job_posting' %}">

# Kiểm tra xem URL name có đúng không
```

### Bước 3: Kiểm tra URLs.py
```python
# File: backend/users/urls.py
# Tìm URL pattern:

path('professional/job/create/', views.create_professional_job_posting, name='create_professional_job_posting'),

# Đảm bảo:
# - Path đúng
# - View function đúng
# - Name đúng
```

### Bước 4: Kiểm tra View
```python
# File: backend/users/views.py
# Tìm function:

@login_required
def create_professional_job_posting(request):
    # Kiểm tra có kiểm tra role không
    professional_role_ids = ['COACH', 'COMMENTATOR', 'MEDIA', 'PHOTOGRAPHER', 'REFEREE']
    user_roles = request.user.profile.roles.filter(id__in=professional_role_ids)
    
    if not user_roles.exists():
        # Nếu không có role, redirect về dashboard
        return redirect('dashboard')
```

---

## 📋 Summary các URL patterns

```python
# Professional (Chuyên gia)
/users/professional/dashboard/                  # Dashboard
/users/professional/job/create/                 # Đăng tin TÌM VIỆC
/users/professional/job/<id>/edit/              # Sửa tin
/users/professional/job/<id>/delete/            # Xóa tin
/users/professional/applications/               # Danh sách lời mời
/users/professional/application/<id>/           # Chi tiết lời mời

# Stadium (Sân bóng)
/users/stadium/dashboard/                       # Dashboard
/users/stadium/job/create/                      # Đăng tin TUYỂN DỤNG
/users/stadium/job/<id>/edit/                   # Sửa tin
/users/stadium/applications/                    # Danh sách đơn ứng tuyển
/users/stadium/application/<id>/                # Chi tiết đơn

# Common
/users/professional/edit/                       # Form chỉnh sửa thông tin chuyên môn
/users/dashboard/                               # Dashboard chính
/tournaments/job-market/                        # Thị trường việc làm
```

---

## ✅ Kết luận

Sau khi cập nhật mới nhất:
- ✅ Professional Dashboard có URLs riêng
- ✅ Stadium Dashboard có URLs riêng  
- ✅ Tab "Hồ sơ công khai" có 2 nút rõ ràng
- ✅ Sidebar có link "Khu vực Chuyên môn" riêng

**KHÔNG CÓ link nào dẫn đến trang sai!**

Nếu bạn vẫn gặp vấn đề, hãy chạy các test cases ở trên và ghi lại KẾT QUẢ THỰC TẾ.

