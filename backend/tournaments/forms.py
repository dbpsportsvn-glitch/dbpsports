# tournaments/forms.py
from django import forms
from .models import Team, Player # Thêm Player vào đây

class TeamCreationForm(forms.ModelForm):
    class Meta:
        model = Team
        fields = ['name', 'coach_name', 'logo'] # Thêm 'logo' vào đây
        labels = {
            'name': 'Tên đội bóng',
            'coach_name': 'Tên huấn luyện viên (không bắt buộc)',
            'logo': 'Logo đội bóng',
        }

class PlayerCreationForm(forms.ModelForm):
    class Meta:
        model = Player
        fields = ['full_name', 'jersey_number', 'position', 'avatar'] # Thêm 'avatar'
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