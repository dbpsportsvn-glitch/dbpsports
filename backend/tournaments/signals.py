# backend/tournaments/signals.py
from django.core.cache import cache
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import HomeBanner, Tournament # Thêm Tournament vào đây

# Thêm Tournament vào danh sách theo dõi
@receiver([post_save, post_delete], sender=[HomeBanner, Tournament])
def clear_home_page_cache(sender, instance, **kwargs):
    """
    Tự động xóa cache của trang chủ mỗi khi có thay đổi trong HomeBanner hoặc Tournament.
    """
    cache.clear()
    print("Cache đã được xóa do có thay đổi banner hoặc giải đấu.")