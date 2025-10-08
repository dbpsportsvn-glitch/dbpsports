# backend/sponsors/forms.py

from django import forms
from .models import SponsorProfile, Testimonial

class SponsorProfileForm(forms.ModelForm):
    class Meta:
        model = SponsorProfile
        # Cập nhật lại fields cho đúng với model của bạn
        fields = [
            'brand_name', 
            'brand_logo',  # <-- Thêm logo vào form
            'tagline', 
            'description', 
            'website_url', 
            'phone_number', 
            'cover_image'
        ]
        labels = {
            'brand_name': 'Tên thương hiệu',
            'brand_logo': 'Logo thương hiệu', # <-- Thêm label
            'tagline': 'Slogan/Khẩu hiệu',
            'description': 'Giới thiệu chi tiết',
            'website_url': 'Link trang web',
            'cover_image': 'Ảnh bìa',
        }
        help_texts = {
            'cover_image': 'Tải lên ảnh bìa mới để thay thế ảnh hiện tại (nếu có).',
            'brand_logo': 'Đây là logo sẽ hiển thị khi bạn tài trợ cho các giải đấu.' # <-- Thêm help_text
        }

# --- BẮT ĐẦU THÊM MỚI ---
class TestimonialForm(forms.ModelForm):
    class Meta:
        model = Testimonial
        # --- THÊM 'rating' VÀO ĐÂY ---
        fields = ['rating', 'text']
        widgets = {
            # --- SỬ DỤNG RadioSelect ĐỂ DỄ DÀNG CUSTOMIZE CSS ---
            'rating': forms.RadioSelect(attrs={'class': 'star-rating'}),
            'text': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Chia sẻ cảm nhận của bạn về nhà tài trợ...'}),
        }
        labels = {
            'rating': 'Bạn đánh giá nhà tài trợ này thế nào?',
            'text': 'Nội dung nhận xét'
        }        