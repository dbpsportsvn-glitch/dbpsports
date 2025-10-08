# backend/users/adapters.py

# 1. Đảm bảo bạn đã thêm 2 dòng import này ở đầu file
import requests
from django.core.files.base import ContentFile

# 2. Các dòng import có sẵn khác
from allauth.account.adapter import DefaultAccountAdapter
from allauth.exceptions import ImmediateHttpResponse
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.account.utils import perform_login
from django.contrib.auth import get_user_model
from django.shortcuts import redirect
from django.contrib import messages
from .models import Profile
from django.urls import reverse

User = get_user_model()


# Lớp này giữ nguyên, không thay đổi
class CustomAccountAdapter(DefaultAccountAdapter):
    def save_user(self, request, user, form, commit=True):
        user = super().save_user(request, user, form, commit=False)
        user.username = user.email
        if commit:
            user.save()
        return user

    def get_login_redirect_url(self, request):
        profile = request.user.profile
        if not profile.has_selected_roles:
            return reverse('select_roles')
        if not profile.is_profile_complete:
            return reverse('profile_setup')
        return reverse('home')

    def get_signup_redirect_url(self, request):
        return reverse('select_roles')


# 3. THAY THẾ TOÀN BỘ LỚP CustomSocialAccountAdapter BẰNG KHỐI MỚI DƯỚI ĐÂY
class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    def pre_social_login(self, request, sociallogin):
        # Lấy user từ sociallogin object
        user = sociallogin.user
        
        # Cố gắng liên kết tài khoản nếu user đã tồn tại trong hệ thống
        if not sociallogin.is_existing:
            email = sociallogin.account.extra_data.get('email')
            if email:
                try:
                    # Tìm user trong hệ thống có cùng email
                    existing_user = User.objects.get(email__iexact=email)
                    # Kết nối tài khoản social này với user đã tồn tại
                    sociallogin.connect(request, existing_user)
                    user = existing_user # Cập nhật user để dùng cho bước sau
                except User.DoesNotExist:
                    pass

        # --- LOGIC ĐỒNG BỘ AVATAR ĐÃ ĐƯỢC CHUYỂN VÀO ĐÂY ---
        # Logic này sẽ chạy cho cả user mới và user cũ mỗi khi họ đăng nhập
        if user.pk: # Đảm bảo user đã tồn tại trong database
            # Lấy hoặc tạo profile cho user
            profile, created = Profile.objects.get_or_create(user=user)
            
            # Chỉ tải avatar về nếu họ CHƯA có avatar tự tải lên
            if not profile.avatar:
                avatar_url = sociallogin.account.get_avatar_url()
                if avatar_url:
                    try:
                        # Tải nội dung ảnh từ URL
                        response = requests.get(avatar_url, stream=True)
                        if response.status_code == 200:
                            # Tạo tên file duy nhất
                            file_name = f"{user.id}_avatar_google.jpg"
                            
                            # Lưu ảnh vào trường 'avatar' của Profile
                            profile.avatar.save(
                                file_name,
                                ContentFile(response.content),
                                save=True
                            )
                    except requests.exceptions.RequestException:
                        # Bỏ qua nếu có lỗi khi tải ảnh (ví dụ: mất mạng)
                        pass

    # Giữ nguyên hàm save_user này
    def save_user(self, request, sociallogin, form=None):
        user = sociallogin.user
        user.username = user.email
        sociallogin.save(request)
        return user