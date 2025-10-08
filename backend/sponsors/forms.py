# backend/sponsors/forms.py

from django import forms
from .models import SponsorProfile

class SponsorProfileForm(forms.ModelForm):
    class Meta:
        model = SponsorProfile
        fields = ['brand_name', 'tagline', 'description', 'website_url', 'cover_image']
        labels = {
            'brand_name': 'Tên thương hiệu',
            'tagline': 'Slogan/Khẩu hiệu',
            'description': 'Giới thiệu chi tiết',
            'website_url': 'Link trang web',
            'cover_image': 'Ảnh bìa',
        }
        help_texts = {
            'cover_image': 'Tải lên ảnh bìa mới để thay thế ảnh hiện tại (nếu có).',
        }