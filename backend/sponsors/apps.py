# backend/sponsors/apps.py

from django.apps import AppConfig

class SponsorsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'sponsors'

    def ready(self):
        # Dòng này sẽ import file signals của chúng ta khi app sẵn sàng
        import sponsors.signals