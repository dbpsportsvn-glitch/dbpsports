"""
Django settings for dbpsports_core project.
"""

from pathlib import Path
import os
import environ

# === Paths & Env ===
BASE_DIR = Path(__file__).resolve().parent.parent
env = environ.Env()
environ.Env.read_env(BASE_DIR / ".env")

# === Core ===
SECRET_KEY = env("SECRET_KEY", default="dev-secret")
DEBUG = env.bool("DEBUG", default=False)
ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=["127.0.0.1", "localhost"])
CSRF_TRUSTED_ORIGINS = env.list("CSRF_TRUSTED_ORIGINS", default=[])

# === Apps ===
INSTALLED_APPS = [
    "jazzmin",
    "users",
    "tournaments",

    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sites",  # bắt buộc cho allauth

    "crispy_forms",
    "crispy_bootstrap5",

    "allauth",
    "allauth.account",
    "allauth.socialaccount",
    "allauth.socialaccount.providers.google",  # dùng Google
]

# === Middleware ===
MIDDLEWARE = [
    'django.middleware.cache.UpdateCacheMiddleware',
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "allauth.account.middleware.AccountMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    'django.middleware.cache.FetchFromCacheMiddleware',
]

ROOT_URLCONF = "dbpsports_core.urls"

# === Templates ===
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",  # bắt buộc cho allauth
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "dbpsports_core.wsgi.application"

# === Database ===
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

# === Cache ===
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "unique-snowflake",
        "TIMEOUT": 300,  # Thời gian cache (giây), 300s = 5 phút
    }
}

# === Auth validators ===
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# === i18n ===
LANGUAGE_CODE = "vi"
TIME_ZONE = "Asia/Ho_Chi_Minh"
USE_I18N = True
USE_TZ = True

# Cấu hình tùy chỉnh để Whitenoise bỏ qua các file sourcemap bị thiếu
from whitenoise.storage import CompressedManifestStaticFilesStorage

class WhiteNoiseStaticFilesStorage(CompressedManifestStaticFilesStorage):
    manifest_strict = False

# === Static / Media ===
STATIC_URL = '/static/'          # ← có dấu "/" ở đầu và cuối
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "dbpsports_core.settings.WhiteNoiseStaticFilesStorage"},
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# === Crispy ===
CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"

# === Jazzmin ===
JAZZMIN_SETTINGS = {
    "site_title": "DBP Sports Admin",
    "site_header": "DBP Sports",
    "site_brand": "DBP Sports",
    "welcome_sign": "Chào mừng bạn đến với trang quản trị DBP Sports",
    "copyright": "DBP Sports Ltd.",
    "order_with_respect_to": [
        "tournaments",
        "tournaments.Tournament",
        "tournaments.Team",
        "tournaments.Player",
        "tournaments.Match",
        "users",
    ],
    "icons": {
        "auth": "fas fa-users-cog",
        "users.user": "fas fa-user",
        "tournaments.Tournament": "fas fa-trophy",
        "tournaments.Team": "fas fa-users",
        "tournaments.Player": "fas fa-user-shield",
        "tournaments.Match": "fas fa-futbol",
    },
    "topmenu_links": [
        {"name": "Trang chủ", "url": "admin:index"},
        {"name": "Xem trang web", "url": "/", "new_window": True},
    ],
    "language_chooser": False,
}
JAZZMIN_UI_TWEAKS = {
    "navbar_small_text": False,
    "footer_small_text": False,
    "body_small_text": False,
    "brand_small_text": False,
    "brand_colour": "navbar-dark",
    "accent": "accent-primary",
    "navbar": "navbar-dark",
    "no_navbar_border": False,
    "sidebar": "sidebar-dark-primary",
    "sidebar_nav_small_text": False,
    "sidebar_disable_expand": False,
    "sidebar_nav_child_indent": False,
    "sidebar_nav_compact_style": False,
    "sidebar_nav_legacy_style": False,
    "sidebar_nav_flat_style": False,
}

# === Email ===
# Nếu DEBUG=False (trên host), sử dụng SMTP. Ngược lại (ở máy), dùng console.
EMAIL_BACKEND = env('EMAIL_BACKEND', default='django.core.mail.backends.console.EmailBackend')

ADMIN_EMAIL = "admin@dbpsports.com" # Email của bạn để nhận thông báo
EMAIL_HOST = env("EMAIL_HOST", default="")
EMAIL_PORT = env.int("EMAIL_PORT", default=587)
EMAIL_HOST_USER = env("EMAIL_HOST_USER", default="")
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD", default="")
EMAIL_USE_TLS = env.bool("EMAIL_USE_TLS", default=True)
EMAIL_USE_SSL = env.bool("EMAIL_USE_SSL", default=False) # Thêm dòng này
DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL", default="DBP Sports <no-reply@example.com>")

# === Sites ===
SITE_ID = 2  # chỉnh theo Admin > Sites cho đúng host

# backend/dbpsports_core/settings.py

# === Auth / allauth ===
AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
    "allauth.account.auth_backends.AuthenticationBackend",
]

# URL chuyển hướng
LOGIN_URL = "account_login" # Sử dụng URL chuẩn của allauth
LOGIN_REDIRECT_URL = "/"
ACCOUNT_LOGOUT_REDIRECT_URL = "/"

# Cấu hình allauth để sử dụng email làm username
ACCOUNT_AUTHENTICATION_METHOD = "email" # Đăng nhập bằng email
ACCOUNT_EMAIL_REQUIRED = True           # Bắt buộc phải có email
ACCOUNT_USERNAME_REQUIRED = False       # Không yêu cầu username
ACCOUNT_USER_MODEL_USERNAME_FIELD = None # Không dùng trường username
ACCOUNT_EMAIL_VERIFICATION = "none"     # Tạm thời không cần xác thực email
SOCIALACCOUNT_AUTO_SIGNUP = True
ACCOUNT_SIGNUP_PASSWORD_ENTER_TWICE = True # Bắt buộc nhập mật khẩu 2 lần

# yêu cầu quyền truy cập email
SOCIALACCOUNT_PROVIDERS = {
    'google': {
        'SCOPE': [
            'profile',
            'email',
        ],
        'AUTH_PARAMS': {
            'access_type': 'online',
        }
    }
}

SOCIALACCOUNT_ADAPTER = 'users.adapters.CustomSocialAccountAdapter'
