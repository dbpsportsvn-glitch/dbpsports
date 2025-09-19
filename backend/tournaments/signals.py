# backend/tournaments/signals.py
from django.core.cache import cache
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import HomeBanner

@receiver([post_save, post_delete], sender=HomeBanner)
def clear_home_page_cache(sender, instance, **kwargs):
    """
    Tự động xóa cache của trang chủ mỗi khi có thay đổi trong HomeBanner.
    """
    # Django cache middleware tạo một key phức tạp, cách đơn giản nhất
    # là xóa toàn bộ cache. Đối với trang ít thay đổi, việc này chấp nhận được.
    cache.clear()
    print("Cache của trang chủ đã được xóa do có thay đổi banner.")