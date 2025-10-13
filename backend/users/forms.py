# backend/users/forms.py

# Improt
from django import forms
from allauth.account.forms import SignupForm
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.contrib.auth.models import User
from .models import Profile # <-- Thêm import này
from django.utils.safestring import mark_safe  # <-- THÊM DÒNG NÀY
from django.urls import reverse_lazy         # <-- THÊM DÒNG NÀY
from .models import Profile, Role

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
    display_name = forms.CharField(
        label="Tên hiển thị của bạn", 
        max_length=150, 
        required=True,
        help_text="Tên này sẽ được sử dụng công khai trên toàn hệ thống."
    )

    class Meta:
        model = Profile
        fields = ['display_name', 'bio', 'location', 'experience', 'equipment', 
                  'referee_level', 'brand_website', 'sponsorship_interests']
        labels = {
            'bio': 'Giới thiệu bản thân',
            'location': 'Khu vực hoạt động',
            'experience': 'Số năm kinh nghiệm',
            'equipment': 'Thiết bị sở hữu',
            'referee_level': 'Cấp độ Trọng tài (nếu có)',
            'brand_website': 'Website Thương hiệu (nếu có)',
            'sponsorship_interests': 'Lĩnh vực quan tâm tài trợ (nếu có)',
        }
        widgets = {
            'bio': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if self.user:
            # Lấy tên đầy đủ hiện tại (nếu có) làm giá trị mặc định
            initial_name = self.user.get_full_name()
            if not initial_name:
                initial_name = self.user.get_username()
            self.fields['display_name'].initial = initial_name

    def save(self, commit=True):
        profile = super().save(commit=False)
        
        if self.user:
            # Lưu toàn bộ tên mới vào trường first_name và xóa last_name
            self.user.first_name = self.cleaned_data.get('display_name')
            self.user.last_name = '' # Xóa họ đi
            if commit:
                self.user.save()
        
        if commit:
            profile.save()
            
        return profile


# === THÊM FORM MỚI VÀO CUỐI FILE ===
class ProfileUpdateForm(forms.ModelForm):
    # === THÊM TRƯỜNG ROLES VÀO ĐÂY ===
    roles = forms.ModelMultipleChoiceField(
        queryset=Role.objects.all().order_by('order'),
        widget=forms.CheckboxSelectMultiple,
        label="Vai trò của bạn",
        required=True,
    )

    class Meta:
        model = Profile
        # === THÊM 'roles' VÀO ĐẦU DANH SÁCH fields ===
        fields = ['roles', 'bio', 'location', 'experience', 'equipment',
                  'referee_level', 'brand_website', 'sponsorship_interests']
        labels = {
            'bio': 'Giới thiệu bản thân (hiển thị công khai)',
            'location': 'Khu vực hoạt động chính',
            'experience': 'Số năm kinh nghiệm',
            'equipment': 'Thiết bị chuyên dụng (nếu có)',
            'referee_level': 'Cấp độ Trọng tài',
            'brand_website': 'Website Thương hiệu',
            'sponsorship_interests': 'Lĩnh vực quan tâm tài trợ',
        }
        widgets = {
            'bio': forms.Textarea(attrs={'rows': 4}),
        }        

    def clean_roles(self):
        roles = self.cleaned_data.get('roles')

        # === THÊM ĐOẠN KIỂM TRA NÀY VÀO ĐẦU PHƯƠNG THỨC ===
        if len(roles) > 2:
            raise forms.ValidationError("Bạn chỉ được chọn tối đa 2 vai trò.")
        # === KẾT THÚC THAY ĐỔI ===

        # Giữ lại logic kiểm tra số lần thay đổi vai trò
        if self.instance and self.instance.pk and self.instance.role_change_count >= 3:
            if set(self.instance.roles.all()) != set(roles):
                raise forms.ValidationError(
                    "Bạn đã hết số lần đổi vai trò. Vui lòng liên hệ Admin để được hỗ trợ."
                )
        
        return roles


# === FORM CHO SÂN BÓNG ===
class StadiumProfileForm(forms.ModelForm):
    """Form tạo/cập nhật hồ sơ Sân bóng"""
    class Meta:
        from .models import StadiumProfile
        model = StadiumProfile
        fields = [
            'stadium_name', 'logo', 'description',
            'address', 'region', 'location_detail', 'phone_number', 'email', 'website',
            'field_type', 'capacity', 'number_of_fields', 'amenities', 'rental_price_range', 'operating_hours',
            'bank_name', 'bank_account_number', 'bank_account_name', 'payment_qr_code'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
            'amenities': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'operating_hours': forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
            'address': forms.TextInput(attrs={'class': 'form-control'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }