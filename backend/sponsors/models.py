# backend/sponsors/models.py

from django.db import models
from django.conf import settings
from django.urls import reverse

# Chúng ta sẽ cần liên kết đến model Tournament sau này
from tournaments.models import Tournament
from users.models import SponsorProfile  # Import model mới từ users app

# DEPRECATED: Model SponsorProfile cũ đã được xóa và thay thế bởi users.models.SponsorProfile
# Model mới có đầy đủ fields: payment_qr_code, email, region, location_detail, is_active...

class Testimonial(models.Model):
    """Lưu trữ nhận xét, lời chứng thực cho nhà tài trợ."""
    sponsor_profile = models.ForeignKey(
        SponsorProfile, 
        on_delete=models.CASCADE, 
        related_name='testimonials',
        verbose_name="Hồ sơ Nhà tài trợ"
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE,
        verbose_name="Người viết"
    )
    tournament = models.ForeignKey(
        Tournament,
        on_delete=models.SET_NULL, # Giữ lại nhận xét dù giải đấu bị xóa
        null=True,
        blank=True,
        verbose_name="Giải đấu liên quan"
    )
    rating = models.PositiveSmallIntegerField(
        "Xếp hạng (sao)",
        choices=[(i, f"{i} sao") for i in range(1, 6)], # Lựa chọn từ 1 đến 5
        default=5
    )
    text = models.TextField("Nội dung nhận xét", max_length=1000)
    is_approved = models.BooleanField("Được hiển thị", default=True, help_text="Nhà tài trợ có thể chọn ẩn/hiện nhận xét này trên hồ sơ của họ.")
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Nhận xét"
        verbose_name_plural = "Các Nhận xét"
        ordering = ['-created_at']

    def __str__(self):
        return f"Nhận xét từ {self.author.username} cho {self.sponsor_profile.brand_name}"