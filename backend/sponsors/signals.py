# backend/sponsors/signals.py

from django.db.models.signals import m2m_changed
from django.dispatch import receiver
from django.conf import settings
from .models import SponsorProfile
from users.models import Profile # Cần import Profile để lấy quan hệ many-to-many

@receiver(m2m_changed, sender=Profile.roles.through)
def create_sponsor_profile_on_role_add(sender, instance, action, pk_set, **kwargs):
    """
    Lắng nghe sự kiện thay đổi trên trường 'roles' của Profile.
    Tự động tạo SponsorProfile nếu vai trò 'SPONSOR' được thêm vào.
    """
    # Chúng ta chỉ quan tâm khi có vai trò mới được thêm vào
    if action == 'post_add':
        # 'pk_set' chứa ID của các vai trò vừa được thêm.
        # Trong trường hợp của chúng ta, đó là các chuỗi như 'SPONSOR'
        if 'SPONSOR' in pk_set:
            profile_instance = instance # instance ở đây là một đối tượng Profile
            user = profile_instance.user

            # Kiểm tra xem user này đã có SponsorProfile chưa, nếu chưa thì tạo mới
            SponsorProfile.objects.get_or_create(
                user=user,
                # Ưu tiên lấy tên đầy đủ, nếu không có mới dùng username (email)
                defaults={'brand_name': user.get_full_name() or user.username}
            )