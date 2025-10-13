# tournaments/forms.py
from django import forms
from .models import Team, Player, Comment, Tournament, TeamRegistration
from .models import MatchNote, TournamentBudget, RevenueItem, ExpenseItem
from .models import PlayerTransfer, CoachRecruitment
from colorfield.widgets import ColorWidget
from users.models import CoachProfile

# === BẮT ĐẦU THAY THẾ TỪ ĐÂY ===
class TeamCreationForm(forms.ModelForm):
    # Thêm trường để chọn huấn luyện viên
    coach = forms.ModelChoiceField(
        queryset=CoachProfile.objects.filter(team__isnull=True, is_available=True),
        required=False,
        label='Chọn Huấn luyện viên',
        help_text='Chọn HLV từ danh sách những người đang tìm đội (để trống nếu không có)',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    def __init__(self, *args, **kwargs):
        # Lấy user từ view và xóa khỏi kwargs trước khi gọi super()
        self.user = kwargs.pop('user', None)
        super(TeamCreationForm, self).__init__(*args, **kwargs)
        
        # Cập nhật queryset cho coach (HLV chưa có đội)
        self.fields['coach'].queryset = CoachProfile.objects.filter(
            team__isnull=True, 
            is_available=True
        )

    class Meta:
        model = Team
        fields = ['name', 'coach', 'coach_name', 'logo', 'kit_home_color', 'kit_away_color']
        labels = {
            'name': 'Tên đội bóng',
            'coach_name': 'Hoặc nhập tên HLV (nếu không có trong danh sách)',
            'logo': 'Logo đội bóng',
            'kit_home_color': 'Màu áo sân nhà',
            'kit_away_color': 'Màu áo sân khách',
        }
        # === THÊM KHỐI WIDGETS NÀY VÀO ===
        widgets = {
            'kit_home_color': ColorWidget,
            'kit_away_color': ColorWidget,
        }
    
    def clean_name(self):
        name = self.cleaned_data.get('name')
        # Chỉ kiểm tra nếu user đã được truyền vào
        if self.user and Team.objects.filter(captain=self.user, name__iexact=name).exists():
            raise forms.ValidationError("Bạn đã có một đội với tên này. Vui lòng chọn một tên khác.")
        return name
    
    def clean(self):
        cleaned_data = super().clean()
        coach = cleaned_data.get('coach')
        coach_name = cleaned_data.get('coach_name')
        
        # Kiểm tra không được điền cả hai
        if coach and coach_name:
            raise forms.ValidationError("Chỉ chọn một trong hai: Chọn HLV từ danh sách hoặc nhập tên HLV.")
        
        return cleaned_data

class PlayerCreationForm(forms.ModelForm):
    class Meta:
        model = Player
        fields = ['full_name', 'jersey_number', 'position', 'specialty_position', 
                  'date_of_birth', 'height', 'weight', 'preferred_foot', 
                  'agent_contact', 'avatar', 'donation_qr_code', 'region', 
                  'location_detail'] # << Thêm 'location_detail'
        labels = {
            'full_name': 'Họ và tên cầu thủ',
            'jersey_number': 'Số áo',
            'position': 'Vị trí đăng ký',
            'specialty_position': 'Vị trí sở trường',
            'date_of_birth': 'Ngày sinh',
            'height': 'Chiều cao (cm)',
            'weight': 'Cân nặng (kg)',
            'preferred_foot': 'Chân thuận',
            'agent_contact': 'Thông tin liên hệ (đại diện)',
            'avatar': 'Ảnh đại diện / Giấy tờ',
            'donation_qr_code': 'Mã QR nhận ủng hộ (tùy chọn)',
            'region': 'Khu vực',
            'location_detail': 'Tỉnh / Thành phố',
        }
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
        }

    # === THÊM PHƯƠNG THỨC NÀY VÀO ĐỂ KIỂM TRA SỐ ÁO ===
    def clean_jersey_number(self):
        """
        Đây là một phương thức đặc biệt của Django Form.
        Nó sẽ tự động được gọi để kiểm tra riêng cho trường 'jersey_number'.
        """
        # Lấy dữ liệu số áo mà người dùng đã nhập
        number = self.cleaned_data.get('jersey_number')
        
        # Kiểm tra nếu số áo tồn tại (người dùng có nhập)
        if number is not None:
            # Nếu số áo không nằm trong khoảng 1-99
            if not (1 <= number <= 99):
                # Gửi trả về một lỗi xác thực với thông báo thân thiện
                raise forms.ValidationError("Số áo phải là một số trong khoảng từ 1 đến 99.")
        
        # Nếu không có lỗi, trả về dữ liệu đã được làm sạch
        return number


