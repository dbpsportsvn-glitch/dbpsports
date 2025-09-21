from django import forms
from tournaments.models import Tournament, Organization, Match
from .models import Organization
from django.contrib.auth.models import User

class TournamentCreationForm(forms.ModelForm):
    class Meta:
        model = Tournament
        # Thêm 'status' vào danh sách fields
        fields = [
            'name', 'status', 'region', 'start_date', 'end_date', 'image', 'rules',
            'bank_name', 'bank_account_number', 'bank_account_name', 'payment_qr_code'
        ]
        labels = {
            'name': 'Tên giải đấu',
            'status': 'Trạng thái giải đấu', # Thêm nhãn cho status
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

# === BẮT ĐẦU THÊM MỚI ===
class MatchUpdateForm(forms.ModelForm):
    class Meta:
        model = Match
        fields = [
            'team1_score', 'team2_score', 'livestream_url', 
            'referee', 'commentator', 'ticker_text'
        ]
        labels = {
            'team1_score': 'Tỉ số đội 1',
            'team2_score': 'Tỉ số đội 2',
            'livestream_url': 'Đường dẫn Livestream (YouTube)',
            'referee': 'Tên trọng tài',
            'commentator': 'Tên bình luận viên',
            'ticker_text': 'Dòng chữ chạy trên Livestream',
        }        
