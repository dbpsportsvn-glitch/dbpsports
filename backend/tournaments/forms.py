# tournaments/forms.py
from django import forms
# Sửa dòng import này để thêm "Comment"
from .models import Team, Player, Comment 

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

# >>> THÊM FORM MỚI NÀY VÀO CUỐI FILE <<<
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
        labels = {
            'text': '' # Ẩn nhãn của trường text
        }      