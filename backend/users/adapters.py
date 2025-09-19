# backend/users/adapters.py

from allauth.exceptions import ImmediateHttpResponse
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.account.utils import perform_login
from django.contrib.auth import get_user_model
from django.shortcuts import redirect
from django.contrib import messages

User = get_user_model()

class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    def pre_social_login(self, request, sociallogin):
        """
        Can thiệp vào quá trình đăng nhập social.
        Nếu email của người dùng social đã tồn tại trong hệ thống,
        hãy liên kết tài khoản social này với tài khoản đã có.
        """
        # Bỏ qua nếu người dùng đã được kết nối
        if sociallogin.is_existing:
            return

        # Kiểm tra xem có tài khoản social nào khác đã kết nối chưa
        if sociallogin.account.extra_data:
            email = sociallogin.account.extra_data.get('email', '').lower()
            if email:
                # Tìm người dùng có cùng email và chưa có tài khoản social
                try:
                    user = User.objects.get(email__iexact=email)
                    if not user.socialaccount_set.exists():
                        # Nếu tìm thấy, liên kết tài khoản social này với người dùng đó
                        sociallogin.connect(request, user)
                        
                        # Đăng nhập cho người dùng
                        perform_login(request, user, email_verification='none')
                        messages.success(request, "Đăng nhập thành công! Tài khoản Google của bạn đã được liên kết.")
                        raise ImmediateHttpResponse(redirect('dashboard')) # Chuyển hướng sau khi đăng nhập

                except User.DoesNotExist:
                    pass # Không tìm thấy, tiếp tục quy trình đăng ký bình thường

    def save_user(self, request, sociallogin, form=None):
        """
        Ghi đè để đảm bảo username là duy nhất.
        """
        user = super().save_user(request, sociallogin, form)
        # Đảm bảo username được đặt thành email nếu nó trống hoặc đã tồn tại
        if not user.username or User.objects.filter(username=user.username).exclude(pk=user.pk).exists():
            user.username = user.email
            user.save()
        return user