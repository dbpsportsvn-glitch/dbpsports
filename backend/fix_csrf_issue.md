# Giải pháp cho lỗi CSRF 403

## Nguyên nhân có thể:
1. **Session timeout** - User đã đăng nhập lâu, session hết hạn
2. **Cookie bị xóa** - Browser xóa cookie CSRF
3. **Multiple tabs** - Đăng nhập ở tab khác làm rotate CSRF token
4. **JavaScript interference** - Code JS can thiệp vào form submit

## Giải pháp cho User:

### Bước 1: Refresh trang
- **F5** hoặc **Ctrl+F5** để reload trang
- Đảm bảo đăng nhập lại nếu cần

### Bước 2: Clear browser data
- **Ctrl+Shift+Delete**
- Clear cookies và cache
- Đăng nhập lại

### Bước 3: Thử browser khác
- Chrome, Firefox, Edge
- Đảm bảo cookies được enable

### Bước 4: Kiểm tra network
- Mở Developer Tools (F12)
- Tab Network để xem request
- Kiểm tra có CSRF token trong POST data không

## Giải pháp Technical:

### 1. Thêm CSRF exemption cho debug
```python
from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
@login_required  
def debug_shop_settings(request, org_slug):
    # Debug view without CSRF
```

### 2. Kiểm tra middleware
```python
# settings.py
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',  # Đảm bảo có
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    # ...
]
```

### 3. Debug CSRF token
```python
# Trong view
print(f"CSRF token: {request.META.get('CSRF_COOKIE')}")
print(f"Session key: {request.session.session_key}")
```

## Test URLs:
- `/shop/org/<org_slug>/test-csrf/` - Test CSRF functionality
- `/shop/org/<org_slug>/manage/settings/` - Shop settings với debug
