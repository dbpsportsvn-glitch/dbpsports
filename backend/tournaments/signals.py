# backend/tournaments/signals.py

from django.core.cache import cache
from django.db.models.signals import post_save, post_delete, pre_delete
from django.dispatch import receiver
from django.urls import reverse
from django.db.models import F
from .models import HomeBanner, Tournament, Group, Match, Team, Notification, TeamAchievement, Player
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
    # === THAY ĐỔI BẮT ĐẦU TẠI ĐÂY ===
    # Chỉ thực hiện khi đội được tạo, đã "thanh toán" VÀ có liên kết với một giải đấu
    if created and instance.payment_status == 'PAID' and instance.tournament:
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
    # === KẾT THÚC THAY ĐỔI ===

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

# === Tự động lưu thành tích và trao thưởng ===
@receiver(post_save, sender=Match)
def award_achievements_on_final_match_save(sender, instance, created, **kwargs):
    """
    Tự động trao danh hiệu, cộng phiếu bầu VÀ GỬI THÔNG BÁO
    khi một trận Chung kết hoặc Tranh Hạng Ba có kết quả.
    """
    match = instance

    # Chỉ hoạt động khi trận đấu có kết quả và có người thắng/thua
    if not match.winner or not match.loser:
        return

    tournament = match.tournament

    # Hàm nội bộ để cộng phiếu và gửi thông báo, tránh lặp code
    def process_award(team, votes_to_add, rank_name, achievement_type):
        if not team or votes_to_add <= 0:
            return
            
        # 1. Gán danh hiệu cho đội
        TeamAchievement.objects.update_or_create(
            team=team, tournament=tournament, achievement_type=achievement_type,
            defaults={'description': f'{rank_name} giải {tournament.name} {tournament.start_date.year}'}
        )

        # 2. Lấy danh sách cầu thủ có tài khoản để gửi thông báo
        players_with_users = Player.objects.filter(team=team, user__isnull=False)
        user_ids = list(players_with_users.values_list('user_id', flat=True))

        # 3. Cộng phiếu cho tất cả cầu thủ trong đội
        updated_count = Player.objects.filter(team=team).update(votes=F('votes') + votes_to_add)
        print(f"Đã cộng {votes_to_add} phiếu cho {updated_count} thành viên của đội {team.name}.")

        # 4. Chỉ tạo thông báo nếu có người dùng để gửi
        if user_ids:
            # Tạo một dict để lấy pk của cầu thủ tương ứng với user_id
            player_pk_map = {p.user_id: p.pk for p in players_with_users}

            notifications = [
                Notification(
                    user_id=user_id,
                    title=f"Bạn được thưởng {votes_to_add} phiếu bầu!",
                    message=f"Chúc mừng bạn và đội {team.name} đã đạt thành tích {rank_name} tại giải {tournament.name}. Bạn được hệ thống tặng thưởng {votes_to_add} phiếu.",
                    notification_type=Notification.NotificationType.VOTE_AWARDED,
                    related_url=reverse('player_detail', kwargs={'pk': player_pk_map.get(user_id)})
                )
                for user_id in user_ids if player_pk_map.get(user_id)
            ]
            Notification.objects.bulk_create(notifications)
            print(f"Đã tạo {len(notifications)} thông báo thưởng phiếu cho đội {team.name}.")

    # Xử lý các trận đấu
    if match.match_round == 'FINAL':
        process_award(match.winner, 3, "Vô địch", "CHAMPION")
        process_award(match.loser, 2, "Á quân", "RUNNER_UP")
        print(f"Đã tự động trao giải Vô địch, Á quân và cộng phiếu cho giải {tournament.name}.")

    elif match.match_round == 'THIRD_PLACE':
        process_award(match.winner, 1, "Hạng ba", "THIRD_PLACE")
        # Không có danh hiệu "Hạng tư", chỉ cộng phiếu
        process_award(match.loser, 1, "Hạng tư", "OTHER") 
        print(f"Đã tự động trao giải Hạng ba, Hạng tư và cộng phiếu cho giải {tournament.name}.")            