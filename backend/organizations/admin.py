from django.contrib import admin
from django.db import models
from .models import Organization, Membership

class MembershipInline(admin.TabularInline):
    """
    Hiển thị danh sách thành viên ngay trong trang chi tiết của Organization.
    """
    model = Membership
    extra = 1  # Luôn có 1 dòng trống để thêm thành viên mới
    autocomplete_fields = ['user']
    fields = ('user', 'role')
    verbose_name = "Thành viên"
    verbose_name_plural = "Các thành viên"

@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ('name', 'owner', 'member_count', 'created_at')
    search_fields = ('name', 'owner__username')
    list_filter = ('created_at',)
    autocomplete_fields = ['owner']
    inlines = [MembershipInline]

    def get_queryset(self, request):
        # Tăng tốc độ load bằng cách lấy sẵn thông tin liên quan
        return super().get_queryset(request).prefetch_related('members').annotate(
            models.Count('members')
        )

    @admin.display(description='Số thành viên')
    def member_count(self, obj):
        # Hiển thị số lượng thành viên cho mỗi đơn vị
        return obj.members__count

@admin.register(Membership)
class MembershipAdmin(admin.ModelAdmin):
    list_display = ('organization', 'user', 'role', 'date_joined')
    list_filter = ('organization', 'role')
    search_fields = ('organization__name', 'user__username')
    autocomplete_fields = ['organization', 'user']