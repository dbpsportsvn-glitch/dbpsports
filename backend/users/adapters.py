# backend/users/adapters.py
from allauth.account.adapter import DefaultAccountAdapter
from allauth.exceptions import ImmediateHttpResponse
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.account.utils import perform_login
from django.contrib.auth import get_user_model
from django.shortcuts import redirect
from django.contrib import messages

#------------------------------------

User = get_user_model()

# === THÊM CLASS MỚI NÀY VÀO ĐẦU FILE ===
class CustomAccountAdapter(DefaultAccountAdapter):
    def save_user(self, request, user, form, commit=True):
        """
        Ghi đè phương thức này để tự động gán username bằng email
        khi người dùng đăng ký tài khoản thông thường.
        """
        # Gọi phương thức gốc để lấy user object
        user = super().save_user(request, user, form, commit=False)
        # Gán username bằng email
        user.username = user.email
        # Lưu lại user
        if commit:
            user.save()
        return user

class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    def pre_social_login(self, request, sociallogin):
        """
        Can thiệp trước khi quá trình đăng nhập social hoàn tất.

        Kiểm tra xem email từ tài khoản social (Google) đã tồn tại trong
        hệ thống hay chưa. Nếu đã tồn tại, hãy liên kết tài khoản social này
        với người dùng hiện có và đăng nhập cho họ.
        """
        # Bỏ qua nếu tài khoản social này đã được kết nối với người dùng nào đó
        if sociallogin.is_existing:
            return

        # Lấy email từ dữ liệu của Google
        if sociallogin.account.extra_data:
            email = sociallogin.account.extra_data.get('email', '').lower()
            if email:
                # Tìm xem có người dùng nào trong hệ thống có email này không
                try:
                    user = User.objects.get(email__iexact=email)
                    
                    # Nếu tìm thấy, kết nối tài khoản social với người dùng đó
                    sociallogin.connect(request, user)
                    
                    # Thực hiện đăng nhập cho người dùng
                    perform_login(request, user, email_verification='none')
                    messages.success(request, "Đăng nhập thành công! Tài khoản Google của bạn đã được liên kết.")
                    
                    # Dừng quá trình và chuyển hướng ngay lập tức
                    raise ImmediateHttpResponse(redirect('dashboard'))

                except User.DoesNotExist:
                    # Nếu không tìm thấy email, tiếp tục quy trình đăng ký bình thường
                    pass

    def save_user(self, request, sociallogin, form=None):
        """
        Ghi đè phương thức lưu người dùng để đảm bảo username là duy nhất.
        
        Phương thức này được gọi khi tạo một người dùng mới từ social login.
        Chúng ta sẽ đặt username của người dùng bằng email của họ để đảm bảo
        tính duy nhất, vì email đã được cấu hình là duy nhất.
        """
        # Lấy đối tượng user đã được allauth tạo ra (nhưng chưa lưu)
        user = sociallogin.user
        
        # Gán username bằng email của người dùng
        # Allauth đã tự động điền email từ thông tin của Google
        user.username = user.email
        
        # Bây giờ, gọi phương thức lưu của sociallogin, lúc này username đã hợp lệ
        sociallogin.save(request)
        
        return user