# backend/tournaments/signals.py

from django.core.cache import cache
from django.db.models.signals import post_save, post_delete, pre_delete
from django.dispatch import receiver
from django.urls import reverse
from .models import HomeBanner, Tournament, Group, Match, Team, Notification

@receiver([post_save, post_delete], sender=[HomeBanner, Tournament, Match, Group])
def clear_cache_on_data_change(sender, instance, **kwargs):
    cache.clear()
    print(f"Cache đã được xóa do có thay đổi trong model: {sender.__name__}")

@receiver(pre_delete, sender=Group)
def delete_all_tournament_matches_on_group_delete(sender, instance, **kwargs):
    # ... (Hàm này giữ nguyên không đổi)
    group = instance
    tournament = group.tournament
    matches_to_delete = Match.objects.filter(tournament=tournament)
    if matches_to_delete.exists():
        print(f"Xóa bảng {group.name}. Sắp xóa {matches_to_delete.count()} trận đấu của giải {tournament.name}.")
        matches_to_delete.delete()

# === BẮT ĐẦU THÊM CÁC HÀM MỚI ===

@receiver(post_save, sender=Match)
def create_match_result_notification(sender, instance, created, **kwargs):
    """
    Tự động tạo thông báo khi một trận đấu được cập nhật tỉ số.
    """
    # Chỉ hoạt động khi tỉ số được cập nhật (không phải lúc mới tạo)
    if not created and instance.team1_score is not None and instance.team2_score is not None:
        match = instance
        tournament = match.tournament
        
        # Lấy tất cả người dùng liên quan: đội trưởng, cầu thủ, và người theo dõi
        users_to_notify = set()
        
        # 1. Người theo dõi giải đấu
        for user in tournament.followers.all():
            users_to_notify.add(user)
            
        # 2. Đội trưởng và cầu thủ của 2 đội tham gia
        for team in [match.team1, match.team2]:
            users_to_notify.add(team.captain)
            for player in team.players.filter(user__isnull=False):
                users_to_notify.add(player.user)

        title = "Kết quả trận đấu được cập nhật"
        message = (
            f"Trận đấu giữa {match.team1.name} và {match.team2.name} "
            f"đã kết thúc với tỉ số {match.team1_score} - {match.team2_score}."
        )
        url = reverse('match_detail', kwargs={'pk': match.pk})

        # Tạo thông báo cho từng người dùng
        for user in users_to_notify:
            Notification.objects.create(
                user=user,
                title=title,
                message=message,
                notification_type=Notification.NotificationType.MATCH_RESULT,
                related_url=url
            )

@receiver(post_save, sender=Team)
def create_new_team_notification(sender, instance, created, **kwargs):
    """
    Tự động tạo thông báo khi có một đội mới đăng ký và được duyệt.
    """
    # Chỉ hoạt động khi một đội mới được tạo VÀ đã thanh toán
    if created and instance.payment_status == 'PAID':
        team = instance
        tournament = team.tournament
        
        # Lấy tất cả người theo dõi giải đấu
        users_to_notify = set(tournament.followers.all())
        
        title = "Đội mới tham gia giải đấu"
        message = f"Giải đấu '{tournament.name}' có thêm một đội mới tham gia: {team.name}."
        url = reverse('team_detail', kwargs={'pk': team.pk})
        
        for user in users_to_notify:
            Notification.objects.create(
                user=user,
                title=title,
                message=message,
                notification_type=Notification.NotificationType.NEW_TEAM,
                related_url=url
            )
# === KẾT THÚC THÊM CÁC HÀM MỚI ===