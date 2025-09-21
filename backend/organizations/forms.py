from django import forms
from tournaments.models import Tournament
from .models import Organization
from django.contrib.auth.models import User

# === THAY THẾ FORM CŨ BẰNG PHIÊN BẢN HOÀN CHỈNH NÀY ===
class TournamentCreationForm(forms.ModelForm):
    class Meta:
        model = Tournament
        # Bao gồm tất cả các trường cần thiết ngay từ đầu
        fields = [
            'name', 'region', 'start_date', 'end_date', 'image', 'rules',
            'bank_name', 'bank_account_number', 'bank_account_name', 'payment_qr_code'
        ]
        labels = {
            'name': 'Tên giải đấu',
            'region': 'Khu vực tổ chức',
            'start_date': 'Ngày bắt đầu',
            'end_date': 'Ngày kết thúc',
            'image': 'Ảnh bìa / Banner giải đấu',
            'rules': 'Điều lệ & Quy định',
            'bank_name': 'Tên ngân hàng (cho đội tham gia chuyển khoản)',
            'bank_account_number': 'Số tài khoản',
            'bank_account_name': 'Tên chủ tài khoản',
            'payment_qr_code': 'Ảnh mã QR thanh toán (tùy chọn)',
        }
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


# === Tờ khai mời thành viên nhóm ===      
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
