from django.contrib import admin, messages
from django.db import models
from .models import Organization, Membership, JobPosting, JobApplication

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
    
    class Meta:
        verbose_name = "Tổ chức"
        verbose_name_plural = "Tổ chức"

    class Media:
        js = ('js/admin_state.js',)
        
    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related('members').annotate(
            models.Count('members')
        )

    @admin.display(description='Số thành viên')
    def member_count(self, obj):
        return obj.members__count

    @admin.action(description='Duyệt các đơn vị tổ chức đã chọn')
    def approve_organizations(self, request, queryset):
        pending_orgs = queryset.filter(status=Organization.Status.PENDING)
        
        approved_count = 0
        emailed_count = 0
        failed_emails = []

        for org in pending_orgs:
            org.status = Organization.Status.ACTIVE
            org.save()
            approved_count += 1

            if org.owner.email:
                # Gọi hàm và nhận kết quả trả về
                success = send_notification_email(
                    subject=f"Đơn vị tổ chức '{org.name}' của bạn đã được duyệt!",
                    template_name='organizations/emails/organization_approved.html',
                    context={'organization': org, 'owner': org.owner},
                    recipient_list=[org.owner.email],
                    request=request
                )
                if success:
                    emailed_count += 1
                else:
                    failed_emails.append(org.owner.email)

        if approved_count > 0:
            self.message_user(request, f"Đã duyệt thành công {approved_count} đơn vị.", messages.SUCCESS)
        if emailed_count > 0:
            self.message_user(request, f"Đã gửi email thông báo thành công đến {emailed_count} người dùng.", messages.SUCCESS)
        # Thông báo cụ thể nếu có lỗi
        if failed_emails:
            self.message_user(request, f"Không thể gửi email đến các địa chỉ sau: {', '.join(failed_emails)}. Vui lòng kiểm tra logs của server.", messages.ERROR)

   # === THÊM PHƯƠNG THỨC NÀY VÀO CLASS OrganizationAdmin ===
    def save_model(self, request, obj, form, change):
        # 'change' is True if you are editing an existing object
        if change:
            try:
                # Lấy trạng thái CŨ của object từ database
                old_obj = Organization.objects.get(pk=obj.pk)
                old_status = old_obj.status
            except Organization.DoesNotExist:
                # Nếu không tìm thấy, cứ lưu bình thường
                super().save_model(request, obj, form, change)
                return

            # Lưu object mới trước
            super().save_model(request, obj, form, change)

            # Lấy trạng thái MỚI sau khi đã lưu
            new_status = obj.status

            # So sánh: chỉ gửi email nếu trạng thái thay đổi từ PENDING sang ACTIVE
            if old_status == Organization.Status.PENDING and new_status == Organization.Status.ACTIVE:
                if obj.owner.email:
                    send_notification_email(
                        subject=f"Đơn vị tổ chức '{obj.name}' của bạn đã được duyệt!",
                        template_name='organizations/emails/organization_approved.html',
                        context={'organization': obj, 'owner': obj.owner},
                        recipient_list=[obj.owner.email],
                        request=request
                    )
                    self.message_user(request, f"Đã gửi email thông báo duyệt cho {obj.owner.email}.", messages.SUCCESS)
        else:
            # Nếu đây là object mới (không phải sửa đổi), chỉ cần lưu
            super().save_model(request, obj, form, change)

@admin.register(Membership)
class MembershipAdmin(admin.ModelAdmin):
    list_display = ('organization', 'user', 'role', 'date_joined')
    list_filter = ('organization', 'role')
    search_fields = ('organization__name', 'user__username')
    autocomplete_fields = ['organization', 'user']
    
    class Meta:
        verbose_name = "Thành viên"
        verbose_name_plural = "Thành viên"

@admin.register(JobPosting)
class JobPostingAdmin(admin.ModelAdmin):
    list_display = ('title', 'posted_by', 'get_posted_for', 'role_required', 'status', 'created_at')
    list_filter = ('posted_by', 'status', 'role_required', 'created_at')
    search_fields = ('title', 'description', 'tournament__name', 'stadium__stadium_name')
    list_editable = ('status',)
    autocomplete_fields = ('tournament', 'stadium', 'role_required')
    list_select_related = ('tournament', 'stadium', 'role_required')
    readonly_fields = ('created_at',)
    list_per_page = 50
    
    class Meta:
        verbose_name = "Tin tuyển dụng"
        verbose_name_plural = "Tin tuyển dụng"
    
    @admin.display(description='Đăng cho', ordering='tournament__name')
    def get_posted_for(self, obj):
        if obj.posted_by == JobPosting.PostedBy.TOURNAMENT and obj.tournament:
            return f"Giải: {obj.tournament.name}"
        elif obj.posted_by == JobPosting.PostedBy.STADIUM and obj.stadium:
            return f"Sân: {obj.stadium.stadium_name}"
        return "N/A"
    
    fieldsets = (
        ('Thông tin đăng tin', {
            'fields': ('posted_by', 'tournament', 'stadium')
        }),
        ('Nội dung tuyển dụng', {
            'fields': ('role_required', 'title', 'description', 'budget', 'location_detail')
        }),
        ('Trạng thái', {
            'fields': ('status', 'created_at')
        }),
    )

@admin.register(JobApplication)
class JobApplicationAdmin(admin.ModelAdmin):
    list_display = ('applicant', 'job', 'status', 'applied_at')
    list_filter = ('status', 'job__posted_by', 'applied_at')
    search_fields = ('applicant__username', 'job__title', 'message')
    list_editable = ('status',)
    autocomplete_fields = ('job', 'applicant')
    list_select_related = ('job', 'applicant')
    readonly_fields = ('applied_at',)
    list_per_page = 50
    
    class Meta:
        verbose_name = "Đơn ứng tuyển"
        verbose_name_plural = "Đơn ứng tuyển"
    
    fieldsets = (
        ('Thông tin ứng tuyển', {
            'fields': ('job', 'applicant', 'message')
        }),
        ('Trạng thái', {
            'fields': ('status', 'applied_at')
        }),
    )