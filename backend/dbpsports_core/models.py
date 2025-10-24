from django.db import models
from django.utils import timezone


class NewsletterSubscription(models.Model):
    """Model để lưu trữ email đăng ký nhận thông báo"""
    email = models.EmailField(
        unique=True,
        verbose_name="Email đăng ký",
        help_text="Địa chỉ email để nhận thông báo"
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="Trạng thái hoạt động",
        help_text="Có nhận thông báo hay không"
    )
    subscribed_at = models.DateTimeField(
        default=timezone.now,
        verbose_name="Ngày đăng ký"
    )
    unsubscribed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Ngày hủy đăng ký"
    )
    
    class Meta:
        verbose_name = "Đăng ký nhận thông báo"
        verbose_name_plural = "Đăng ký nhận thông báo"
        ordering = ['-subscribed_at']
    
    def __str__(self):
        return f"{self.email} - {'Hoạt động' if self.is_active else 'Đã hủy'}"
    
    def unsubscribe(self):
        """Hủy đăng ký newsletter"""
        self.is_active = False
        self.unsubscribed_at = timezone.now()
        self.save()
