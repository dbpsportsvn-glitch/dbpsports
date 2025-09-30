# backend/users/admin.py
from django.contrib import admin
from .models import Role, Profile # Thêm Role và Profile

# === BẮT ĐẦU THÊM MỚI TẠI ĐÂY ===
@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ('name', 'id', 'icon', 'description')

# Bạn có thể thêm cả Profile vào admin để tiện theo dõi
@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'has_selected_roles')
    list_filter = ('has_selected_roles',)
    filter_horizontal = ('roles',) # Giúp chọn vai trò dễ hơn
# === KẾT THÚC THÊM MỚI ===