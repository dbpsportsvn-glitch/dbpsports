# backend/sponsors/models.py

from django.db import models
from django.conf import settings
from django.urls import reverse

# Chúng ta sẽ cần liên kết đến model Tournament sau này
from tournaments.models import Tournament

class SponsorProfile(models.Model):
    """Lưu trữ hồ sơ công khai chi tiết của một nhà tài trợ."""
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='sponsor_profile',
        verbose_name="Tài khoản Nhà tài trợ"
    )
    brand_name = models.CharField("Tên thương hiệu", max_length=200, help_text="Tên công khai của nhà tài trợ.")
    brand_logo = models.ImageField(upload_to='sponsor_logos/', blank=True, null=True, verbose_name="Logo thương hiệu") # <-- THÊM DÒNG NÀY
    tagline = models.CharField("Slogan/Khẩu hiệu", max_length=255, blank=True, help_text="Một câu giới thiệu ngắn gọn.")
    description = models.TextField("Giới thiệu chi tiết", blank=True, help_text="Mô tả về thương hiệu, lĩnh vực hoạt động...")
    website_url = models.URLField("Link trang web", blank=True)
    phone_number = models.CharField("Số điện thoại", max_length=20, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Hồ sơ Nhà tài trợ"
        verbose_name_plural = "Các Hồ sơ Nhà tài trợ"

    def __str__(self):
        return self.brand_name

    def get_absolute_url(self):
        return reverse('public_profile', kwargs={'username': self.user.username})

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