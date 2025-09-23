# backend/tournaments/signals.py
from django.core.cache import cache
from django.db.models.signals import post_save, post_delete, pre_delete
from django.dispatch import receiver
# === THAY ĐỔI DÒNG NÀY: THÊM MATCH VÀ GROUP VÀO IMPORT ===
from .models import HomeBanner, Tournament, Group, Match

# === THAY ĐỔI DÒNG NÀY: THÊM MATCH VÀ GROUP VÀO DANH SÁCH THEO DÕI ===
@receiver([post_save, post_delete], sender=[HomeBanner, Tournament, Match, Group])
def clear_cache_on_data_change(sender, instance, **kwargs):
    """
    Tự động xóa toàn bộ cache mỗi khi có thay đổi trong các model quan trọng.
    """
    cache.clear()
    # Thay đổi câu lệnh print để rõ ràng hơn
    print(f"Cache đã được xóa do có thay đổi trong model: {sender.__name__}")

@receiver(pre_delete, sender=Group)
def delete_matches_on_group_delete(sender, instance, **kwargs):
    """
    Tự động xóa các trận đấu VÒNG BẢNG khi một bảng đấu bị xóa.
    """
    group = instance
    teams_in_group = list(group.teams.all().values_list('id', flat=True))

    if teams_in_group:
        matches_to_delete = Match.objects.filter(
            team1_id__in=teams_in_group,
            team2_id__in=teams_in_group,
            match_round='GROUP'
        )
        
        print(f"Sắp xóa {matches_to_delete.count()} trận đấu thuộc về Bảng {group.name}.")
        
        matches_to_delete.delete()