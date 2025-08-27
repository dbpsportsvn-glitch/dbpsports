# tournaments/forms.py
from django import forms
from .models import Team, Player # Thêm Player vào đây

class TeamCreationForm(forms.ModelForm):
    class Meta:
        model = Team
        fields = ['name', 'coach_name']
        labels = {
            'name': 'Tên đội bóng',
            'coach_name': 'Tên huấn luyện viên (không bắt buộc)',
        }

class PlayerCreationForm(forms.ModelForm):
    class Meta:
        model = Player
        # Chúng ta không cần trường 'team' vì nó sẽ được tự động gán
        fields = ['full_name', 'jersey_number', 'position']
        labels = {
            'full_name': 'Họ và tên cầu thủ',
            'jersey_number': 'Số áo',
            'position': 'Vị trí',
        }        