class PaymentProofForm(forms.ModelForm):
    class Meta:
        model = TeamRegistration  # <-- THAY ĐỔI QUAN TRỌNG NHẤT
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
    # === THÊM LỰA CHỌN MỚI "PRIORITIZED" VÀO ĐÂY ===
    STRATEGY_CHOICES = [
        ('PRIORITIZED', 'Ưu tiên theo thứ tự Bảng (A->B->C)'),
        ('MIXED', 'Xếp xen kẽ (lấp đầy lịch)'),
        ('ROTATIONAL', 'Xếp xoay vòng (mỗi tuần một bảng)'),
    ]

    start_date = forms.DateField(
        label="Ngày bắt đầu thi đấu",
        widget=forms.DateInput(attrs={'type': 'date'}),
        help_text="Chọn ngày diễn ra trận đấu đầu tiên."
    )
    time_slots = forms.CharField(
        label="Các khung giờ trong ngày (cách nhau bằng dấu phẩy)",
        initial="08:00, 10:00, 14:30, 16:30",
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
        initial=[5, 6],
        required=True
    )
    matches_per_week = forms.IntegerField(
        label="Tổng số trận tối đa mỗi tuần (để trống nếu không giới hạn)",
        min_value=1,
        required=False,
        help_text="Hữu ích khi bạn muốn giãn lịch thi đấu."
    )
    max_matches_per_team_per_week = forms.IntegerField(
        label="Số trận tối đa MỖI ĐỘI trong một tuần (để trống nếu không giới hạn)",
        min_value=1,
        required=False,
        help_text="Ví dụ: nhập 1 để đảm bảo không đội nào phải đá quá 1 trận/tuần."
    )
    # === THÊM TRƯỜNG MỚI ĐỂ GIỚI HẠN THEO BẢNG ===
    matches_per_group_per_week = forms.CharField(
        label="Giới hạn trận đấu MỖI BẢNG trong tuần (tùy chọn)",
        required=False,
        help_text="Định dạng: Tên Bảng:Số trận, Tên Bảng:Số trận. Ví dụ: Bảng A:2, Bảng B:1, Bảng C:1"
    )
    scheduling_strategy = forms.ChoiceField(
        choices=STRATEGY_CHOICES,
        label="Chiến lược xếp lịch",
        initial='PRIORITIZED', # <-- Đặt chiến lược mới làm mặc định
        widget=forms.RadioSelect
    )

    # === THÊM TÙY CHỌN LƯỢT ĐI/LƯỢT VỀ ===
    ROUND_ROBIN_LEGS = [
        (1, 'Vòng tròn 1 lượt (single round-robin)'),
        (2, 'Vòng tròn 2 lượt (lượt đi & lượt về)'),
    ]
    round_robin_legs = forms.ChoiceField(
        choices=ROUND_ROBIN_LEGS,
        label='Hình thức vòng tròn',
        initial=1,
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

# === THÊM FORM MỚI VÀO CUỐI FILE ===
class TournamentForm(forms.ModelForm):
    class Meta:
        model = Tournament
        fields = [
            'name', 'status', 'format', 'region', 'location_detail', 'start_date', 'end_date', 'image', 'rules',
            'registration_fee', 'bank_name', 'bank_account_number', 'bank_account_name', 'payment_qr_code'
        ]
        labels = {
            'name': 'Tên giải đấu',
            'status': 'Trạng thái giải đấu',
            'format': 'Thể thức thi đấu',
            'region': 'Khu vực tổ chức',
            'start_date': 'Ngày bắt đầu',
            'location_detail': 'Tỉnh / Thành phố',
            'end_date': 'Ngày kết thúc',
            'image': 'Ảnh bìa / Banner giải đấu',
            'rules': 'Điều lệ & Quy định',
            'registration_fee': 'Phí đăng ký (VNĐ)',
            'bank_name': 'Tên ngân hàng (cho đội tham gia chuyển khoản)',
            'bank_account_number': 'Số tài khoản',
            'bank_account_name': 'Tên chủ tài khoản',
            'payment_qr_code': 'Ảnh mã QR thanh toán (tùy chọn)',
        }
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
            'rules': forms.Textarea(attrs={'rows': 5}),
            'registration_fee': forms.NumberInput(attrs={
                'min': '0',
                'step': '100000',
                'placeholder': 'Nhập phí đăng ký cho mỗi đội'
            }),
        }        

class CommentatorNoteForm(forms.ModelForm):
    class Meta:
        model = MatchNote
        fields = ['commentator_notes_team1', 'commentator_notes_team2']
        widgets = {
            'commentator_notes_team1': forms.Textarea(attrs={'rows': 15}),
            'commentator_notes_team2': forms.Textarea(attrs={'rows': 15}),
        }      

class CaptainNoteForm(forms.ModelForm):
    class Meta:
        model = MatchNote
        fields = ['captain_note']
        labels = {
            'captain_note': 'Nội dung ghi chú'
        }
        widgets = {
            'captain_note': forms.Textarea(attrs={'rows': 8}),
        }     

