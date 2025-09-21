from django.db import models
from django.conf import settings

class Organization(models.Model):
    """
    Đại diện cho một đơn vị tổ chức giải đấu trên nền tảng.
    """
    name = models.CharField("Tên đơn vị tổ chức", max_length=150)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT, # Không cho xóa User nếu họ đang là chủ sở hữu
        related_name='owned_organizations',
        verbose_name="Chủ sở hữu"
    )
    members = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        through='Membership', # Liên kết thông qua model Membership
        related_name='organizations',
        verbose_name="Thành viên"
    )
    logo = models.ImageField("Logo", upload_to='org_logos/', null=True, blank=True)
    created_at = models.DateTimeField("Ngày tạo", auto_now_add=True)

    def __str__(self):
        return self.name

    # === BẮT ĐẦU THÊM MỚI ===
    def save(self, *args, **kwargs):
        # is_new sẽ là True nếu đây là lần đầu tiên object được tạo
        is_new = self._state.adding
        super().save(*args, **kwargs)
        # Nếu là object mới, hãy tự động tạo Membership cho owner
        if is_new and self.owner:
            Membership.objects.create(
                organization=self,
                user=self.owner,
                role=Membership.Role.OWNER
            )
    # === KẾT THÚC THÊM MỚI ===        
    
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