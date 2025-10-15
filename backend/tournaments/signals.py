# backend/tournaments/signals.py

from django.core.cache import cache
from django.db.models.signals import post_save, post_delete, pre_delete
from django.dispatch import receiver
from django.urls import reverse
from django.db.models import F
from .models import HomeBanner, Tournament, Group, Match, Team, Notification, TeamAchievement, Player, TeamRegistration
from .utils import send_schedule_notification
from organizations.models import JobPosting
from .models import Sponsorship

@receiver([post_save, post_delete], sender=[HomeBanner, Tournament, Match, Group, JobPosting, TeamRegistration])
def clear_cache_on_data_change(sender, instance, **kwargs):
    cache.clear()

@receiver(pre_delete, sender=Group)
def delete_all_tournament_matches_on_group_delete(sender, instance, **kwargs):
    group = instance
    tournament = group.tournament
    matches_to_delete = Match.objects.filter(tournament=tournament)
    if matches_to_delete.exists():
        print(f"Deleting group {group.name}. About to delete {matches_to_delete.count()} matches from tournament {tournament.name}.")
        matches_to_delete.delete()

@receiver(post_save, sender=Match)
def create_match_result_notification(sender, instance, created, **kwargs):
    """
    Tự động tạo thông báo khi một trận đấu được cập nhật tỉ số,
    CHỈ gửi cho những người dùng đã bật cài đặt này.
    """
    if not created and instance.team1_score is not None and instance.team2_score is not None:
        match = instance
        tournament = match.tournament
        
        user_ids_to_notify = set()

        follower_ids = tournament.followers.filter(profile__notify_match_results=True).values_list('id', flat=True)
        user_ids_to_notify.update(follower_ids)

        for team in [match.team1, match.team2]:
            if hasattr(team.captain, 'profile') and team.captain.profile.notify_match_results:
                user_ids_to_notify.add(team.captain.id)
            
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

@receiver(post_save, sender=TeamRegistration)
def create_new_team_notification(sender, instance, created, **kwargs):
    """
    Tự động tạo thông báo khi có đội mới được duyệt (thanh toán thành công),
    CHỈ gửi cho những người dùng đã bật cài đặt này.
    """
    is_newly_paid = created and instance.payment_status == 'PAID'
    
    # Kiểm tra xem trạng thái có được cập nhật từ chưa thanh toán -> đã thanh toán không
    if not is_newly_paid and not created:
        try:
            old_instance = sender.objects.get(pk=instance.pk)
            if old_instance.payment_status != 'PAID' and instance.payment_status == 'PAID':
                is_newly_paid = True
        except sender.DoesNotExist:
            pass
            
    if is_newly_paid:
        registration = instance
        team = registration.team
        tournament = registration.tournament
        
        users_to_notify = tournament.followers.filter(profile__notify_new_teams=True)
        
        if not users_to_notify.exists():
            return

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

@receiver(post_save, sender=Match)
def create_schedule_notification_on_match_creation(sender, instance, created, **kwargs):
    """
    Gửi thông báo khi có trận đấu mới được tạo.
    """
    if created:
        tournament = instance.tournament
        if tournament.matches.count() == 1:
            send_schedule_notification(
                tournament,
                Notification.NotificationType.SCHEDULE_CREATED,
                f"Giải đấu '{tournament.name}' đã có lịch thi đấu",
                "Lịch thi đấu mới đã được tạo. Hãy vào xem chi tiết.",
                'tournament_detail'
            )

@receiver(post_save, sender=Match)
def award_achievements_on_final_match_save(sender, instance, created, **kwargs):
    """
    Tự động trao danh hiệu, cộng phiếu bầu VÀ GỬI THÔNG BÁO
    khi một trận Chung kết hoặc Tranh Hạng Ba có kết quả.
    """
    match = instance

    if not match.winner or not match.loser:
        return

    tournament = match.tournament

    def process_award(team, votes_to_add, rank_name, achievement_type):
        if not team or votes_to_add <= 0:
            return
            
        TeamAchievement.objects.update_or_create(
            team=team, tournament=tournament, achievement_type=achievement_type,
            defaults={'description': f'{rank_name} giải {tournament.name} {tournament.start_date.year}'}
        )

        players_with_users = Player.objects.filter(team=team, user__isnull=False)
        user_ids = list(players_with_users.values_list('user_id', flat=True))

        updated_count = Player.objects.filter(team=team).update(votes=F('votes') + votes_to_add)
        print(f"Added {votes_to_add} votes to {updated_count} members of team {team.name}.")

        if user_ids:
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
            print(f"Created {len(notifications)} vote reward notifications for team {team.name}.")

    if match.match_round == 'FINAL':
        process_award(match.winner, 3, "Vô địch", "CHAMPION")
        process_award(match.loser, 2, "Á quân", "RUNNER_UP")
        print(f"Automatically awarded Championship, Runner-up and votes for tournament {tournament.name}.")

    elif match.match_round == 'THIRD_PLACE':
        process_award(match.winner, 1, "Hạng ba", "THIRD_PLACE")
        process_award(match.loser, 1, "Hạng tư", "OTHER") 
        print(f"Automatically awarded Third place, Fourth place and votes for tournament {tournament.name}.")


# Tự động tạo hoặc cập nhật checklist quyền lợi khi một Sponsorship được lưu
@receiver(post_save, sender=Sponsorship)
def create_or_update_sponsorship_checklist(sender, instance, **kwargs):
    """
    Tự động tạo hoặc cập nhật checklist quyền lợi khi một Sponsorship được lưu.
    Phiên bản này đã sửa lỗi logic nhân đôi và xóa nhầm.
    """
    sponsorship = instance
    package = sponsorship.package

    # Ngắt kết nối tạm thời signal để tránh vòng lặp vô tận khi gọi .save()
    post_save.disconnect(create_or_update_sponsorship_checklist, sender=Sponsorship)

    try:
        # Nếu không có gói hoặc gói không có quyền lợi, hãy xóa checklist cũ
        if not package or not package.benefits:
            if sponsorship.benefits_checklist: # Chỉ lưu khi có sự thay đổi
                sponsorship.benefits_checklist = []
                sponsorship.save(update_fields=['benefits_checklist'])
            return

        # Tách các quyền lợi mới từ package (loại bỏ dòng trống)
        new_benefits_list = [benefit.strip() for benefit in package.benefits.splitlines() if benefit.strip()]

        # Lấy checklist hiện tại để so sánh
        current_checklist = sponsorship.benefits_checklist or []
        
        # Tạo một dictionary từ checklist cũ để dễ dàng tra cứu trạng thái "checked"
        current_checked_status = {item['text']: item['checked'] for item in current_checklist}

        # Dựng lại checklist mới hoàn toàn
        # Giữ lại trạng thái 'checked' của các quyền lợi đã có
        final_checklist = []
        for benefit_text in new_benefits_list:
            final_checklist.append({
                'text': benefit_text,
                'checked': current_checked_status.get(benefit_text, False) # Lấy trạng thái cũ, mặc định là False
            })

        # Chỉ lưu vào database nếu checklist mới khác checklist cũ
        if final_checklist != current_checklist:
            sponsorship.benefits_checklist = final_checklist
            sponsorship.save(update_fields=['benefits_checklist'])

    finally:
        # Kết nối lại signal sau khi đã xử lý xong
        post_save.connect(create_or_update_sponsorship_checklist, sender=Sponsorship)        