# File: backend/organizations/forms.py

from django import forms
from tournaments.models import Tournament, Organization, Match, Goal, Card, Player, Team # Đảm bảo 'Team' được import
from .models import Organization
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError # Thêm import này
from tournaments.forms import PlayerCreationForm

class TournamentCreationForm(forms.ModelForm):
    class Meta:
        model = Tournament
        fields = [
            'name', 'status', 'region', 'start_date', 'end_date', 'image', 'rules',
            'bank_name', 'bank_account_number', 'bank_account_name', 'payment_qr_code'
        ]
        labels = {
            'name': 'Tên giải đấu',
            'status': 'Trạng thái giải đấu',
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

class OrganizationCreationForm(forms.ModelForm):
    class Meta:
        model = Organization
        fields = ['name', 'logo']
        labels = {
            'name': 'Tên đơn vị tổ chức của bạn',
            'logo': 'Logo (không bắt buộc)',
        }
     
class MemberInviteForm(forms.Form):
    email = forms.EmailField(
        label="Email của thành viên mới",
        widget=forms.EmailInput(attrs={'placeholder': 'nhapemail@vidu.com'})
    )

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if not User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("Không tìm thấy người dùng nào với email này.")
        return email


class MatchUpdateForm(forms.ModelForm):
    # === THÊM DÒNG NÀY VÀO ===
    team1 = forms.ModelChoiceField(queryset=Team.objects.none(), label="Đội 1")
    team2 = forms.ModelChoiceField(queryset=Team.objects.none(), label="Đội 2")

    class Meta:
        model = Match
        # === CẬP NHẬT DANH SÁCH fields ===
        fields = [
            'team1', 'team2', 'match_time', 'location', 
            'team1_score', 'team2_score', 
            'team1_penalty_score', 'team2_penalty_score', # Thêm 2 trường mới
            'livestream_url', 'referee', 'commentator', 'ticker_text'
        ]
        # === CẬP NHẬT labels VÀ widgets ===
        labels = {
            'match_time': 'Thời gian thi đấu',
            'location': 'Địa điểm',
            'team1_score': 'Tỉ số đội 1',
            'team2_score': 'Tỉ số đội 2',
            'team1_penalty_score': 'Tỉ số penalty đội 1',
            'team2_penalty_score': 'Tỉ số penalty đội 2',
            'livestream_url': 'Đường dẫn Livestream (YouTube)',
            'referee': 'Tên trọng tài',
            'commentator': 'Tên bình luận viên',
            'ticker_text': 'Dòng chữ chạy trên Livestream',
        }
        widgets = {
            'match_time': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }

    # === THÊM HÀM MỚI NÀY VÀO ===
    def clean(self):
        cleaned_data = super().clean()
        team1 = cleaned_data.get("team1")
        team2 = cleaned_data.get("team2")

        if team1 and team2 and team1 == team2:
            raise ValidationError("Hai đội trong một trận đấu không được trùng nhau.")
        
        return cleaned_data

class GoalForm(forms.ModelForm):
    player = forms.ModelChoiceField(queryset=Player.objects.none(), label="Cầu thủ ghi bàn")
    class Meta:
        model = Goal
        fields = ['player', 'minute', 'is_own_goal'] # Đã bao gồm trường mới
        labels = { 'minute': 'Phút ghi bàn' }

class CardForm(forms.ModelForm):
    player = forms.ModelChoiceField(queryset=Player.objects.none(), label="Cầu thủ nhận thẻ")
    class Meta:
        model = Card
        fields = ['player', 'card_type', 'minute']
        labels = {
            'card_type': 'Loại thẻ',
            'minute': 'Phút nhận thẻ'
        }

# === BẮT ĐẦU THÊM MỚI TẠI ĐÂY ===
class QuarterFinalCreationForm(forms.Form):
    qf1_team1 = forms.ModelChoiceField(queryset=Team.objects.none(), label="Tứ kết 1 - Đội 1")
    qf1_team2 = forms.ModelChoiceField(queryset=Team.objects.none(), label="Tứ kết 1 - Đội 2")
    qf1_datetime = forms.DateTimeField(
        label="Thời gian Tứ kết 1",
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        required=False
    )
    
    qf2_team1 = forms.ModelChoiceField(queryset=Team.objects.none(), label="Tứ kết 2 - Đội 1")
    qf2_team2 = forms.ModelChoiceField(queryset=Team.objects.none(), label="Tứ kết 2 - Đội 2")
    qf2_datetime = forms.DateTimeField(
        label="Thời gian Tứ kết 2",
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        required=False
    )

    qf3_team1 = forms.ModelChoiceField(queryset=Team.objects.none(), label="Tứ kết 3 - Đội 1")
    qf3_team2 = forms.ModelChoiceField(queryset=Team.objects.none(), label="Tứ kết 3 - Đội 2")
    qf3_datetime = forms.DateTimeField(
        label="Thời gian Tứ kết 3",
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        required=False
    )

    qf4_team1 = forms.ModelChoiceField(queryset=Team.objects.none(), label="Tứ kết 4 - Đội 1")
    qf4_team2 = forms.ModelChoiceField(queryset=Team.objects.none(), label="Tứ kết 4 - Đội 2")
    qf4_datetime = forms.DateTimeField(
        label="Thời gian Tứ kết 4",
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        required=False
    )

    def __init__(self, *args, **kwargs):
        qualified_teams_queryset = kwargs.pop('qualified_teams', None)
        super().__init__(*args, **kwargs)
        if qualified_teams_queryset is not None:
            # Gán queryset cho tất cả 8 trường chọn đội
            for i in range(1, 5):
                self.fields[f'qf{i}_team1'].queryset = qualified_teams_queryset
                self.fields[f'qf{i}_team2'].queryset = qualified_teams_queryset

    def clean(self):
        cleaned_data = super().clean()
        teams = [cleaned_data.get(f'qf{i}_team{j}') for i in range(1, 5) for j in range(1, 3)]
        
        # Lọc ra các giá trị None (trường hợp người dùng chưa chọn)
        valid_teams = [team for team in teams if team is not None]

        # Kiểm tra xem có đội nào được chọn nhiều hơn một lần không
        if len(set(valid_teams)) != len(valid_teams):
            raise ValidationError("Mỗi đội chỉ được chọn một lần. Vui lòng kiểm tra lại các cặp đấu Tứ kết.")
        return cleaned_data
# === KẾT THÚC THÊM MỚI ===


class SemiFinalCreationForm(forms.Form):
    sf1_team1 = forms.ModelChoiceField(queryset=Team.objects.none(), label="Bán kết 1 - Đội 1")
    sf1_team2 = forms.ModelChoiceField(queryset=Team.objects.none(), label="Bán kết 1 - Đội 2")
    sf1_datetime = forms.DateTimeField(
        label="Thời gian Bán kết 1",
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        required=False
    )
    sf2_team1 = forms.ModelChoiceField(queryset=Team.objects.none(), label="Bán kết 2 - Đội 1")
    sf2_team2 = forms.ModelChoiceField(queryset=Team.objects.none(), label="Bán kết 2 - Đội 2")
    sf2_datetime = forms.DateTimeField(
        label="Thời gian Bán kết 2",
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        required=False
    )

    def __init__(self, *args, **kwargs):
        # Sửa ở đây: chấp nhận cả qualified_teams và quarter_final_winners
        qualified_teams_queryset = kwargs.pop('qualified_teams', None)
        quarter_final_winners_queryset = kwargs.pop('quarter_final_winners', None)
        
        super().__init__(*args, **kwargs)
        
        # Ưu tiên lấy đội từ vòng Tứ kết, nếu không có thì mới lấy từ vòng bảng
        final_queryset = quarter_final_winners_queryset if quarter_final_winners_queryset is not None else qualified_teams_queryset

        if final_queryset is not None:
            self.fields['sf1_team1'].queryset = final_queryset
            self.fields['sf1_team2'].queryset = final_queryset
            self.fields['sf2_team1'].queryset = final_queryset
            self.fields['sf2_team2'].queryset = final_queryset

    def clean(self):
        cleaned_data = super().clean()
        teams = [
            cleaned_data.get('sf1_team1'),
            cleaned_data.get('sf1_team2'),
            cleaned_data.get('sf2_team1'),
            cleaned_data.get('sf2_team2'),
        ]
        valid_teams = [team for team in teams if team is not None]
        if len(set(valid_teams)) != len(valid_teams):
            raise ValidationError("Mỗi đội chỉ được chọn một lần. Vui lòng kiểm tra lại các cặp đấu Bán kết.")
        return cleaned_data

# === TẠO CẶP ĐẤU CHUNG KẾT ===
class FinalCreationForm(forms.Form):
    final_team1 = forms.ModelChoiceField(queryset=Team.objects.none(), label="Đội 1")
    final_team2 = forms.ModelChoiceField(queryset=Team.objects.none(), label="Đội 2")
    final_datetime = forms.DateTimeField(
        label="Thời gian Chung kết",
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        required=False
    )

    def __init__(self, *args, **kwargs):
        semi_final_winners_queryset = kwargs.pop('semi_final_winners', None)
        super().__init__(*args, **kwargs)
        if semi_final_winners_queryset is not None:
            self.fields['final_team1'].queryset = semi_final_winners_queryset
            self.fields['final_team2'].queryset = semi_final_winners_queryset

    def clean(self):
        cleaned_data = super().clean()
        team1 = cleaned_data.get('final_team1')
        team2 = cleaned_data.get('final_team2')
        if team1 and team2 and team1 == team2:
            raise ValidationError("Hai đội trong trận chung kết không được trùng nhau.")
        return cleaned_data     

# === Tranh Hạng Ba ===
class ThirdPlaceCreationForm(forms.Form):
    tp_team1 = forms.ModelChoiceField(queryset=Team.objects.none(), label="Đội 1")
    tp_team2 = forms.ModelChoiceField(queryset=Team.objects.none(), label="Đội 2")
    tp_datetime = forms.DateTimeField(
        label="Thời gian Tranh Hạng Ba",
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        required=False
    )

    def __init__(self, *args, **kwargs):
        semi_final_losers_queryset = kwargs.pop('semi_final_losers', None)
        super().__init__(*args, **kwargs)
        if semi_final_losers_queryset is not None:
            self.fields['tp_team1'].queryset = semi_final_losers_queryset
            self.fields['tp_team2'].queryset = semi_final_losers_queryset

    def clean(self):
        cleaned_data = super().clean()
        team1 = cleaned_data.get('tp_team1')
        team2 = cleaned_data.get('tp_team2')
        if team1 and team2 and team1 == team2:
            raise ValidationError("Hai đội trong trận tranh hạng Ba không được trùng nhau.")
        return cleaned_data

# === BTC TẠO TRẬN ĐẤU THỦ CÔNG ===
class MatchCreationForm(forms.ModelForm):
    team1 = forms.ModelChoiceField(queryset=Team.objects.none(), label="Đội 1")
    team2 = forms.ModelChoiceField(queryset=Team.objects.none(), label="Đội 2")

    class Meta:
        model = Match
        # Lấy các trường cần thiết để tạo một trận đấu mới
        fields = [
            'match_round', 'team1', 'team2', 'match_time', 'location'
        ]
        labels = {
            'match_round': 'Vòng đấu',
            'match_time': 'Thời gian thi đấu',
            'location': 'Địa điểm',
        }
        widgets = {
            'match_time': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        team1 = cleaned_data.get("team1")
        team2 = cleaned_data.get("team2")

        if team1 and team2 and team1 == team2:
            raise ValidationError("Hai đội trong một trận đấu không được trùng nhau.")
        
        return cleaned_data

class PlayerUpdateForm(PlayerCreationForm):
    """
    Form cho phép BTC chỉnh sửa thông tin cầu thủ.
    Kế thừa từ form gốc để tái sử dụng các trường đã có.
    """
    class Meta(PlayerCreationForm.Meta):
        pass # Giữ nguyên các thiết lập từ form cha        