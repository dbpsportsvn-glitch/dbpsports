# Các Mẫu Hệ Thống

- **Kiến trúc:** Monolithic App - Backend và Frontend được xây dựng chung trong một project Django.
- **Cấu trúc project:** Theo mô hình "Django apps", mỗi ứng dụng (tournaments, users, shop,...) đảm nhiệm một chức năng riêng biệt và có models, views, templates riêng.
- **Luồng dữ liệu:**
  - Người dùng tương tác qua giao diện (templates).
  - Yêu cầu được gửi đến `views.py` của ứng dụng tương ứng.
  - `views.py` xử lý logic, tương tác với `models.py` để truy vấn/thay đổi dữ liệu trong database.
  - Dữ liệu được trả về cho templates để hiển thị.
- **Phân quyền:** Hệ thống sử dụng các "vai trò" (Roles) trong model `User` để phân quyền truy cập và chức năng cho các loại người dùng khác nhau (ví dụ: chỉ có `Organization Manager` mới được tạo giải đấu).