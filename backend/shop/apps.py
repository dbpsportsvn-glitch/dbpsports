from django.apps import AppConfig


class ShopConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'shop'
    verbose_name = 'Cửa hàng'
    
    def ready(self):
        """Import signals khi app ready"""
        import shop.signals