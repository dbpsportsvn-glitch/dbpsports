from django.db import models
from django.conf import settings

class Organization(models.Model):
    """
    Đại diện cho một đơn vị tổ chức giải đấu trên nền tảng.
    """
    # === BẮT ĐẦU THÊM MỚI ===
    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Chờ xét duyệt'
        ACTIVE = 'ACTIVE', 'Đang hoạt động'
        REJECTED = 'REJECTED', 'Bị từ chối'
        DISABLED = 'DISABLED', 'Vô hiệu hóa'

    status = models.CharField(
        "Trạng thái",
        max_length=10,
        choices=Status.choices,
        default=Status.PENDING # Mặc định khi mới tạo là "Chờ xét duyệt"
    )
    # === KẾT THÚC THÊM MỚI ===

    name = models.CharField("Tên đơn vị tổ chức", max_length=150)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='owned_organizations',
        verbose_name="Chủ sở hữu"
    )
    members = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        through='Membership',
        related_name='organizations',
        verbose_name="Thành viên"
    )
    logo = models.ImageField("Logo", upload_to='org_logos/', null=True, blank=True)
    phone_number = models.CharField("Số điện thoại", max_length=20, blank=True)
    contact_email = models.EmailField("Email liên hệ", blank=True)
    created_at = models.DateTimeField("Ngày tạo", auto_now_add=True)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        is_new = self._state.adding
        super().save(*args, **kwargs)
        if is_new and self.owner:
            Membership.objects.create(
                organization=self,
                user=self.owner,
                role=Membership.Role.OWNER
            )

class Membership(models.Model):
    """
    Liên kết một User với một Organization và gán vai trò cho họ.
    """
    class Role(models.TextChoices):
        OWNER = 'OWNER', 'Chủ sở hữu'
        ADMIN = 'ADMIN', 'Quản trị viên'

    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, verbose_name="Đơn vị")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name="Thành viên")
    role = models.CharField("Vai trò", max_length=10, choices=Role.choices, default=Role.ADMIN)
    date_joined = models.DateTimeField(auto_now_add=True)

    class Meta:
        # Đảm bảo một người dùng chỉ có một vai trò trong một đơn vị
        unique_together = ('organization', 'user')

    def __str__(self):
        return f"{self.user.username} - {self.get_role_display()} tại {self.organization.name}"

