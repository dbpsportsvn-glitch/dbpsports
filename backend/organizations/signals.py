# backend/organizations/signals.py

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.urls import reverse
from tournaments.models import TournamentStaff, Notification

@receiver(post_save, sender=TournamentStaff)
def notify_user_on_new_role(sender, instance, created, **kwargs):
    """
    Gửi thông báo cho người dùng khi họ được gán một vai trò mới trong giải đấu.
    """
    if created:
        staff_entry = instance
        user_to_notify = staff_entry.user
        tournament = staff_entry.tournament
        role = staff_entry.role

        title = f"Bạn có vai trò mới tại giải đấu"
        message = (
            f"Bạn đã được chỉ định làm '{role.name}' "
            f"cho giải đấu '{tournament.name}'. "
            f"Hãy vào trang giải đấu để xem các quyền mới của bạn."
        )
        # Tạo URL để người dùng có thể nhấp vào và đi đến trang giải đấu
        url = reverse('tournament_detail', kwargs={'pk': tournament.pk})

        Notification.objects.create(
            user=user_to_notify,
            title=title,
            message=message,
            notification_type=Notification.NotificationType.GENERIC, # Dùng loại thông báo chung
            related_url=url
        )
        print(f"Created role assignment notification for {user_to_notify.username}")