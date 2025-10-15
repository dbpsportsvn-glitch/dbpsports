# Email Templates - DBP Sports

## Tổng quan

Đã thiết kế lại toàn bộ email templates của dự án theo mẫu thống nhất với giao diện đẹp mắt và responsive.

## Các email templates đã được thiết kế lại

### 1. Shop Emails
- `shop/emails/customer_order_confirmation.html` - Xác nhận đơn hàng cho khách hàng
- `shop/emails/admin_order_notification.html` - Thông báo đơn hàng mới cho admin
- `shop/emails/payment_confirmed.html` - Cảm ơn khách hàng sau khi thanh toán

### 2. Tournament Emails
- `tournaments/emails/announcement_notification.html` - Thông báo từ Ban Tổ chức
- `tournaments/emails/payment_confirmed.html` - Xác nhận thanh toán thành công
- `tournaments/emails/new_payment_proof.html` - Thông báo thanh toán mới cho admin
- `tournaments/emails/payment_pending_confirmation.html` - Xác nhận đã nhận thanh toán
- `tournaments/emails/payment_rejected.html` - Thông báo thanh toán bị từ chối
- `tournaments/emails/new_team_registration.html` - Thông báo đội mới đăng ký cho admin
- `tournaments/emails/new_team_joined.html` - Thông báo đội mới tham gia cho followers

### 3. Organization Emails
- `organizations/emails/new_organization_notification.html` - Thông báo đơn vị mới đăng ký
- `organizations/emails/new_job_application.html` - Thông báo đơn ứng tuyển mới
- `organizations/emails/organization_approved.html` - Thông báo đơn vị được duyệt
- `organizations/emails/application_status_update.html` - Cập nhật trạng thái ứng tuyển
- `organizations/emails/new_transfer_invitation.html` - Lời mời chuyển nhượng mới
- `organizations/emails/transfer_accepted_notification.html` - Chuyển nhượng được chấp nhận
- `organizations/emails/transfer_rejected_notification.html` - Chuyển nhượng bị từ chối

### 4. Account Emails
- `account/email/email_confirmation_message.html` - Xác nhận đăng ký tài khoản (HTML)
- `account/email/email_confirmed.html` - Xác nhận email thành công

## Base Template

Tất cả email templates đều extend từ `templates/emails/base_email.html` với:
- Gradient header màu tím (#667eea → #764ba2)
- Responsive design
- CSS inline tương thích với email clients
- Typography và spacing đồng nhất

## Test Email Templates

### 1. Tạo file HTML để xem trước
```bash
cd backend
python test_email_html.py
```

Sẽ tạo ra 13 file HTML:
- `shop_customer_email.html`
- `tournament_announcement_email.html`
- `payment_confirmed_email.html`
- `organization_approved_email.html`
- `account_registration_email.html`
- `email_confirmed.html`
- `new_team_registration_email.html`
- `new_team_joined_email.html`
- `payment_rejected_email.html`
- `transfer_invitation_email.html`
- `transfer_accepted_email.html`
- `transfer_rejected_email.html`
- `job_status_update_email.html`

### 2. Gửi email thật (cần cấu hình SMTP)

#### Bước 1: Tạo file .env
Tạo file `.env` trong thư mục `backend` với nội dung:
```
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=127.0.0.1,localhost

# Email Configuration (SMTP)
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
EMAIL_USE_TLS=True
EMAIL_USE_SSL=False
DEFAULT_FROM_EMAIL=DBP Sports <your-email@gmail.com>

ADMIN_EMAIL=admin@dbpsports.com
```

#### Bước 2: Cấu hình Gmail App Password
1. Vào Google Account Settings
2. Security > 2-Step Verification > App passwords
3. Tạo password mới cho "Mail"
4. Thay `your-app-password` bằng password này

#### Bước 3: Gửi email test
```bash
cd backend
python send_email_real.py
```

### 3. Sử dụng Django Management Command
```bash
cd backend
python manage.py test_email_templates --email thienhamedia2024@gmail.com
```

## Đặc điểm thiết kế

### Giao diện thống nhất
- Header gradient tím với logo DBP Sports
- Layout responsive cho mobile và desktop
- Info boxes với border-left màu tím
- Status badges với màu sắc theo trạng thái
- Alert boxes (warning/success) với màu phù hợp

### Cải thiện UX
- Thông tin được tổ chức rõ ràng theo từng section
- Call-to-action buttons với gradient và hover effects
- Emoji icons để dễ nhận biết nội dung
- Typography và spacing đồng nhất

### Tính năng kỹ thuật
- Template inheritance từ base template
- CSS inline để tương thích với email clients
- Responsive design cho mobile
- Tương thích với các trình duyệt phổ biến

## Files đã tạo

1. `templates/emails/base_email.html` - Base template chung
2. `test_email_html.py` - Script tạo file HTML để xem trước
3. `send_email_real.py` - Script gửi email thật
4. `smtp_config_example.txt` - Hướng dẫn cấu hình SMTP
5. `shop/management/commands/test_email_templates.py` - Django management command

## Kết quả

✅ Đã thiết kế lại toàn bộ 18 email templates
✅ Tạo base template thống nhất
✅ Responsive design cho mobile và desktop
✅ CSS inline tương thích email clients
✅ Test scripts để kiểm tra templates
✅ Hướng dẫn cấu hình SMTP

### Danh sách đầy đủ email templates:

**Shop (3 templates):**
- Xác nhận đơn hàng cho khách hàng
- Thông báo đơn hàng mới cho admin
- Cảm ơn khách hàng sau khi thanh toán

**Tournament (7 templates):**
- Thông báo từ Ban Tổ chức
- Xác nhận thanh toán thành công
- Thông báo thanh toán mới cho admin
- Xác nhận đã nhận thanh toán
- Thông báo thanh toán bị từ chối
- Thông báo đội mới đăng ký cho admin
- Thông báo đội mới tham gia cho followers

**Organization (7 templates):**
- Thông báo đơn vị mới đăng ký
- Thông báo đơn ứng tuyển mới
- Thông báo đơn vị được duyệt
- Cập nhật trạng thái ứng tuyển
- Lời mời chuyển nhượng mới
- Chuyển nhượng được chấp nhận
- Chuyển nhượng bị từ chối

**Account (2 templates):**
- Xác nhận đăng ký tài khoản (HTML)
- Xác nhận email thành công

Tất cả email templates đã được đồng bộ theo mẫu của shop với giao diện thống nhất và UX tốt hơn.