class JobPosting(models.Model):
    """Lưu một tin đăng tuyển nhân sự của BTC cho một giải đấu, từ Sân bóng, hoặc từ Chuyên gia tìm việc."""
    class Status(models.TextChoices):
        OPEN = 'OPEN', 'Đang mở'
        CLOSED = 'CLOSED', 'Đã đóng'
    
    class PostedBy(models.TextChoices):
        TOURNAMENT = 'TOURNAMENT', 'Ban Tổ chức Giải đấu'
        STADIUM = 'STADIUM', 'Sân bóng'
        PROFESSIONAL = 'PROFESSIONAL', 'Chuyên gia tìm việc'

    # Người đăng tin
    posted_by = models.CharField(
        "Đăng bởi",
        max_length=20,
        choices=PostedBy.choices,
        default=PostedBy.TOURNAMENT
    )
    
    # Liên kết đến giải đấu (nếu BTC đăng)
    tournament = models.ForeignKey(
        "tournaments.Tournament",
        on_delete=models.CASCADE,
        related_name='job_postings',
        verbose_name="Giải đấu",
        null=True,
        blank=True,
        help_text="Chỉ điền nếu tin này được đăng bởi BTC"
    )
    
    # Liên kết đến sân bóng (nếu sân bóng đăng)
    stadium = models.ForeignKey(
        "users.StadiumProfile",
        on_delete=models.CASCADE,
        related_name='job_postings',
        verbose_name="Sân bóng",
        null=True,
        blank=True,
        help_text="Chỉ điền nếu tin này được đăng bởi Sân bóng"
    )
    
    # Liên kết đến chuyên gia (nếu chuyên gia đăng tin tìm việc)
    professional_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='professional_job_postings',
        verbose_name="Chuyên gia",
        null=True,
        blank=True,
        help_text="Chỉ điền nếu tin này được đăng bởi Chuyên gia tìm việc"
    )
    
    role_required = models.ForeignKey("users.Role", on_delete=models.CASCADE, verbose_name="Vai trò cần tuyển")
    location_detail = models.CharField("Tỉnh/Thành phố (tùy chọn)", max_length=100, blank=True, help_text="Nếu bỏ trống, sẽ lấy theo địa điểm của giải đấu hoặc sân bóng.")
    title = models.CharField("Tiêu đề công việc", max_length=200)
    description = models.TextField("Mô tả chi tiết")
    budget = models.CharField("Mức kinh phí", max_length=150, blank=True, help_text="Ví dụ: 500.000 VNĐ/trận, hoặc 'Thỏa thuận'")
    status = models.CharField("Trạng thái", max_length=10, choices=Status.choices, default=Status.OPEN)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Tin Tuyển dụng"
        verbose_name_plural = "Các Tin Tuyển dụng"

    def __str__(self):
        if self.posted_by == self.PostedBy.STADIUM and self.stadium:
            return f"{self.title} tại {self.stadium.stadium_name}"
        elif self.posted_by == self.PostedBy.PROFESSIONAL and self.professional_user:
            return f"{self.title} - {self.professional_user.get_full_name() or self.professional_user.username}"
        elif self.tournament:
            return f"{self.title} cho giải {self.tournament.name}"
        return self.title
    
    def clean(self):
        from django.core.exceptions import ValidationError
        
        # Debug: in ra giá trị posted_by
        print(f"Model clean() - posted_by: {self.posted_by}")
        print(f"Model clean() - tournament: {self.tournament}")
        print(f"Model clean() - stadium: {self.stadium}")
        print(f"Model clean() - professional_user: {self.professional_user}")
        
        # Đảm bảo chỉ có một trong ba: tournament, stadium, hoặc professional_user
        if self.posted_by == self.PostedBy.TOURNAMENT and not self.tournament:
            raise ValidationError("Phải chọn Giải đấu nếu đăng bởi BTC")
        if self.posted_by == self.PostedBy.STADIUM and not self.stadium:
            raise ValidationError("Phải chọn Sân bóng nếu đăng bởi Sân bóng")
        if self.posted_by == self.PostedBy.PROFESSIONAL and not self.professional_user:
            raise ValidationError("Phải chọn Chuyên gia nếu đăng bởi Chuyên gia")
        
        # Đếm số lượng trường được điền
        filled_count = sum([bool(self.tournament), bool(self.stadium), bool(self.professional_user)])
        if filled_count > 1:
            raise ValidationError("Chỉ được chọn một trong ba: Giải đấu, Sân bóng, hoặc Chuyên gia")

class JobApplication(models.Model):
    """Lưu một đơn ứng tuyển của người dùng vào một tin tuyển dụng."""
    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Đang chờ'
        APPROVED = 'APPROVED', 'Đã chấp thuận'
        REJECTED = 'REJECTED', 'Đã từ chối'

    job = models.ForeignKey(JobPosting, on_delete=models.CASCADE, related_name='applications', verbose_name="Công việc")
    applicant = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='job_applications', verbose_name="Người ứng tuyển")
    message = models.TextField("Lời nhắn (tùy chọn)", blank=True, help_text="Gửi một vài lời giới thiệu về kỹ năng và kinh nghiệm của bạn cho BTC.")
    status = models.CharField("Trạng thái", max_length=10, choices=Status.choices, default=Status.PENDING)
    applied_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-applied_at']
        unique_together = ('job', 'applicant') # Mỗi người chỉ được ứng tuyển 1 lần/công việc
        verbose_name = "Đơn Ứng tuyển"
        verbose_name_plural = "Các Đơn Ứng tuyển"

    def __str__(self):
        return f"{self.applicant.username} ứng tuyển vào {self.job.title}"      

class ProfessionalReview(models.Model):
    """Lưu một đánh giá của BTC cho một chuyên gia sau khi hoàn thành công việc."""
    job_application = models.OneToOneField(
        JobApplication, 
        on_delete=models.CASCADE, 
        related_name='review',
        verbose_name="Đơn ứng tuyển"
    )
    reviewer = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='given_reviews',
        verbose_name="Người đánh giá (BTC)"
    )
    reviewee = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='received_reviews',
        verbose_name="Người được đánh giá (Chuyên gia)"
    )
    rating = models.PositiveIntegerField("Số sao", choices=[(i, f"{i} sao") for i in range(1, 6)])
    comment = models.TextField("Nội dung nhận xét", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Đánh giá Chuyên gia"
        verbose_name_plural = "Các Đánh giá Chuyên gia"

    def __str__(self):
        return f"Đánh giá {self.rating} sao cho {self.reviewee.username} từ {self.reviewer.username}"          