# tournaments/forms.py
from django import forms
from .models import Team, Player, Comment, Tournament

# === BẮT ĐẦU THAY THẾ TỪ ĐÂY ===
class TeamCreationForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        # Lấy user từ view và xóa khỏi kwargs trước khi gọi super()
        self.user = kwargs.pop('user', None)
        super(TeamCreationForm, self).__init__(*args, **kwargs)

    class Meta:
        model = Team
        fields = ['name', 'coach_name', 'logo']
        labels = {
            'name': 'Tên đội bóng',
            'coach_name': 'Tên huấn luyện viên (không bắt buộc)',
            'logo': 'Logo đội bóng',
        }
    
    def clean_name(self):
        name = self.cleaned_data.get('name')
        # Chỉ kiểm tra nếu user đã được truyền vào
        if self.user and Team.objects.filter(captain=self.user, name__iexact=name).exists():
            raise forms.ValidationError("Bạn đã có một đội với tên này. Vui lòng chọn một tên khác.")
        return name

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

# === BẮT ĐẦU THAY THẾ TỪ ĐÂY ===
class ScheduleGenerationForm(forms.Form):
    WEEKDAY_CHOICES = [
        (6, 'Chủ Nhật'),
        (5, 'Thứ Bảy'),
        (4, 'Thứ Sáu'),
        (3, 'Thứ Năm'),
        (2, 'Thứ Tư'),
        (1, 'Thứ Ba'),
        (0, 'Thứ Hai'),
    ]
    STRATEGY_CHOICES = [
        ('MIXED', 'Xếp xen kẽ (ưu tiên lấp đầy lịch)'),
        ('ROTATIONAL', 'Xếp xoay vòng (mỗi tuần một bảng)'),
    ]

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
    weekdays = forms.MultipleChoiceField(
        choices=WEEKDAY_CHOICES,
        widget=forms.CheckboxSelectMultiple,
        label="Chỉ xếp lịch vào các ngày",
        initial=[5, 6], # Mặc định chọn Thứ 7, Chủ Nhật
        required=True
    )
    matches_per_week = forms.IntegerField(
        label="Số trận tối đa mỗi tuần (để trống nếu không giới hạn)",
        min_value=1,
        required=False,
        help_text="Hữu ích khi bạn muốn giãn lịch thi đấu."
    )
    scheduling_strategy = forms.ChoiceField(
        choices=STRATEGY_CHOICES,
        label="Chiến lược xếp lịch",
        initial='MIXED',
        widget=forms.RadioSelect
    )
# === KẾT THÚC THAY THẾ TẠI ĐÂY ===

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