# backend/users/admin.py
from django.contrib import admin
from .models import Role, Profile

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