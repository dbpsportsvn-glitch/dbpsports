# backend/organizations/forms.py

from django import forms
from tournaments.models import Match, Goal, Card, Player, Team, Announcement
from .models import Organization, ProfessionalReview, JobApplication
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from tournaments.forms import PlayerCreationForm
from tournaments.models import Substitution 
from users.models import Role

from tournaments.models import Sponsorship
from .models import JobPosting, JobApplication 
from users.models import Role 

#==============================================

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

# === BẮT ĐẦU THAY ĐỔI: TẠO CUSTOM FIELD ĐỂ HIỂN THỊ (C) ===
class PlayerChoiceFieldWithCaptain(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        """
        Ghi đè phương thức này để thêm (C) vào sau tên đội trưởng.
        """
        is_captain = obj.user and obj.team.captain == obj.user
        captain_indicator = " (C)" if is_captain else ""
        return f"{obj.full_name} (#{obj.jersey_number}){captain_indicator}"
# === KẾT THÚC THAY ĐỔI ===


class MatchUpdateForm(forms.ModelForm):
    team1 = forms.ModelChoiceField(queryset=Team.objects.none(), label="Đội 1")
    team2 = forms.ModelChoiceField(queryset=Team.objects.none(), label="Đội 2")

    class Meta:
        model = Match
        fields = [
            'team1', 'team2', 'match_time', 'location', 
            'team1_score', 'team2_score', 
            'team1_penalty_score', 'team2_penalty_score',
            'livestream_url', 'referee', 'commentator', 'ticker_text',
            'cover_photo', 'gallery_url'
        ]
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
            'cover_photo': 'Ảnh bìa trận đấu',
            'gallery_url': 'Link Album ảnh của trận đấu'
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

class GoalForm(forms.ModelForm):
    # === THAY ĐỔI: SỬ DỤNG CUSTOM FIELD MỚI ===
    player = PlayerChoiceFieldWithCaptain(queryset=Player.objects.none(), label="Cầu thủ ghi bàn")
    class Meta:
        model = Goal
        fields = ['player', 'minute', 'is_own_goal']
        labels = { 'minute': 'Phút ghi bàn' }

class CardForm(forms.ModelForm):
    # === THAY ĐỔI: SỬ DỤNG CUSTOM FIELD MỚI ===
    player = PlayerChoiceFieldWithCaptain(queryset=Player.objects.none(), label="Cầu thủ nhận thẻ")
    class Meta:
        model = Card
        fields = ['player', 'card_type', 'minute']
        labels = {
            'card_type': 'Loại thẻ',
            'minute': 'Phút nhận thẻ'
        }

# ... (các form khác giữ nguyên không đổi) ...
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
            for i in range(1, 5):
                self.fields[f'qf{i}_team1'].queryset = qualified_teams_queryset
                self.fields[f'qf{i}_team2'].queryset = qualified_teams_queryset

    def clean(self):
        cleaned_data = super().clean()
        teams = [cleaned_data.get(f'qf{i}_team{j}') for i in range(1, 5) for j in range(1, 3)]
        valid_teams = [team for team in teams if team is not None]
        if len(set(valid_teams)) != len(valid_teams):
            raise ValidationError("Mỗi đội chỉ được chọn một lần. Vui lòng kiểm tra lại các cặp đấu Tứ kết.")
        return cleaned_data

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
        qualified_teams_queryset = kwargs.pop('qualified_teams', None)
        quarter_final_winners_queryset = kwargs.pop('quarter_final_winners', None)
        super().__init__(*args, **kwargs)
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

class MatchCreationForm(forms.ModelForm):
    team1 = forms.ModelChoiceField(queryset=Team.objects.none(), label="Đội 1")
    team2 = forms.ModelChoiceField(queryset=Team.objects.none(), label="Đội 2")

    class Meta:
        model = Match
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


class PlayerUpdateForm(forms.ModelForm):
    class Meta:
        model = Player
        fields = [
            'full_name', 'jersey_number', 'position', 'specialty_position', 
            'date_of_birth', 'height', 'weight', 'preferred_foot', 
            'agent_contact', 'avatar', 'region', 'location_detail'
        ]
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
            'region': 'Khu vực hoạt động chính',
            'location_detail': 'Tỉnh / Thành phố',
        }
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
        }

class AnnouncementForm(forms.ModelForm):
    class Meta:
        model = Announcement
        fields = ['title', 'audience', 'content', 'is_published']
        labels = {
            'title': 'Tiêu đề thông báo',
            'audience': 'Đối tượng nhận',
            'content': 'Nội dung chi tiết',
            'is_published': 'Công khai ngay',
        }
        widgets = {
            'content': forms.Textarea(attrs={'rows': 10}),
        }
        help_texts = {
            'is_published': 'Bỏ chọn nếu đây là bản nháp và bạn muốn gửi sau.'
        }

# === Thay người ===
class SubstitutionForm(forms.ModelForm):
    player_in = PlayerChoiceFieldWithCaptain(queryset=Player.objects.none(), label="Cầu thủ vào sân")
    player_out = PlayerChoiceFieldWithCaptain(queryset=Player.objects.none(), label="Cầu thủ ra sân")
    
    class Meta:
        model = Substitution
        fields = ['player_in', 'player_out', 'minute']
        labels = {
            'minute': 'Phút thay người'
        }        

