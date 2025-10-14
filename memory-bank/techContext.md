# Bối Cảnh Công Nghệ

- **Backend:**
  - **Framework:** Django (Python)
  - **Database:** SQLite (dùng cho phát triển, có thể thay đổi sau này)
  - **Quản lý Users:** Sử dụng `django-allauth` để xử lý đăng ký, đăng nhập, và xác thực mạng xã hội.
  - **Thư viện phụ thuộc chính:** Xem chi tiết trong file `backend/requirements.txt`.

- **Frontend:**
  - **Templates:** Sử dụng hệ thống template của Django.
  - **Styling:** CSS thuần, có thể có sự hỗ trợ của các framework như Bootstrap (cần kiểm tra thêm trong file `base.html`).
  - **JavaScript:** Sử dụng JavaScript cơ bản để tăng tính tương tác.

- **Môi trường phát triển:**
  - Cần cài đặt Python và các thư viện trong `requirements.txt`.
  - Chạy server bằng lệnh: `python backend/manage.py runserver`.