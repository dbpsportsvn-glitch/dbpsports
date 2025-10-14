# backend/sponsors/forms.py

from django import forms
from .models import SponsorProfile, Testimonial

class SponsorProfileForm(forms.ModelForm):
    class Meta:
        model = SponsorProfile
        fields = [
            'brand_name', 
            'brand_logo',
            'tagline', 
            'description', 
            'website_url', 
            'phone_number'
        ]
        labels = {
            'brand_name': 'Tên thương hiệu',
            'brand_logo': 'Logo thương hiệu',
            'tagline': 'Slogan/Khẩu hiệu',
            'description': 'Giới thiệu chi tiết',
            'website_url': 'Link trang web',
            'phone_number': 'Số điện thoại liên hệ',
        }
        help_texts = {
            'brand_logo': 'Logo sẽ hiển thị trên hồ sơ và khi bạn tài trợ các giải đấu. Khuyến nghị: 500x500px.',
            'description': 'Giới thiệu về thương hiệu, lĩnh vực kinh doanh, cam kết với thể thao...',
        }
        widgets = {
            'description': forms.Textarea(attrs={'rows': 5}),
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