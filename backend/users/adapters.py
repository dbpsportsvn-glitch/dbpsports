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

    # === BẮT ĐẦU THAY ĐỔI: Chuyển hướng sau khi đăng nhập/đăng ký ===
    def get_login_redirect_url(self, request):
        """
        Ghi đè để chuyển hướng người dùng đến trang chọn vai trò
        nếu họ chưa chọn.
        """
        if not request.user.profile.has_selected_roles:
            return reverse('select_roles')
        return super().get_login_redirect_url(request)

    def get_signup_redirect_url(self, request):
        """
        Chuyển hướng người dùng đến trang chọn vai trò sau khi đăng ký thành công.
        """
        return reverse('select_roles')
    # === KẾT THÚC THAY ĐỔI ===


class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    # === BẮT ĐẦU KHỐI CODE ĐÃ SỬA LỖI VÀ CẢI TIẾN ===
    def pre_social_login(self, request, sociallogin):
        """
        Can thiệp trước khi quá trình đăng nhập social hoàn tất.
        - Kiểm tra và tạo Profile nếu chưa có.
        - Chuyển hướng đến trang chọn vai trò nếu cần.
        """
        # Bỏ qua nếu tài khoản social này đã được kết nối
        if sociallogin.is_existing:
            return

        # Lấy email từ tài khoản social
        email = sociallogin.account.extra_data.get('email', '').lower()
        if not email:
            return

        # Thử tìm người dùng đã tồn tại với email này
        try:
            user = User.objects.get(email__iexact=email)
            
            # GIẢI PHÁP: Dùng get_or_create để đảm bảo Profile luôn tồn tại
            profile, created = Profile.objects.get_or_create(user=user)
            
            # Kết nối tài khoản social với người dùng hiện có
            sociallogin.connect(request, user)
            
            # Thực hiện đăng nhập cho người dùng
            perform_login(request, user, email_verification='none')
            messages.success(request, "Đăng nhập thành công! Tài khoản Google của bạn đã được liên kết.")
            
            # Quyết định URL chuyển hướng
            if profile.has_selected_roles:
                redirect_url = 'dashboard'
            else:
                redirect_url = 'select_roles'
            
            # Dừng quá trình và chuyển hướng ngay lập tức
            raise ImmediateHttpResponse(redirect(redirect_url))

        except User.DoesNotExist:
            # Nếu không tìm thấy email, tiếp tục quy trình đăng ký social bình thường
            pass
    # === KẾT THÚC KHỐI CODE ĐÃ SỬA LỖI ===

    def save_user(self, request, sociallogin, form=None):
        """
        Ghi đè phương thức này để tự động gán username bằng email
        khi tạo người dùng mới từ social login.
        """
        user = sociallogin.user
        user.username = user.email
        sociallogin.save(request)
        return user