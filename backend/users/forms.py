# backend/users/forms.py

# Improt
from django import forms
from allauth.account.forms import SignupForm
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.contrib.auth.models import User
from .models import Profile # <-- Thêm import này
from django.utils.safestring import mark_safe  # <-- THÊM DÒNG NÀY
from django.urls import reverse_lazy         # <-- THÊM DÒNG NÀY

# ===============================

# === THÊM CLASS MỚI NÀY VÀO ===
class CustomSignupForm(SignupForm):
    # Định nghĩa trường 'terms' trước, nhưng với một label tạm thời
    terms = forms.BooleanField(
        required=True,
        initial=False,
        label="Đồng ý với điều khoản", # Label này sẽ được thay thế bên dưới
        error_messages={'required': 'Bạn phải đồng ý với các điều khoản để tiếp tục.'}
    )

    def __init__(self, *args, **kwargs):
        # Gọi __init__ của lớp cha trước tiên
        super(CustomSignupForm, self).__init__(*args, **kwargs)
        
        # Bây giờ, khi form đã được khởi tạo, chúng ta mới tạo label chứa link
        terms_label_with_links = mark_safe(
            'Tôi đã đọc và đồng ý với <a href="{}" target="_blank">Điều khoản Dịch vụ</a> và <a href="{}" target="_blank">Chính sách Quyền riêng tư</a>.'
            .format(reverse_lazy('terms_of_service'), reverse_lazy('privacy_policy'))
        )
        
        # Cập nhật lại label của trường 'terms'
        self.fields['terms'].label = terms_label_with_links

        self.fields['password1'].help_text = 'Mật khẩu phải có ít nhất 8 ký tự, không quá giống email và không phải là mật khẩu thông dụng.'

    def save(self, request):
        user = super(CustomSignupForm, self).save(request)
        return user

class CustomUserCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'email', 'first_name', 'last_name')

class CustomUserChangeForm(UserChangeForm):
    password = None 
    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name')

# === THÊM FORM MỚI Ở ĐÂY ===
class AvatarUpdateForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['avatar']
        labels = {
            'avatar': 'Chọn ảnh mới'
        }

class NotificationPreferencesForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['notify_match_results', 'notify_new_teams', 'notify_draw_results', 'notify_schedule_updates']
        labels = {
            'notify_match_results': 'Khi có kết quả trận đấu mới',
            'notify_new_teams': 'Khi có đội mới được duyệt tham gia giải',
            'notify_draw_results': 'Khi giải đấu bốc thăm chia bảng xong',
            'notify_schedule_updates': 'Khi có lịch thi đấu mới được tạo',
        }

# === FORM MỚI CHO TRANG SETUP PROFILE ===
class ProfileSetupForm(forms.ModelForm):
    first_name = forms.CharField(label="Tên", max_length=150, required=True)
    last_name = forms.CharField(label="Họ", max_length=150, required=True)

    class Meta:
        model = Profile
        fields = ['first_name', 'last_name', 'bio', 'location', 'experience', 'equipment']
        labels = {
            'bio': 'Giới thiệu bản thân',
            'location': 'Khu vực hoạt động',
            'experience': 'Số năm kinh nghiệm',
            'equipment': 'Thiết bị sở hữu',
        }
        widgets = {
            'bio': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        # Lấy 'user' từ view để điền giá trị ban đầu
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Điền tên từ user model vào form
        if self.user:
            self.fields['first_name'].initial = self.user.first_name
            self.fields['last_name'].initial = self.user.last_name

    def save(self, commit=True):
        # Lưu các trường của Profile model
        profile = super().save(commit=False)
        
        # Cập nhật first_name và last_name cho User model
        if self.user:
            self.user.first_name = self.cleaned_data.get('first_name')
            self.user.last_name = self.cleaned_data.get('last_name')
            if commit:
                self.user.save()
        
        if commit:
            profile.save()
            
        return profile

# === THÊM FORM MỚI VÀO CUỐI FILE ===
class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['bio', 'location', 'experience', 'equipment']
        labels = {
            'bio': 'Giới thiệu bản thân (hiển thị công khai)',
            'location': 'Khu vực hoạt động chính',
            'experience': 'Số năm kinh nghiệm',
            'equipment': 'Thiết bị chuyên dụng (nếu có)',
        }
        widgets = {
            'bio': forms.Textarea(attrs={'rows': 4}),
        }        