# users/forms.py

from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.contrib.auth.models import User

class CustomUserCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'email', 'first_name', 'last_name')

class CustomUserChangeForm(UserChangeForm):
    # Bỏ trường mật khẩu vì chúng ta có form đổi mật khẩu riêng
    password = None 
    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name')