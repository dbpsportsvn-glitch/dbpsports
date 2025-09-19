# backend/tournaments/apps.py
from django.apps import AppConfig

class TournamentsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'tournaments'

    def ready(self):
        # Import signals để chúng được đăng ký khi ứng dụng khởi động
        import tournaments.signals