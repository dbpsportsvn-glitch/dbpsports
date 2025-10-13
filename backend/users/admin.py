# backend/users/admin.py
from django.contrib import admin
from .models import Role, Profile, CoachProfile, StadiumProfile

@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ('name', 'id', 'icon', 'order')
    list_editable = ('order',)
    search_fields = ('name', 'id')

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'has_selected_roles')
    list_filter = ('has_selected_roles',)
    filter_horizontal = ('roles',)

@admin.register(CoachProfile)
class CoachProfileAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'user', 'team', 'is_available', 'region', 'location_detail', 'years_of_experience')
    list_filter = ('is_available', 'region', 'created_at')
    search_fields = ('full_name', 'user__username', 'coaching_license', 'specialization')
    readonly_fields = ('created_at', 'updated_at')
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