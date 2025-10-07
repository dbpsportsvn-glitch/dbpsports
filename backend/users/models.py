# backend/users/models.py
from django.db import models
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver

class Role(models.Model):
    """Định nghĩa các vai trò khác nhau trong hệ thống."""
    ROLE_CHOICES = [
        ('ORGANIZER', 'Ban Tổ chức'),
        ('PLAYER', 'Cầu thủ'),
        ('COMMENTATOR', 'Bình Luận Viên'),
        ('MEDIA', 'Đơn Vị Truyền Thông'),
        ('PHOTOGRAPHER', 'Nhiếp Ảnh Gia'),
        ('COLLABORATOR', 'Cộng Tác Viên'),
        ('TOURNAMENT_MANAGER', 'Quản lý Giải đấu'),
        ('REFEREE', 'Trọng tài'),
    ]
    id = models.CharField(max_length=20, primary_key=True, choices=ROLE_CHOICES)
    name = models.CharField("Tên vai trò", max_length=50)
    icon = models.CharField("Tên icon (Bootstrap Icons)", max_length=50, help_text="Ví dụ: bi-shield-check")
    description = models.TextField("Mô tả vai trò")
    order = models.PositiveIntegerField("Thứ tự hiển thị", default=0, help_text="Số nhỏ hơn sẽ được hiển thị trước.")

    class Meta:
        ordering = ['order']

    def __str__(self):
        return self.name


class Profile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='profile')
    avatar = models.ImageField("Ảnh đại diện", upload_to='user_avatars/', null=True, blank=True)
    
    roles = models.ManyToManyField(Role, blank=True, verbose_name="Các vai trò đã chọn")
    has_selected_roles = models.BooleanField("Đã chọn vai trò lần đầu", default=False)
    
    is_profile_complete = models.BooleanField("Đã hoàn tất hồ sơ lần đầu", default=False)
    
    bio = models.TextField("Giới thiệu bản thân", blank=True, help_text="Một vài dòng về kỹ năng, đam mê hoặc thành tích của bạn.")
    location = models.CharField("Khu vực hoạt động", max_length=100, blank=True, help_text="Ví dụ: Hà Nội, TP.HCM, Điện Biên...")
    experience = models.PositiveIntegerField("Số năm kinh nghiệm", null=True, blank=True, help_text="Để trống nếu không áp dụng.")
    equipment = models.CharField("Thiết bị sở hữu", max_length=255, blank=True, help_text="Liệt kê các thiết bị chuyên dụng nếu có (máy ảnh, flycam, micro...).")

    notify_match_results = models.BooleanField("Nhận thông báo kết quả trận đấu", default=True)
    notify_new_teams = models.BooleanField("Nhận thông báo khi có đội mới", default=True)
    notify_draw_results = models.BooleanField("Nhận thông báo khi có kết quả bốc thăm", default=True)
    notify_schedule_updates = models.BooleanField("Nhận thông báo khi có lịch thi đấu mới", default=True)


    def __str__(self):
        return f"Hồ sơ của {self.user.username}"

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()