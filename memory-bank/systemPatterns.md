# Các Mẫu Hệ Thống

- **Kiến trúc:** Monolithic App - Backend và Frontend được xây dựng chung trong một project Django.

- **Cấu trúc project:** Theo mô hình "Django apps", mỗi ứng dụng (tournaments, users, shop,...) đảm nhiệm một chức năng riêng biệt và có models, views, templates riêng.

- **Luồng dữ liệu:**
  - Người dùng tương tác qua giao diện (Django templates).
  - Yêu cầu được gửi đến `views.py` của ứng dụng tương ứng.
  - `views.py` xử lý logic, tương tác với `models.py` để truy vấn/thay đổi dữ liệu trong database.
  - Dữ liệu được trả về cho templates để hiển thị.
  - AJAX/Fetch API cho các tương tác real-time.

- **Phân quyền & Authentication:**
  - Hệ thống sử dụng model `Role` để định nghĩa các vai trò.
  - Model `Profile` có ManyToMany relationship với `Role`.
  - Context processor `user_roles_context` inject thông tin vai trò vào mọi template.
  - Decorator và kiểm tra điều kiện trong views dựa trên `user.profile.roles`.
  - Custom adapters cho allauth: `CustomAccountAdapter`, `CustomSocialAccountAdapter`.

- **Database Patterns:**
  - **Through Models:** Sử dụng intermediate models cho complex M2M relationships
    - `TeamRegistration`: liên kết Team ↔ Tournament với thông tin thêm (group, payment status)
  - **Soft References:** ForeignKey với `null=True, blank=True` cho optional relationships
  - **Choices Classes:** Sử dụng `TextChoices` cho enum values (Status, Format, Region...)
  - **Related Names:** Đặt tên rõ ràng cho reverse relationships (`related_name`)

- **Signals Pattern:**
  - Auto-create Profile khi User được tạo (post_save signal)
  - Auto-create Organization khi user có role ORGANIZER
  - Các signals khác trong `signals.py` của từng app

- **Image Processing:**
  - Override `save()` method để resize/optimize images
  - Sử dụng Pillow để xử lý ảnh
  - Upload paths động: `upload_to='folder/'`
  - Lazy loading cho performance

- **Caching Strategy:**
  - Django LocMem Cache (timeout: 200s)
  - Cache middleware: UpdateCacheMiddleware → FetchFromCacheMiddleware
  - Custom middleware `DisableCacheMiddleware` cho shop API
  - View-level caching với decorators (`@cache_page`, `@never_cache`)

- **Form Handling:**
  - Crispy Forms với Bootstrap 5
  - Model Forms cho CRUD operations
  - Custom validation trong `clean()` methods
  - Form wizards cho multi-step forms

- **URL Structure:**
  - App-level URLconf trong `urls.py` của từng app
  - Include vào main `urls.py` với namespace
  - Named URLs cho reverse lookups
  - RESTful patterns: `/resource/<pk>/action/`

- **Template Patterns:**
  - Base template inheritance (`base.html`)
  - App-specific templates trong `app/templates/app/`
  - Custom template tags và filters trong `templatetags/`
  - Context processors cho global data

- **Notification System:**
  - Model `Notification` cho user-specific notifications
  - Model `Announcement` cho tournament-wide announcements
  - Email notifications với `send_notification_email()` utility
  - Real-time count trong navbar via context processor

- **Business Logic Location:**
  - Complex queries → Model Managers
  - Data manipulation → Model methods
  - Request handling → Views
  - Reusable logic → Utility functions (`utils.py`)
  - Validation → Model `clean()` và Form validation