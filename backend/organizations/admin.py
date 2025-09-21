from django.contrib import admin, messages
from django.db import models
from .models import Organization, Membership

# Import các công cụ cần thiết
from tournaments.utils import send_notification_email
from django.conf import settings


class MembershipInline(admin.TabularInline):
    model = Membership
    extra = 1
    autocomplete_fields = ['user']
    fields = ('user', 'role')
    verbose_name = "Thành viên"
    verbose_name_plural = "Các thành viên"


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    # === BẮT ĐẦU SỬA ĐỔI ===
    list_display = ('name', 'owner', 'status', 'member_count', 'created_at')
    list_filter = ('status', 'created_at')
    list_editable = ('status',) # Cho phép sửa trực tiếp trên danh sách
    actions = ['approve_organizations'] # Thêm hành động mới
    # === KẾT THÚC SỬA ĐỔI ===

    search_fields = ('name', 'owner__username')
    autocomplete_fields = ['owner']
    inlines = [MembershipInline]

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related('members').annotate(
            models.Count('members')
        )

    @admin.display(description='Số thành viên')
    def member_count(self, obj):
        return obj.members__count

    @admin.action(description='Duyệt các đơn vị tổ chức đã chọn')
    def approve_organizations(self, request, queryset):
        # Lọc ra những đơn vị đang ở trạng thái chờ
        pending_orgs = queryset.filter(status=Organization.Status.PENDING)

        approved_count = 0
        for org in pending_orgs:
            # Chuyển trạng thái
            org.status = Organization.Status.ACTIVE
            org.save()
            approved_count += 1

            # Gửi email thông báo cho chủ sở hữu
            if org.owner.email:
                send_notification_email(
                    subject=f"Đơn vị tổ chức '{org.name}' của bạn đã được duyệt!",
                    template_name='organizations/emails/organization_approved.html',
                    context={'organization': org, 'owner': org.owner},
                    recipient_list=[org.owner.email],
                    request=request # <--- THÊM DÒNG QUAN TRỌNG NÀY
                )

        if approved_count > 0:
            self.message_user(request, f"Đã duyệt thành công {approved_count} đơn vị.", messages.SUCCESS)

@admin.register(Membership)
class MembershipAdmin(admin.ModelAdmin):
    list_display = ('organization', 'user', 'role', 'date_joined')
    list_filter = ('organization', 'role')
    search_fields = ('organization__name', 'user__username')
    autocomplete_fields = ['organization', 'user']