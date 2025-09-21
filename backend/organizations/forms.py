# organizations/forms.py
from django import forms
from tournaments.models import Tournament

class TournamentCreationForm(forms.ModelForm):
    class Meta:
        model = Tournament
        # Chỉ cho phép người dùng điền các trường này
        fields = ['name', 'start_date', 'end_date', 'image', 'rules']
        labels = {
            'name': 'Tên giải đấu',
            'start_date': 'Ngày bắt đầu',
            'end_date': 'Ngày kết thúc',
            'image': 'Ảnh bìa / Banner giải đấu',
            'rules': 'Điều lệ & Quy định',
        }
        # Thêm widget để có thể chọn ngày tháng dễ dàng
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
            'rules': forms.Textarea(attrs={'rows': 5}),
        }