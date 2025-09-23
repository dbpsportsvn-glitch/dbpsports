# backend/tournaments/signals.py
from django.core.cache import cache
from django.db.models.signals import post_save, post_delete, pre_delete
from django.dispatch import receiver
from .models import HomeBanner, Tournament, Group, Match

@receiver([post_save, post_delete], sender=[HomeBanner, Tournament, Match, Group])
def clear_cache_on_data_change(sender, instance, **kwargs):
    """
    Tự động xóa toàn bộ cache mỗi khi có thay đổi trong các model quan trọng.
    """
    cache.clear()
    print(f"Cache đã được xóa do có thay đổi trong model: {sender.__name__}")

# === BẮT ĐẦU SỬA ĐỔI TẠI ĐÂY ===
@receiver(pre_delete, sender=Group)
def delete_all_tournament_matches_on_group_delete(sender, instance, **kwargs):
    """
    Tự động xóa TẤT CẢ các trận đấu (vòng bảng và knockout) của giải đấu
    khi một bảng đấu bất kỳ bị xóa.
    """
    group = instance
    tournament = group.tournament

    # Tìm tất cả các trận đấu thuộc về toàn bộ giải đấu này
    matches_to_delete = Match.objects.filter(tournament=tournament)
    
    if matches_to_delete.exists():
        print(f"Xóa bảng {group.name}. Sắp xóa {matches_to_delete.count()} trận đấu của giải {tournament.name}.")
        # Xóa tất cả các trận đấu tìm được
        matches_to_delete.delete()
# === KẾT THÚC SỬA ĐỔI ===