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
    """Lưu một tin đăng tuyển nhân sự của BTC cho một giải đấu."""
    class Status(models.TextChoices):
        OPEN = 'OPEN', 'Đang mở'
        CLOSED = 'CLOSED', 'Đã đóng'

    tournament = models.ForeignKey("tournaments.Tournament", on_delete=models.CASCADE, related_name='job_postings', verbose_name="Giải đấu")
    role_required = models.ForeignKey("users.Role", on_delete=models.CASCADE, verbose_name="Vai trò cần tuyển")
    location_detail = models.CharField("Tỉnh/Thành phố (tùy chọn)", max_length=100, blank=True, help_text="Nếu bỏ trống, sẽ lấy theo địa điểm của giải đấu.")
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
        return f"{self.title} cho giải {self.tournament.name}"

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