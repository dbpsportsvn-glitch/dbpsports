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