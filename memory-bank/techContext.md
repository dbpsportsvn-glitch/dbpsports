# Bối Cảnh Công Nghệ

- **Backend:**
  - **Framework:** Django 4.2.13 (Python)
  - **Database:** 
    - Development: SQLite
    - Production: MySQL (hỗ trợ qua mysqlclient)
  - **Authentication:** 
    - django-allauth 0.58.2 (đăng ký, đăng nhập)
    - Social login: Google OAuth2, Facebook OAuth2
    - Email-based authentication (không dùng username)
  - **Admin Interface:** django-admin-interface 0.30.1 (tùy chỉnh giao diện admin)
  - **Forms:** django-crispy-forms + crispy-bootstrap5
  - **Image Processing:** Pillow (tự động resize/optimize ảnh)
  - **Static Files:** WhiteNoise (phục vụ static files trên production)
  - **Caching:** Django LocMem Cache (timeout 200s)
  - **Email:** SMTP support với django-environ config
  - **Other libs:** django-colorfield, beautifulsoup4, requests, django-environ

- **Frontend:**
  - **Templates:** Django Template Language
  - **CSS Framework:** Bootstrap 5
  - **Icons:** Bootstrap Icons
  - **JavaScript:** Vanilla JS cho tương tác (AJAX, fetch API)
  - **Features:** 
    - Responsive design
    - Real-time notifications
    - Share API integration
    - Clipboard API

- **Deployment & Infrastructure:**
  - **WSGI Server:** Gunicorn
  - **Static Files:** WhiteNoise với CompressedManifestStaticFilesStorage
  - **Media Files:** Django FileSystemStorage
  - **Environment Variables:** django-environ (.env file)
  - **Timezone:** Asia/Ho_Chi_Minh (USE_TZ=False)
  - **Language:** Tiếng Việt (vi)

- **Môi trường phát triển:**
  - Python 3.9+
  - Cài đặt dependencies: `pip install -r backend/requirements.txt`
  - Chạy migrations: `python backend/manage.py migrate`
  - Chạy server: `python backend/manage.py runserver`
  - Collect static files: `python backend/manage.py collectstatic`