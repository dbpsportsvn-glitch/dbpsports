# backend/users/models.py
from django.db import models
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver

# === BẮT ĐẦU THÊM MỚI TẠI ĐÂY ===
class Role(models.Model):
    """Định nghĩa các vai trò khác nhau trong hệ thống."""
    ROLE_CHOICES = [
        ('ORGANIZER', 'Ban Tổ chức'),
        ('PLAYER', 'Cầu thủ'),
        ('COMMENTATOR', 'Bình Luận Viên'),
        ('MEDIA', 'Đơn Vị Truyền Thông'),
        ('PHOTOGRAPHER', 'Nhiếp Ảnh Gia'),
        ('COLLABORATOR', 'Cộng Tác Viên'),
    ]
    id = models.CharField(max_length=20, primary_key=True, choices=ROLE_CHOICES)
    name = models.CharField("Tên vai trò", max_length=50)
    icon = models.CharField("Tên icon (Bootstrap Icons)", max_length=50, help_text="Ví dụ: bi-shield-check")
    description = models.TextField("Mô tả vai trò")

    def __str__(self):
        return self.name

# === KẾT THÚC THÊM MỚI ===


class Profile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='profile')
    avatar = models.ImageField("Ảnh đại diện", upload_to='user_avatars/', null=True, blank=True)
    
    # === BẮT ĐẦU THAY ĐỔI TẠI ĐÂY ===
    roles = models.ManyToManyField(Role, blank=True, verbose_name="Các vai trò đã chọn")
    has_selected_roles = models.BooleanField("Đã chọn vai trò lần đầu", default=False)
    # === KẾT THÚC THAY ĐỔI ===

    notify_match_results = models.BooleanField("Nhận thông báo kết quả trận đấu", default=True)
    notify_new_teams = models.BooleanField("Nhận thông báo khi có đội mới", default=True)
    notify_draw_results = models.BooleanField("Nhận thông báo khi có kết quả bốc thăm", default=True)
    notify_schedule_updates = models.BooleanField("Nhận thông báo khi có lịch thi đấu mới", default=True)

    def __str__(self):
        return f"Hồ sơ của {self.user.username}"

# (Các hàm receiver giữ nguyên không đổi)
@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()