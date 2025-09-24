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