# === THÊM FORM MỚI VÀO CUỐI FILE ===
class TournamentStaffInviteForm(forms.Form):
    email = forms.EmailField(
        label="Email thành viên",
        widget=forms.EmailInput(attrs={'placeholder': 'nhapemail@vidu.com'})
    )
    role = forms.ModelChoiceField(
        # Loại bỏ các vai trò không phải chuyên môn
        queryset=Role.objects.exclude(id__in=['ORGANIZER', 'PLAYER', 'SPONSOR']),
        label="Vai trò chuyên môn"
    )

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if not User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("Không tìm thấy người dùng nào với email này.")
        return email        

# === THÊM FORM MỚI VÀO CUỐI FILE ===
class MatchMediaUpdateForm(forms.ModelForm):
    class Meta:
        model = Match
        fields = ['livestream_url', 'ticker_text', 'cover_photo', 'gallery_url']
        labels = {
            'livestream_url': 'Đường dẫn Livestream (YouTube)',
            'ticker_text': 'Dòng chữ chạy trên Livestream',
            'cover_photo': 'Ảnh bìa trận đấu',
            'gallery_url': 'Link Album ảnh của trận đấu'
        }            

# === From thi truong cong viec ===
class JobPostingForm(forms.ModelForm):
    class Meta:
        model = JobPosting
        fields = ['title', 'role_required', 'location_detail', 'budget', 'description']
        labels = {
            'title': 'Tiêu đề công việc',
            'role_required': 'Vai trò cần tuyển',
            'location_detail': 'Tỉnh / Thành phố', # <-- Thêm label mới
            'budget': 'Mức kinh phí (tùy chọn)',
            'description': 'Mô tả chi tiết công việc',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Giới hạn chỉ cho phép tuyển các vai trò chuyên môn
        self.fields['role_required'].queryset = Role.objects.exclude(id__in=['ORGANIZER', 'PLAYER'])

class JobApplicationUpdateForm(forms.ModelForm):
    class Meta:
        model = JobApplication
        fields = ['status']
        labels = {'status': 'Cập nhật trạng thái'}    

class JobApplicationForm(forms.ModelForm):
    class Meta:
        model = JobApplication
        fields = ['message']
        widgets = {
            'message': forms.Textarea(attrs={'rows': 4}),
        }            

# === DÁN FORM MỚI NÀY VÀO CUỐI FILE ===
class ProfessionalReviewForm(forms.ModelForm):
    class Meta:
        model = ProfessionalReview
        fields = ['rating', 'comment']
        labels = {
            'rating': 'Bạn đánh giá chất lượng công việc thế nào?',
            'comment': 'Viết một vài lời nhận xét (tùy chọn)',
        }
        widgets = {
            # Hiển thị các ngôi sao thay vì dropdown số
            'rating': forms.RadioSelect(attrs={'class': 'star-rating'}),
            'comment': forms.Textarea(attrs={'rows': 4}),
        }


class SponsorshipForm(forms.ModelForm):
    class Meta:
        model = Sponsorship
        # --- THÊM 'sponsor_name' VÀO ĐÂY ---
        fields = ['sponsor', 'sponsor_name', 'package_name', 'logo', 'website_url', 'order', 'is_active']
        labels = {
            'sponsor': 'Chọn Nhà tài trợ (nếu có tài khoản)',
            'sponsor_name': 'Tên Nhà tài trợ (nếu không có tài khoản)', # <-- Label mới
            'package_name': 'Tên gói tài trợ',
            'logo': 'Logo/Banner của Nhà tài trợ',
            'website_url': 'Đường dẫn trang web',
            'order': 'Thứ tự ưu tiên hiển thị',
            'is_active': 'Hiển thị công khai',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # --- THAY ĐỔI: CHO PHÉP TRƯỜNG sponsor KHÔNG BẮT BUỘC ---
        self.fields['sponsor'].required = False
        
        # Lọc danh sách người dùng chỉ bao gồm những ai có vai trò "Nhà tài trợ"
        try:
            sponsor_role = Role.objects.get(id='SPONSOR')
            self.fields['sponsor'].queryset = User.objects.filter(profile__roles=sponsor_role).order_by('username')
        except Role.DoesNotExist:
            self.fields['sponsor'].queryset = User.objects.none()

    # --- THÊM PHƯƠNG THỨC clean NÀY ĐỂ VALIDATE ---
    def clean(self):
        cleaned_data = super().clean()
        sponsor_account = cleaned_data.get('sponsor')
        sponsor_manual_name = cleaned_data.get('sponsor_name')

        if sponsor_account and sponsor_manual_name:
            raise ValidationError(
                "Lỗi: Bạn chỉ được chọn Nhà tài trợ có sẵn hoặc nhập tên thủ công, không được chọn cả hai.",
                code='invalid_sponsor_choice'
            )
        
        if not sponsor_account and not sponsor_manual_name:
            raise ValidationError(
                "Lỗi: Bạn phải chọn một Nhà tài trợ có sẵn hoặc nhập tên thủ công.",
                code='sponsor_required'
            )
        
        return cleaned_data        