# === THÊM FORM MỚI NÀY VÀO CUỐI TỆP ===
class PlayerTransferForm(forms.ModelForm):
    class Meta:
        model = PlayerTransfer
        # === THÊM 'offer_amount' VÀO ĐÂY ===
        fields = ['transfer_type', 'loan_end_date', 'offer_amount']
        labels = {
            'transfer_type': 'Loại hình đề nghị',
            'loan_end_date': 'Ngày kết thúc cho mượn',
            'offer_amount': 'Phí đề nghị (VNĐ)',
        }
        widgets = {
            'transfer_type': forms.RadioSelect,
            'loan_end_date': forms.DateInput(attrs={'type': 'date'}),
            # === THÊM WIDGET CHO TRƯỜNG MỚI ===
            'offer_amount': forms.NumberInput(attrs={'placeholder': 'Nhập số tiền bạn đề nghị'}),
        }


# ===== FORMS CHO HỆ THỐNG QUẢN LÝ TÀI CHÍNH =====

class TournamentBudgetForm(forms.ModelForm):
    """Form tạo/cập nhật ngân sách giải đấu"""
    class Meta:
        model = TournamentBudget
        fields = ['initial_budget']
        widgets = {
            'initial_budget': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nhập ngân sách ban đầu (VNĐ)',
                'min': '0'
            })
        }
        labels = {
            'initial_budget': 'Ngân sách ban đầu (VNĐ)'
        }


class RevenueItemForm(forms.ModelForm):
    """Form thêm khoản thu"""
    class Meta:
        model = RevenueItem
        fields = ['category', 'description', 'amount', 'date', 'notes']
        widgets = {
            'category': forms.Select(attrs={'class': 'form-control'}),
            'description': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Mô tả khoản thu'
            }),
            'amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Số tiền (VNĐ)',
                'min': '0'
            }),
            'date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Ghi chú thêm (không bắt buộc)'
            })
        }
        labels = {
            'category': 'Danh mục',
            'description': 'Mô tả',
            'amount': 'Số tiền (VNĐ)',
            'date': 'Ngày',
            'notes': 'Ghi chú'
        }


class ExpenseItemForm(forms.ModelForm):
    """Form thêm khoản chi"""
    class Meta:
        model = ExpenseItem
        fields = ['category', 'description', 'amount', 'date', 'notes', 'receipt_image']
        widgets = {
            'category': forms.Select(attrs={'class': 'form-control'}),
            'description': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Mô tả khoản chi'
            }),
            'amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Số tiền (VNĐ)',
                'min': '0'
            }),
            'date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Ghi chú thêm (không bắt buộc)'
            }),
            'receipt_image': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            })
        }
        labels = {
            'category': 'Danh mục',
            'description': 'Mô tả',
            'amount': 'Số tiền (VNĐ)',
            'date': 'Ngày',
            'notes': 'Ghi chú',
            'receipt_image': 'Hóa đơn (tùy chọn)'
        }


class BudgetQuickAddForm(forms.Form):
    """Form thêm nhanh khoản thu/chi"""
    TYPE_CHOICES = [
        ('revenue', 'Khoản thu'),
        ('expense', 'Khoản chi'),
    ]
    
    type = forms.ChoiceField(
        choices=TYPE_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Loại'
    )
    description = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Mô tả'
        }),
        label='Mô tả'
    )
    amount = forms.DecimalField(
        max_digits=15,
        decimal_places=0,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Số tiền (VNĐ)',
            'min': '0'
        }),
        label='Số tiền (VNĐ)'
    )
    date = forms.DateField(
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        }),
        label='Ngày'
    )


# === FORMS CHO HUẤN LUYỆN VIÊN ===

class CoachProfileForm(forms.ModelForm):
    """Form tạo/cập nhật hồ sơ huấn luyện viên"""
    class Meta:
        model = CoachProfile
        fields = [
            'full_name', 'avatar', 'bio', 'date_of_birth',
            'years_of_experience', 'coaching_license', 'specialization',
            'achievements', 'previous_teams',
            'phone_number', 'email',
            'region', 'location_detail',
            'is_available'
        ]
        widgets = {
            'bio': forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
            'achievements': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'previous_teams': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'date_of_birth': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        }


class CoachRecruitmentForm(forms.ModelForm):
    """Form gửi lời mời chiêu mộ huấn luyện viên"""
    class Meta:
        model = CoachRecruitment
        fields = ['salary_offer', 'contract_duration', 'message']
        labels = {
            'salary_offer': 'Mức lương đề nghị (VNĐ)',
            'contract_duration': 'Thời hạn hợp đồng',
            'message': 'Lời nhắn'
        }
        widgets = {
            'salary_offer': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ví dụ: 5000000'
            }),
            'contract_duration': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ví dụ: 1 năm, 6 tháng...'
            }),
            'message': forms.Textarea(attrs={
                'rows': 4,
                'class': 'form-control',
                'placeholder': 'Giới thiệu về đội bóng và kế hoạch phát triển...'
            })
        }