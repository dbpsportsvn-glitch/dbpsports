# backend/users/models.py
from django.db import models
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver

class Profile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='profile')
    avatar = models.ImageField("Ảnh đại diện", upload_to='user_avatars/', null=True, blank=True)
    notify_match_results = models.BooleanField("Nhận thông báo kết quả trận đấu", default=True)
    notify_new_teams = models.BooleanField("Nhận thông báo khi có đội mới", default=True)    

    def __str__(self):
        return f"Hồ sơ của {self.user.username}"

# Tự động tạo Profile khi một User mới được tạo
@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

# Tự động lưu Profile khi User được lưu
@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()