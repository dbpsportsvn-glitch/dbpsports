# backend/users/models.py
from django.db import models
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver

class Role(models.Model):
    """Định nghĩa các vai trò khác nhau trong hệ thống."""
    ROLE_CHOICES = [
        ('ORGANIZER', 'Ban Tổ chức'),
        ('PLAYER', 'Cầu thủ'),
        ('COMMENTATOR', 'Bình Luận Viên'),
        ('MEDIA', 'Đơn Vị Truyền Thông'),
        ('PHOTOGRAPHER', 'Nhiếp Ảnh Gia'),
        ('COLLABORATOR', 'Cộng Tác Viên'),
        ('TOURNAMENT_MANAGER', 'Quản lý Giải đấu'),
        ('REFEREE', 'Trọng tài'),
        ('SPONSOR', 'Nhà tài trợ'),
        ('COACH', 'Huấn luyện viên'),
        ('STADIUM', 'Sân bóng'),
    ]
    id = models.CharField(max_length=20, primary_key=True, choices=ROLE_CHOICES)
    name = models.CharField("Tên vai trò", max_length=50)
    icon = models.CharField("Tên icon (Bootstrap Icons)", max_length=50, help_text="Ví dụ: bi-shield-check")
    description = models.TextField("Mô tả vai trò")
    order = models.PositiveIntegerField("Thứ tự hiển thị", default=0, help_text="Số nhỏ hơn sẽ được hiển thị trước.")

    class Meta:
        ordering = ['order']

    def __str__(self):
        return self.name


class Profile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='profile')
    avatar = models.ImageField("Ảnh đại diện", upload_to='user_avatars/', null=True, blank=True)
    
    roles = models.ManyToManyField(Role, blank=True, verbose_name="Các vai trò đã chọn")
    has_selected_roles = models.BooleanField("Đã chọn vai trò lần đầu", default=False)
    is_profile_complete = models.BooleanField("Đã hoàn tất hồ sơ lần đầu", default=False)
    role_change_count = models.PositiveIntegerField(default=0, help_text="Số lần người dùng đã thay đổi vai trò.")
    
    bio = models.TextField("Giới thiệu bản thân", blank=True, help_text="Một vài dòng về kỹ năng, đam mê hoặc thành tích của bạn.")
    location = models.CharField("Khu vực hoạt động", max_length=100, blank=True, help_text="Ví dụ: Hà Nội, TP.HCM, Điện Biên...")
    experience = models.PositiveIntegerField("Số năm kinh nghiệm", null=True, blank=True, help_text="Để trống nếu không áp dụng.")
    equipment = models.CharField("Thiết bị sở hữu", max_length=255, blank=True, help_text="Liệt kê các thiết bị chuyên dụng nếu có (máy ảnh, flycam, micro...).")
    
    # Dành cho Trọng tài
    referee_level = models.CharField("Cấp độ Trọng tài", max_length=100, blank=True, help_text="Ví dụ: Chứng chỉ Futsal, Trọng tài Quận, v.v.")
    
    # Dành cho Nhà tài trợ
    brand_website = models.URLField("Website Thương hiệu", max_length=255, blank=True)
    sponsorship_interests = models.CharField("Lĩnh vực quan tâm tài trợ", max_length=255, blank=True, help_text="Ví dụ: Giải đấu U21, Đội bóng doanh nghiệp, Cầu thủ trẻ...")

    notify_match_results = models.BooleanField("Nhận thông báo kết quả trận đấu", default=True)
    notify_new_teams = models.BooleanField("Nhận thông báo khi có đội mới", default=True)
    notify_draw_results = models.BooleanField("Nhận thông báo khi có kết quả bốc thăm", default=True)
    notify_schedule_updates = models.BooleanField("Nhận thông báo khi có lịch thi đấu mới", default=True)


    def __str__(self):
        return f"Hồ sơ của {self.user.username}"

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()


