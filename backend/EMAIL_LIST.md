# Danh sách Email Templates DBP Sports

## Tổng quan
Đã thiết kế lại toàn bộ **18 email templates** với giao diện thống nhất và responsive.

## Danh sách đầy đủ các file HTML đã tạo:

### 1. Shop Emails (3 templates)
- `shop_customer_email.html` - Xác nhận đơn hàng cho khách hàng
- `admin_order_notification.html` - Thông báo đơn hàng mới cho admin  
- `payment_confirmed.html` - Cảm ơn khách hàng sau khi thanh toán

### 2. Tournament Emails (8 templates)
- `tournament_announcement_email.html` - Thông báo từ Ban Tổ chức
- `payment_confirmed_email.html` - Xác nhận thanh toán thành công
- `new_payment_proof.html` - Thông báo thanh toán mới cho admin
- `payment_pending_confirmation_email.html` - Xác nhận đã nhận hóa đơn thanh toán
- `payment_rejected_email.html` - Thông báo thanh toán bị từ chối
- `new_team_registration_email.html` - Thông báo đội mới đăng ký cho admin
- `new_team_joined_email.html` - Thông báo đội mới tham gia cho followers

### 3. Organization Emails (7 templates)
- `new_organization_notification.html` - Thông báo đơn vị mới đăng ký
- `new_job_application.html` - Thông báo đơn ứng tuyển mới
- `organization_approved_email.html` - Thông báo đơn vị được duyệt
- `job_status_update_email.html` - Cập nhật trạng thái ứng tuyển
- `transfer_invitation_email.html` - Lời mời chuyển nhượng mới
- `transfer_accepted_email.html` - Chuyển nhượng được chấp nhận
- `transfer_rejected_email.html` - Chuyển nhượng bị từ chối

### 4. Account Emails (2 templates)
- `account_registration_email.html` - Xác nhận đăng ký tài khoản (HTML)
- `email_confirmed.html` - Xác nhận email thành công

## Quy trình Email theo từng tính năng:

### Quy trình Thanh toán:
1. Đội trưởng tải hóa đơn → `payment_pending_confirmation_email.html`
2. Admin nhận thông báo → `new_payment_proof.html`
3. Admin duyệt → `payment_confirmed_email.html`
4. Admin từ chối → `payment_rejected_email.html`

### Quy trình Chuyển nhượng:
1. Đội A mời cầu thủ → `transfer_invitation_email.html`
2. Đội B chấp nhận → `transfer_accepted_email.html`
3. Đội B từ chối → `transfer_rejected_email.html`

### Quy trình Công việc:
1. Người dùng ứng tuyển → `new_job_application.html`
2. BTC cập nhật trạng thái → `job_status_update_email.html`

### Quy trình Đăng ký:
1. Người dùng đăng ký → `account_registration_email.html`
2. Xác nhận email → `email_confirmed.html`
3. Đội đăng ký giải → `new_team_registration_email.html`
4. Đội được duyệt → `new_team_joined_email.html`

## Cách xem các email:
Mở các file HTML bằng trình duyệt để xem giao diện và nội dung của từng email template.

## Thống kê:
- **Tổng số email templates:** 18
- **Số file HTML đã tạo:** 14 (một số email dùng chung template)
- **Giao diện:** Responsive, thống nhất với base template
- **Tương thích:** Tất cả email clients phổ biến
