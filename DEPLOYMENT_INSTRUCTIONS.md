# Hướng dẫn sửa lỗi 403 Forbidden - CloudLinux Passenger

## Vấn đề
Site trả về 403 Forbidden với thông báo "Could not write .htaccess: Inappropriate ioctl for device"

## Giải pháp

### Cách 1: Sửa trực tiếp trên Server (Khuyến nghị)

Đăng nhập vào cPanel hoặc SSH vào server:

```bash
# SSH vào server
ssh dbpsport@dbpsports.com

# Vào thư mục public_html
cd ~/public_html

# Kiểm tra file .htaccess hiện tại
cat .htaccess

# Backup file cũ
cp .htaccess .htaccess.backup

# Sửa file .htaccess
nano .htaccess
```

### Nội dung file `.htaccess` cần có:

```apache
# CloudLinux Passenger Configuration - TỰ ĐỘNG thêm bởi CloudLinux
# KHÔNG xóa các dòng này
PassengerAppRoot "/home/dbpsport/dbpsports"
PassengerBaseURI "/"
PassengerPython "/home/dbpsport/virtualenv/dbpsports/3.9/bin/python"

# Remove "Deny from all" nếu có
# Xóa dòng này: Deny from all

# Enable Rewrite Engine
<IfModule mod_rewrite.c>
    RewriteEngine On
    
    # Serve static files directly
    RewriteRule ^static/(.*)$ /home/dbpsport/public_html/staticfiles/$1 [L]
    
    # Serve media files directly
    RewriteRule ^media/(.*)$ /home/dbpsport/public_html/media/$1 [L]
    
    # Pass all other requests to Passenger
    RewriteCond %{REQUEST_FILENAME} !-f
    RewriteCond %{REQUEST_FILENAME} !-d
    RewriteRule ^(.*)$ index.php/$1 [L]
</IfModule>
```

### Cách 2: Sửa qua cPanel File Manager

1. Đăng nhập vào cPanel
2. Mở **File Manager**
3. Vào thư mục `public_html`
4. Tìm file `.htaccess`
5. Click **Edit** (biểu tượng bút chì)
6. Xóa dòng `Deny from all` nếu có
7. Thêm Rewrite rules (như nội dung trên)
8. Click **Save Changes**

### Sau khi sửa, chạy lệnh:

```bash
cd /home/dbpsport/dbpsports/backend

# Restart Passenger
touch passenger_wsgi.py

# Kiểm tra logs
tail -f ../logs/error_log
```

## Kiểm tra

```bash
# Test homepage
curl -I https://dbpsports.com/

# Nếu vẫn 403, check permissions
ls -la ~/public_html/.htaccess

# Phải có quyền 644
chmod 644 ~/public_html/.htaccess
```

## Lưu ý quan trọng

1. CloudLinux tự động thêm Passenger config vào `.htaccess`
2. KHÔNG sửa các dòng có comment "DO NOT REMOVE"
3. Xóa dòng `Deny from all` nếu có
4. Đảm bảo paths đúng:
   - `/home/dbpsport/dbpsports` - root folder app
   - `/home/dbpsport/public_html/staticfiles/` - static files
   - `/home/dbpsport/public_html/media/` - media files

## Troubleshooting

Nếu vẫn lỗi 403:

```bash
# Check error logs
tail -100 /home/dbpsport/logs/error_log

# Check Passenger logs
tail -100 /home/dbpsport/logs/passenger.log

# Check permissions
ls -la /home/dbpsport/dbpsports/
ls -la /home/dbpsport/public_html/

# Test static files
curl https://dbpsports.com/static/images/logo.png
```

