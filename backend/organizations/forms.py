# organizations/forms.py
from django import forms
from tournaments.models import Tournament
from .models import Organization
from django.contrib.auth.models import User

class TournamentCreationForm(forms.ModelForm):
    class Meta:
        model = Tournament
        # Chỉ cho phép người dùng điền các trường này
        fields = ['name', 'start_date', 'end_date', 'image', 'rules']
        labels = {
            'name': 'Tên giải đấu',
            'start_date': 'Ngày bắt đầu',
            'end_date': 'Ngày kết thúc',
            'image': 'Ảnh bìa / Banner giải đấu',
            'rules': 'Điều lệ & Quy định',
        }
        # Thêm widget để có thể chọn ngày tháng dễ dàng
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
            'rules': forms.Textarea(attrs={'rows': 5}),
        }

# === BẮT ĐẦU THÊM MỚI ===
class OrganizationCreationForm(forms.ModelForm):
    class Meta:
        model = Organization
        fields = ['name', 'logo']
        labels = {
            'name': 'Tên đơn vị tổ chức của bạn',
            'logo': 'Logo (không bắt buộc)',
        }
# === KẾT THÚC THÊM MỚI ===      

class MemberInviteForm(forms.Form):
    email = forms.EmailField(
        label="Email của thành viên mới",
        widget=forms.EmailInput(attrs={'placeholder': 'nhapemail@vidu.com'})
    )

    def clean_email(self):
        email = self.cleaned_data.get('email')
        # Kiểm tra xem có tài khoản nào dùng email này không
        if not User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("Không tìm thấy người dùng nào với email này.")
        return email