class CoachProfile(models.Model):
    """Hồ sơ chi tiết dành cho Huấn luyện viên."""
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='coach_profile',
        verbose_name="Tài khoản"
    )
    team = models.ForeignKey(
        'tournaments.Team',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='coaches',
        verbose_name="Đội đang huấn luyện"
    )
    
    # Thông tin hồ sơ công khai
    full_name = models.CharField("Họ và tên", max_length=100)
    avatar = models.ImageField("Ảnh đại diện", upload_to='coach_avatars/', null=True, blank=True)
    bio = models.TextField("Giới thiệu bản thân", blank=True, help_text="Kinh nghiệm, triết lý huấn luyện...")
    date_of_birth = models.DateField("Ngày sinh", null=True, blank=True)
    
    # Kinh nghiệm & Chứng chỉ
    years_of_experience = models.PositiveIntegerField("Số năm kinh nghiệm", null=True, blank=True)
    coaching_license = models.CharField("Chứng chỉ HLV", max_length=200, blank=True, help_text="Ví dụ: AFC C, UEFA B...")
    specialization = models.CharField("Chuyên môn", max_length=200, blank=True, help_text="Ví dụ: Huấn luyện thể lực, Chiến thuật...")
    
    # Thành tích
    achievements = models.TextField("Thành tích nổi bật", blank=True, help_text="Các danh hiệu, giải thưởng đã đạt được")
    previous_teams = models.TextField("Đội đã từng huấn luyện", blank=True, help_text="Lịch sử công tác")
    
    # Liên hệ
    phone_number = models.CharField("Số điện thoại", max_length=20, blank=True)
    email = models.EmailField("Email liên hệ", blank=True)
    
    # Khu vực
    region = models.CharField(
        "Khu vực", 
        max_length=20, 
        choices=[
            ('MIEN_BAC', 'Miền Bắc'),
            ('MIEN_TRUNG', 'Miền Trung'),
            ('MIEN_NAM', 'Miền Nam'),
            ('KHAC', 'Khác')
        ],
        default='KHAC'
    )
    location_detail = models.CharField("Tỉnh/Thành phố", max_length=100, blank=True)
    
    # Trạng thái
    is_available = models.BooleanField("Đang tìm đội", default=False, help_text="Đánh dấu nếu đang tìm đội bóng để huấn luyện")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Hồ sơ Huấn luyện viên"
        verbose_name_plural = "Hồ sơ Huấn luyện viên"
    
    def __str__(self):
        return f"HLV {self.full_name}"


class StadiumProfile(models.Model):
    """Hồ sơ chi tiết dành cho Sân bóng."""
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='stadium_profile',
        verbose_name="Tài khoản"
    )
    
    # Thông tin cơ bản
    stadium_name = models.CharField("Tên sân", max_length=150)
    logo = models.ImageField("Logo/Ảnh sân", upload_to='stadium_logos/', null=True, blank=True)
    description = models.TextField("Mô tả", blank=True, help_text="Giới thiệu về sân bóng, cơ sở vật chất...")
    
    # Địa chỉ & Liên hệ
    address = models.CharField("Địa chỉ chi tiết", max_length=255)
    region = models.CharField(
        "Khu vực", 
        max_length=20, 
        choices=[
            ('MIEN_BAC', 'Miền Bắc'),
            ('MIEN_TRUNG', 'Miền Trung'),
            ('MIEN_NAM', 'Miền Nam'),
            ('KHAC', 'Khác')
        ],
        default='KHAC'
    )
    location_detail = models.CharField("Tỉnh/Thành phố", max_length=100, blank=True)
    phone_number = models.CharField("Số điện thoại", max_length=20)
    email = models.EmailField("Email liên hệ", blank=True)
    website = models.URLField("Website", blank=True)
    
    # Thông tin sân
    field_type = models.CharField(
        "Loại sân",
        max_length=50,
        choices=[
            ('GRASS_11', 'Sân cỏ tự nhiên 11 người'),
            ('GRASS_7', 'Sân cỏ tự nhiên 7 người'),
            ('GRASS_5', 'Sân cỏ tự nhiên 5 người'),
            ('ARTIFICIAL_11', 'Sân cỏ nhân tạo 11 người'),
            ('ARTIFICIAL_7', 'Sân cỏ nhân tạo 7 người'),
            ('ARTIFICIAL_5', 'Sân cỏ nhân tạo 5 người'),
            ('FUTSAL', 'Sân Futsal'),
            ('OTHER', 'Khác'),
        ],
        default='ARTIFICIAL_7'
    )
    capacity = models.PositiveIntegerField("Sức chứa khán giả", null=True, blank=True)
    number_of_fields = models.PositiveIntegerField("Số sân", default=1)
    
    # Dịch vụ & Tiện ích
    amenities = models.TextField(
        "Tiện ích",
        blank=True,
        help_text="Ví dụ: Phòng thay đồ, Bãi đỗ xe, Căn tin, Hệ thống đèn, Camera..."
    )
    rental_price_range = models.CharField(
        "Giá thuê (khoảng)",
        max_length=100,
        blank=True,
        help_text="Ví dụ: 500.000 - 1.000.000 VNĐ/giờ"
    )
    
    # Thanh toán
    bank_name = models.CharField("Tên ngân hàng", max_length=100, blank=True)
    bank_account_number = models.CharField("Số tài khoản", max_length=50, blank=True)
    bank_account_name = models.CharField("Tên chủ tài khoản", max_length=100, blank=True)
    payment_qr_code = models.ImageField("Mã QR thanh toán", upload_to='stadium_qr_codes/', null=True, blank=True)
    
    # Giờ hoạt động
    operating_hours = models.TextField(
        "Giờ hoạt động",
        blank=True,
        help_text="Ví dụ: Thứ 2-7: 6h-22h, Chủ nhật: 6h-20h"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Hồ sơ Sân bóng"
        verbose_name_plural = "Hồ sơ Sân bóng"
    
    def __str__(self):
        return self.stadium_name