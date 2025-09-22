# tournaments/forms.py
from django import forms
from .models import Team, Player, Comment, Tournament

class TeamCreationForm(forms.ModelForm):
    class Meta:
        model = Team
        fields = ['name', 'coach_name', 'logo']
        labels = {
            'name': 'Tên đội bóng',
            'coach_name': 'Tên huấn luyện viên (không bắt buộc)',
            'logo': 'Logo đội bóng',
        }

class PlayerCreationForm(forms.ModelForm):
    class Meta:
        model = Player
        fields = ['full_name', 'jersey_number', 'position', 'avatar']
        labels = {
            'full_name': 'Họ và tên cầu thủ',
            'jersey_number': 'Số áo',
            'position': 'Vị trí',
            'avatar': 'Ảnh đại diện / Giấy tờ',
        }

class PaymentProofForm(forms.ModelForm):
    class Meta:
        model = Team
        fields = ['payment_proof']
        labels = {
            'payment_proof': 'Tải lên ảnh chụp màn hình hóa đơn chuyển khoản',
        }

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['text']
        widgets = {
            'text': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Viết bình luận của bạn...'
            })
        }
        labels = { 'text': '' }

class ScheduleGenerationForm(forms.Form):
    start_date = forms.DateField(
        label="Ngày bắt đầu thi đấu",
        widget=forms.DateInput(attrs={'type': 'date'}),
        help_text="Chọn ngày diễn ra trận đấu đầu tiên."
    )
    time_slots = forms.CharField(
        label="Các khung giờ trong ngày (cách nhau bằng dấu phẩy)",
        initial="08:00, 10:00, 14:00, 16:00",
        help_text="Ví dụ: 08:00, 15:00, 19:30"
    )
    locations = forms.CharField(
        label="Các sân thi đấu (cách nhau bằng dấu phẩy)",
        initial="Sân 1, Sân 2",
        help_text="Ví dụ: Sân Cỏ Nhân tạo A, Sân Vận động B"
    )
    rest_days = forms.IntegerField(
        label="Số ngày nghỉ tối thiểu giữa 2 trận của một đội",
        initial=1,
        min_value=0,
        help_text="Ví dụ: nhập 1 để đảm bảo một đội không phải đá 2 ngày liên tiếp."
    )

class GalleryURLForm(forms.ModelForm):
    class Meta:
        model = Tournament
        fields = ['gallery_url']
        labels = {
            'gallery_url': 'Hoặc dán link album ảnh đầy đủ (Google Drive, Photos, etc.)'
        }
        widgets = {
            'gallery_url': forms.URLInput(attrs={'placeholder': 'https://...'})
        }