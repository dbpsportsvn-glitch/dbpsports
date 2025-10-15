# backend/sponsors/admin.py

from django.contrib import admin
from .models import SponsorProfile, Testimonial

@admin.register(SponsorProfile)
class SponsorProfileAdmin(admin.ModelAdmin):
    list_display = ('brand_name', 'user', 'website_url', 'updated_at')
    search_fields = ('brand_name', 'user__username')
    list_filter = ('created_at',)
    autocomplete_fields = ('user',) # Giúp tìm kiếm user dễ dàng hơn
    
    class Meta:
        verbose_name = "Hồ sơ nhà tài trợ"
        verbose_name_plural = "Hồ sơ nhà tài trợ"

@admin.register(Testimonial)
class TestimonialAdmin(admin.ModelAdmin):
    list_display = ('author', 'sponsor_profile', 'is_approved', 'created_at')
    list_filter = ('is_approved', 'created_at')
    search_fields = ('author__username', 'sponsor_profile__brand_name', 'text')
    list_editable = ('is_approved',) # Cho phép sửa trạng thái ngay trên danh sách
    autocomplete_fields = ('sponsor_profile', 'author', 'tournament')
    
    class Meta:
        verbose_name = "Lời chứng thực"
        verbose_name_plural = "Lời chứng thực"