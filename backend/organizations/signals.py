# backend/organizations/signals.py

from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.urls import reverse
from tournaments.models import TournamentStaff, Notification
from .models import Organization

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

# Store old status before save
@receiver(pre_save, sender=Organization)
def store_old_status(sender, instance, **kwargs):
    """Lưu trạng thái cũ của Organization trước khi save"""
    if instance.pk:
        try:
            old_instance = Organization.objects.get(pk=instance.pk)
            instance._old_status = old_instance.status
        except Organization.DoesNotExist:
            instance._old_status = None
    else:
        instance._old_status = None

@receiver(post_save, sender=Organization)
def create_shop_settings_on_approval(sender, instance, created, **kwargs):
    """
    Tự động tạo Shop Settings khi Organization được approved.
    """
    # Chỉ tạo Shop Settings khi chuyển từ PENDING sang ACTIVE
    if (not created and 
        hasattr(instance, '_old_status') and 
        instance._old_status == Organization.Status.PENDING and 
        instance.status == Organization.Status.ACTIVE):
        
        # Kiểm tra xem Organization có Shop Settings chưa
        try:
            instance.shop_settings
        except:
            # Nếu chưa có Shop Settings, tạo mới
            from shop.organization_models import OrganizationShopSettings
            
            OrganizationShopSettings.objects.create(
                organization=instance,
                shop_name=instance.name,
                is_active=True,
                shop_locked=True,  # Mặc định bị khoá, cần Admin mở
                contact_phone=instance.phone_number or '',
                contact_email=instance.contact_email or instance.owner.email or '',
            )
            print(f"Created Shop Settings for organization: {instance.name}")