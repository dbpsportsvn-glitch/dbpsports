# backend/organizations/apps.py

from django.apps import AppConfig

class OrganizationsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'organizations'

    # THÊM HÀM NÀY VÀO ĐỂ KÍCH HOẠT SIGNALS
    def ready(self):
        import organizations.signals