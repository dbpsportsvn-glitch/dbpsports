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
    'admin_interface',
    'colorfield',
    "organizations",
    "users",
    "tournaments",

    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sites",  # bắt buộc cho allauth
    "django.contrib.humanize",

    "crispy_forms",
    "crispy_bootstrap5",

    "allauth",
    "allauth.account",
    "allauth.socialaccount",
    "allauth.socialaccount.providers.google",  # dùng Google
    'allauth.socialaccount.providers.facebook',
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
                "tournaments.context_processors.unread_announcements_count",
                "tournaments.context_processors.unread_notifications_count",
                "users.context_processors.user_roles_context",
            ],
        },
    },
]

WSGI_APPLICATION = "dbpsports_core.wsgi.application"

# === Database ===
DATABASES = {
    'default': env.db('DATABASE_URL', default='sqlite:///db.sqlite3')
}

# === Cache ===
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "unique-snowflake",
        "TIMEOUT": 200,  # Thời gian cache (giây), 200s = 3.3 phút
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
USE_TZ = False

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

# === Email ===
# Nếu DEBUG=False (trên host), sử dụng SMTP. Ngược lại (ở máy), dùng console.
EMAIL_BACKEND = env('EMAIL_BACKEND', default='django.core.mail.backends.console.EmailBackend')

ADMIN_EMAIL = env("ADMIN_EMAIL", default="admin@example.com") # Đọc email admin từ file .env
EMAIL_HOST = env("EMAIL_HOST", default="")
EMAIL_PORT = env.int("EMAIL_PORT", default=587)
EMAIL_HOST_USER = env("EMAIL_HOST_USER", default="")
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD", default="")
EMAIL_USE_TLS = env.bool("EMAIL_USE_TLS", default=True)
EMAIL_USE_SSL = env.bool("EMAIL_USE_SSL", default=False) # Thêm dòng này
DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL", default="DBP Sports <no-reply@example.com>")

# === Sites ===
# Đọc SITE_ID từ file .env, nếu không có thì mặc định là 1 (cho local)
SITE_ID = env.int("SITE_ID", default=1)

# === Auth / allauth ===
AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
    "allauth.account.auth_backends.AuthenticationBackend",
]

ACCOUNT_ADAPTER = 'users.adapters.CustomAccountAdapter'
# URL chuyển hướng
LOGIN_URL = "account_login" # Sử dụng URL chuẩn của allauth
LOGIN_REDIRECT_URL = "/"
ACCOUNT_LOGOUT_REDIRECT_URL = "/"
ACCOUNT_LOGOUT_ON_GET = True
ACCOUNT_SESSION_REMEMBER = None
SOCIALACCOUNT_LOGIN_ON_GET = True

ACCOUNT_FORMS = {'signup': 'users.forms.CustomSignupForm'}
# Cấu hình allauth để sử dụng email làm username
ACCOUNT_AUTHENTICATION_METHOD = "email" # Đăng nhập bằng email
ACCOUNT_EMAIL_REQUIRED = True           # Bắt buộc phải có email
ACCOUNT_USERNAME_REQUIRED = False       # Không yêu cầu username
ACCOUNT_USER_MODEL_USERNAME_FIELD = None # Không dùng trường username
ACCOUNT_EMAIL_VERIFICATION = "mandatory" # BẮT BUỘC xác thực email
SOCIALACCOUNT_AUTO_SIGNUP = True
ACCOUNT_SIGNUP_PASSWORD_ENTER_TWICE = True # Bắt buộc nhập mật khẩu 2 lần
ACCOUNT_LOGIN_ON_EMAIL_CONFIRMATION = True

# yêu cầu quyền truy cập email
SOCIALACCOUNT_PROVIDERS = {
    'google': {
        'SCOPE': [
            'profile',
            'email',
        ],
        'AUTH_PARAMS': {
            'access_type': 'online',
            'prompt': 'select_account', # <-- Add this line
        }
    }
}

SOCIALACCOUNT_ADAPTER = 'users.adapters.CustomSocialAccountAdapter'

SOCIALACCOUNT_PROVIDERS = {
    'google': {
        # ... (cấu hình google)
    },
    'facebook': {
        'METHOD': 'oauth2',
        'SCOPE': ['email', 'public_profile'],
        'FIELDS': [
            'id', 'email', 'name', 'first_name', 'last_name',
        ],
        # ... (các cài đặt khác)
        'APP': {
            'client_id': env('FACEBOOK_APP_ID'),      # <-- Đọc ID từ .env
            'secret': env('FACEBOOK_SECRET_KEY'), # <-- Đọc Khóa bí mật từ .env
            'key': ''
        }
    }
}
