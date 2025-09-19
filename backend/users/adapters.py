# backend/users/adapters.py

from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.contrib.auth import get_user_model

User = get_user_model()

class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    def save_user(self, request, sociallogin, form=None):
        """
        Lưu người dùng social account. Ghi đè để đảm bảo username là duy nhất.
        """
        user = super().save_user(request, sociallogin, form)
        # Đảm bảo username được đặt thành email nếu nó trống hoặc đã tồn tại
        if not user.username or User.objects.filter(username=user.username).exclude(pk=user.pk).exists():
            user.username = user.email
            user.save()
        return user