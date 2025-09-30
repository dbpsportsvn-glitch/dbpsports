# backend/users/adapters.py
from allauth.account.adapter import DefaultAccountAdapter
from allauth.exceptions import ImmediateHttpResponse
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.account.utils import perform_login
from django.contrib.auth import get_user_model
from django.shortcuts import redirect
from django.contrib import messages
from .models import Profile # <-- Thêm import Profile
from django.urls import reverse

#------------------------------------

User = get_user_model()

class CustomAccountAdapter(DefaultAccountAdapter):
    def save_user(self, request, user, form, commit=True):
        user = super().save_user(request, user, form, commit=False)
        user.username = user.email
        if commit:
            user.save()
        return user

    # === THAY ĐỔI KHỐI NÀY ===
    def get_login_redirect_url(self, request):
        """
        Ghi đè để chuyển hướng người dùng đến các bước thiết lập
        cần thiết nếu chưa hoàn thành.
        """
        profile = request.user.profile
        if not profile.has_selected_roles:
            return reverse('select_roles')
        # Dùng cờ mới để kiểm tra
        if not profile.is_profile_complete:
            return reverse('profile_setup')
        return reverse('home') # Luôn chuyển về trang chủ sau khi xong

    def get_signup_redirect_url(self, request):
        """
        Chuyển hướng người dùng đến trang chọn vai trò sau khi đăng ký thành công.
        """
        return reverse('select_roles')


class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    # === THAY ĐỔI KHỐI NÀY ===
    def pre_social_login(self, request, sociallogin):
        if sociallogin.is_existing:
            return

        email = sociallogin.account.extra_data.get('email', '').lower()
        if not email:
            return

        try:
            user = User.objects.get(email__iexact=email)
            profile, created = Profile.objects.get_or_create(user=user)
            sociallogin.connect(request, user)
            perform_login(request, user, email_verification='none')
            messages.success(request, "Đăng nhập thành công! Tài khoản của bạn đã được liên kết.")
            
            # Quyết định URL chuyển hướng dựa trên các cờ mới
            redirect_url = 'home'
            if not profile.has_selected_roles:
                redirect_url = 'select_roles'
            elif not profile.is_profile_complete:
                redirect_url = 'profile_setup'
            
            raise ImmediateHttpResponse(redirect(redirect_url))
        except User.DoesNotExist:
            pass

    def save_user(self, request, sociallogin, form=None):
        user = sociallogin.user
        user.username = user.email
        sociallogin.save(request)
        return user