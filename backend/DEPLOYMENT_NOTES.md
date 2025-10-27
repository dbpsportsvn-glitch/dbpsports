# Deployment Notes - Fix 403 Forbidden Error

## Vấn đề
Site trả về 403 Forbidden khi truy cập https://dbpsports.com/

## Nguyên nhân
1. `Deny from all` trong `.htaccess` đang chặn tất cả requests
2. Cấu hình Passenger không đúng với CloudLinux Passenger setup
3. Paths không khớp với cấu trúc thực tế trên server

## Giải pháp đã áp dụng

### 1. Cập nhật `.htaccess` với đúng cấu hình CloudLinux:
```apache
# CloudLinux Passenger Configuration
PassengerAppRoot "/home/dbpsport/dbpsports"
PassengerBaseURI "/"
PassengerPython "/home/dbpsport/virtualenv/dbpsports/3.9/bin/python"

# Serve static và media files
RewriteRule ^static/(.*)$ /home/dbpsport/public_html/staticfiles/$1 [L]
RewriteRule ^media/(.*)$ /home/dbpsport/public_html/media/$1 [L]
```

### 2. Thêm favicon handler vào `urls.py`:
- Thêm route `favicon.ico` để serve favicon đúng cách
- Thêm view `favicon()` để serve logo.png như favicon

### 3. Cấu hình serve media files trong production:
- Thêm route để serve media files khi `DEBUG=False`
- Sử dụng Django `serve()` view

## Lỗi Browser Extensions
Các lỗi từ extensions (`inpage.js`, `metadata.js`, `content.js`) KHÔNG phải lỗi của site:
- Regex error trong extension có thể bỏ qua
- Khuyến khích user tạm disable extensions khi test

## File cần upload lên server
1. ✅ `backend/.htaccess` - CloudLinux Passenger config
2. ✅ `backend/dbpsports_core/urls.py` - Updated với favicon handler
3. ✅ `backend/passenger_wsgi.py` - WSGI entry point (không đổi)

## Lệnh chạy trên server sau khi upload

```bash
# 1. Chạy migrations (nếu có thay đổi)
python manage.py migrate

# 2. Collect static files
python manage.py collectstatic --noinput

# 3. Chmod cho .htaccess
chmod 644 .htaccess
chmod 644 passenger_wsgi.py

# 4. Touch để restart Passenger
touch passenger_wsgi.py
```

## Kiểm tra sau khi deploy

```bash
# Test homepage
curl -I https://dbpsports.com/

# Test favicon
curl -I https://dbpsports.com/favicon.ico

# Test static files
curl -I https://dbpsports.com/static/images/logo.png
```

## Ghi chú CloudLinux
- Passenger config TỰ ĐỘNG được thêm bởi CloudLinux
- KHÔNG sửa các dòng có comment "DO NOT REMOVE"
- Paths phải khớp với:
  - `PassengerAppRoot`: root folder của app
  - Python path: virtualenv path
  - Static files: trong `staticfiles/` folder

