# backend/tournaments/signals.py

from django.core.cache import cache
from django.db.models.signals import post_save, post_delete, pre_delete
from django.dispatch import receiver
from django.urls import reverse
from .models import HomeBanner, Tournament, Group, Match, Team, Notification, TeamAchievement
from .utils import send_schedule_notification

@receiver([post_save, post_delete], sender=[HomeBanner, Tournament, Match, Group])
def clear_cache_on_data_change(sender, instance, **kwargs):
    cache.clear()
    print(f"Cache đã được xóa do có thay đổi trong model: {sender.__name__}")

@receiver(pre_delete, sender=Group)
def delete_all_tournament_matches_on_group_delete(sender, instance, **kwargs):
    group = instance
    tournament = group.tournament
    matches_to_delete = Match.objects.filter(tournament=tournament)
    if matches_to_delete.exists():
        print(f"Xóa bảng {group.name}. Sắp xóa {matches_to_delete.count()} trận đấu của giải {tournament.name}.")
        matches_to_delete.delete()

# === BẮT ĐẦU KHỐI CODE ĐÃ CẬP NHẬT HOÀN CHỈNH ===

@receiver(post_save, sender=Match)
def create_match_result_notification(sender, instance, created, **kwargs):
    """
    Tự động tạo thông báo khi một trận đấu được cập nhật tỉ số,
    CHỈ gửi cho những người dùng đã bật cài đặt này.
    """
    if not created and instance.team1_score is not None and instance.team2_score is not None:
        match = instance
        tournament = match.tournament
        
        # Lấy ID của những người dùng muốn nhận thông báo này (tối ưu hóa truy vấn)
        user_ids_to_notify = set()

        # 1. Lọc những người theo dõi muốn nhận thông báo
        follower_ids = tournament.followers.filter(profile__notify_match_results=True).values_list('id', flat=True)
        user_ids_to_notify.update(follower_ids)

        # 2. Lọc đội trưởng và cầu thủ của 2 đội tham gia
        for team in [match.team1, match.team2]:
            # Kiểm tra đội trưởng
            if hasattr(team.captain, 'profile') and team.captain.profile.notify_match_results:
                user_ids_to_notify.add(team.captain.id)
            
            # Lấy cầu thủ
            player_ids = team.players.filter(
                user__isnull=False, 
                user__profile__notify_match_results=True
            ).values_list('user_id', flat=True)
            user_ids_to_notify.update(player_ids)

        title = "Kết quả trận đấu được cập nhật"
        message = (
            f"Trận đấu giữa {match.team1.name} và {match.team2.name} "
            f"đã kết thúc với tỉ số {match.team1_score} - {match.team2_score}."
        )
        url = reverse('match_detail', kwargs={'pk': match.pk})

        # Tạo thông báo hàng loạt (bulk_create) để tăng hiệu suất
        notifications_to_create = [
            Notification(
                user_id=user_id,
                title=title,
                message=message,
                notification_type=Notification.NotificationType.MATCH_RESULT,
                related_url=url
            )
            for user_id in user_ids_to_notify
        ]
        
        if notifications_to_create:
            Notification.objects.bulk_create(notifications_to_create)

@receiver(post_save, sender=Team)
def create_new_team_notification(sender, instance, created, **kwargs):
    """
    Tự động tạo thông báo khi có đội mới được duyệt,
    CHỈ gửi cho những người dùng đã bật cài đặt này.
    """
    if created and instance.payment_status == 'PAID':
        team = instance
        tournament = team.tournament
        
        # Lọc những người theo dõi muốn nhận thông báo về đội mới
        users_to_notify = tournament.followers.filter(profile__notify_new_teams=True)
        
        if not users_to_notify.exists():
            return # Dừng lại nếu không có ai để thông báo

        title = "Đội mới tham gia giải đấu"
        message = f"Giải đấu '{tournament.name}' có thêm một đội mới tham gia: {team.name}."
        url = reverse('team_detail', kwargs={'pk': team.pk})
        
        notifications_to_create = [
            Notification(
                user=user,
                title=title,
                message=message,
                notification_type=Notification.NotificationType.NEW_TEAM,
                related_url=url
            )
            for user in users_to_notify
        ]

        if notifications_to_create:
            Notification.objects.bulk_create(notifications_to_create)

# === KẾT THÚC KHỐI CODE ĐÃ CẬP NHẬT ===

@receiver(post_save, sender=Match)
def create_schedule_notification_on_match_creation(sender, instance, created, **kwargs):
    """
    Gửi thông báo khi có trận đấu mới được tạo.
    """
    if created:
        tournament = instance.tournament
        # Kiểm tra xem giải đấu đã có trận đấu nào trước đó chưa
        # để tránh gửi thông báo cho mỗi trận đấu được tạo riêng lẻ
        if tournament.matches.count() == 1:
            send_schedule_notification(
                tournament,
                Notification.NotificationType.SCHEDULE_CREATED,
                f"Giải đấu '{tournament.name}' đã có lịch thi đấu",
                "Lịch thi đấu mới đã được tạo. Hãy vào xem chi tiết.",
                'tournament_detail'
            )

# === Tự động lưu thành tích ===
@receiver(post_save, sender=Match)
def award_achievements_on_final_match_save(sender, instance, created, **kwargs):
    """
    Tự động trao danh hiệu khi một trận Chung kết hoặc Tranh Hạng Ba có kết quả.
    """
    match = instance

    # Chỉ hoạt động khi trận đấu có kết quả và có người thắng/thua
    if match.winner and match.loser:
        tournament = match.tournament

        # Trường hợp 1: Trận Chung kết
        if match.match_round == 'FINAL':
            # Dùng update_or_create để tránh tạo trùng lặp nếu admin có chỉnh sửa lại tỉ số
            TeamAchievement.objects.update_or_create(
                team=match.winner, tournament=tournament, achievement_type='CHAMPION',
                defaults={'description': f'Vô địch giải {tournament.name} {tournament.start_date.year}'}
            )
            TeamAchievement.objects.update_or_create(
                team=match.loser, tournament=tournament, achievement_type='RUNNER_UP',
                defaults={'description': f'Á quân giải {tournament.name} {tournament.start_date.year}'}
            )
            print(f"Đã tự động trao giải Vô địch và Á quân cho giải {tournament.name}.")

        # Trường hợp 2: Trận Tranh Hạng Ba
        elif match.match_round == 'THIRD_PLACE':
            TeamAchievement.objects.update_or_create(
                team=match.winner, tournament=tournament, achievement_type='THIRD_PLACE',
                defaults={'description': f'Hạng ba giải {tournament.name} {tournament.start_date.year}'}
            )
            print(f"Đã tự động trao giải Hạng ba cho giải {tournament.name}.")            