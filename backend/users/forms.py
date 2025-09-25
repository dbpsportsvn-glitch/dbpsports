# backend/users/forms.py

from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.contrib.auth.models import User
from .models import Profile # <-- Thêm import này

class CustomUserCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'email', 'first_name', 'last_name')

class CustomUserChangeForm(UserChangeForm):
    password = None 
    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name')

# === THÊM FORM MỚI Ở ĐÂY ===
class AvatarUpdateForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['avatar']
        labels = {
            'avatar': 'Chọn ảnh mới'
        }

class NotificationPreferencesForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['notify_match_results', 'notify_new_teams', 'notify_draw_results', 'notify_schedule_updates']
        labels = {
            'notify_match_results': 'Khi có kết quả trận đấu mới',
            'notify_new_teams': 'Khi có đội mới được duyệt tham gia giải',
            'notify_draw_results': 'Khi giải đấu bốc thăm chia bảng xong',
            'notify_schedule_updates': 'Khi có lịch thi đấu mới được tạo',
        }