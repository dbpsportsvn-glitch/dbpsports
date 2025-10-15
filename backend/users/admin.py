# backend/users/admin.py
from django.contrib import admin
from .models import Role, Profile, CoachProfile, StadiumProfile, CoachReview, StadiumReview

@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ('name', 'id', 'icon', 'order')
    list_editable = ('order',)
    search_fields = ('name', 'id')
    
    class Meta:
        verbose_name = "Vai trò"
        verbose_name_plural = "Vai trò"

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'has_selected_roles')
    list_filter = ('has_selected_roles',)
    filter_horizontal = ('roles',)
    
    class Meta:
        verbose_name = "Hồ sơ"
        verbose_name_plural = "Hồ sơ"

@admin.register(CoachProfile)
class CoachProfileAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'user', 'team', 'is_available', 'region', 'location_detail', 'years_of_experience')
    list_filter = ('is_available', 'region', 'created_at')
    search_fields = ('full_name', 'user__username', 'coaching_license', 'specialization')
    readonly_fields = ('created_at', 'updated_at')
    
    class Meta:
        verbose_name = "Hồ sơ HLV"
        verbose_name_plural = "Hồ sơ HLV"
    fieldsets = (
        ('Thông tin cơ bản', {
            'fields': ('user', 'team', 'full_name', 'avatar', 'bio', 'date_of_birth')
        }),
        ('Kinh nghiệm & Chứng chỉ', {
            'fields': ('years_of_experience', 'coaching_license', 'specialization', 'achievements', 'previous_teams')
        }),
        ('Liên hệ & Khu vực', {
            'fields': ('phone_number', 'email', 'region', 'location_detail')
        }),
        ('Trạng thái', {
            'fields': ('is_available',)
        }),
        ('Thông tin hệ thống', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(StadiumProfile)
class StadiumProfileAdmin(admin.ModelAdmin):
    list_display = ('stadium_name', 'user', 'field_type', 'region', 'location_detail', 'phone_number')
    list_filter = ('field_type', 'region', 'created_at')
    search_fields = ('stadium_name', 'user__username', 'address', 'location_detail')
    readonly_fields = ('created_at', 'updated_at')
    
    class Meta:
        verbose_name = "Hồ sơ sân bóng"
        verbose_name_plural = "Hồ sơ sân bóng"
    fieldsets = (
        ('Thông tin cơ bản', {
            'fields': ('user', 'stadium_name', 'logo', 'description')
        }),
        ('Địa chỉ & Liên hệ', {
            'fields': ('address', 'region', 'location_detail', 'phone_number', 'email', 'website')
        }),
        ('Thông tin sân', {
            'fields': ('field_type', 'capacity', 'number_of_fields', 'amenities', 'rental_price_range', 'operating_hours')
        }),
        ('Thanh toán', {
            'fields': ('bank_name', 'bank_account_number', 'bank_account_name', 'payment_qr_code')
        }),
        ('Thông tin hệ thống', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(CoachReview)
class CoachReviewAdmin(admin.ModelAdmin):
    list_display = ('coach_profile', 'reviewer', 'rating', 'team', 'tournament', 'is_approved', 'created_at')
    list_filter = ('rating', 'is_approved', 'created_at')
    search_fields = ('coach_profile__full_name', 'reviewer__username', 'comment')
    readonly_fields = ('created_at',)
    list_editable = ('is_approved',)
    
    class Meta:
        verbose_name = "Đánh giá HLV"
        verbose_name_plural = "Đánh giá HLV"


@admin.register(StadiumReview)
class StadiumReviewAdmin(admin.ModelAdmin):
    list_display = ('stadium_profile', 'reviewer', 'rating', 'team', 'tournament', 'is_approved', 'created_at')
    list_filter = ('rating', 'is_approved', 'created_at')
    search_fields = ('stadium_profile__stadium_name', 'reviewer__username', 'comment')
    readonly_fields = ('created_at',)
    list_editable = ('is_approved',)
    
    class Meta:
        verbose_name = "Đánh giá sân bóng"
        verbose_name_plural = "Đánh giá sân bóng"