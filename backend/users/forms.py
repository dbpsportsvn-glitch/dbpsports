# backend/users/forms.py

from django import forms
from django.contrib.auth.forms import UserChangeForm
from django.contrib.auth.models import User
from .models import Profile, Role, CoachProfile, StadiumProfile
from sponsors.models import SponsorProfile
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Row, Column, Div, HTML, Fieldset

class CustomUserChangeForm(UserChangeForm):
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email')

class AvatarUpdateForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['avatar']

class NotificationPreferencesForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['notify_match_results', 'notify_new_teams', 'notify_draw_results', 'notify_schedule_updates']

class ProfileUpdateForm(forms.ModelForm):
    roles = forms.ModelMultipleChoiceField(
        queryset=Role.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label="Vai trò của bạn"
    )

    class Meta:
        model = Profile
        fields = [
            'banner_image'  # CHỈ GIỮ LẠI BANNER IMAGE
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields['roles'].initial = self.instance.roles.all()

    def save(self, commit=True):
        profile = super().save(commit=False)
        if commit:
            profile.save()
            profile.roles.set(self.cleaned_data['roles'])
        return profile

class StadiumProfileForm(forms.ModelForm):
    class Meta:
        model = StadiumProfile
        fields = ['stadium_name', 'address', 'phone_number', 'description', 'logo']
        labels = {
            'stadium_name': 'Tên sân bóng',
            'address': 'Địa chỉ sân',
            'phone_number': 'Số điện thoại',
            'description': 'Mô tả sân bóng',
            'logo': 'Logo sân bóng',
        }
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }

class ProfileSetupForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['bio', 'location', 'experience', 'equipment', 'referee_level', 'brand_website', 'sponsorship_interests']
        widgets = {
            'bio': forms.Textarea(attrs={'rows': 4}),
            'equipment': forms.Textarea(attrs={'rows': 3}),
        }

    def save(self, commit=True):
        profile = super().save(commit=True)
        return profile

# === FORM THỐNG NHẤT CHO TẤT CẢ VAI TRÒ ===
class UnifiedProfessionalForm(forms.ModelForm):
    """Form thống nhất cho tất cả vai trò chuyên môn"""
    
    # Coach fields
    coach_specialization = forms.CharField(
        max_length=200, 
        required=False, 
        label="Chuyên môn",
        help_text="Ví dụ: Bóng đá, Futsal, Bóng rổ..."
    )
    coach_hourly_rate = forms.DecimalField(
        max_digits=10, 
        decimal_places=0, 
        required=False, 
        label="Giá thuê/giờ (VNĐ)",
        help_text="Để trống nếu không áp dụng"
    )
    coach_is_available = forms.BooleanField(
        required=False, 
        label="Sẵn sàng nhận việc",
        initial=True
    )
    
    # Stadium fields
    stadium_name = forms.CharField(
        max_length=200, 
        required=False, 
        label="Tên sân bóng"
    )
    stadium_address = forms.CharField(
        max_length=500, 
        required=False, 
        label="Địa chỉ sân"
    )
    stadium_phone = forms.CharField(
        max_length=20, 
        required=False, 
        label="Số điện thoại sân"
    )
    stadium_description = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 3}),
        required=False,
        label="Mô tả sân"
    )
    
    # Sponsor fields
    sponsor_brand_name = forms.CharField(
        max_length=200, 
        required=False, 
        label="Tên thương hiệu"
    )
    sponsor_brand_logo = forms.ImageField(
        required=False, 
        label="Logo thương hiệu",
        help_text="Khuyến nghị: 500x500px"
    )
    sponsor_tagline = forms.CharField(
        max_length=255, 
        required=False, 
        label="Slogan/Khẩu hiệu"
    )
    sponsor_description = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 4}),
        required=False,
        label="Giới thiệu chi tiết"
    )
    sponsor_website_url = forms.URLField(
        required=False, 
        label="Link trang web"
    )
    sponsor_phone_number = forms.CharField(
        max_length=20, 
        required=False, 
        label="Số điện thoại liên hệ"
    )

    class Meta:
        model = Profile
        fields = [
            'bio', 'location', 'experience', 'equipment', 'referee_level',
            'brand_website', 'sponsorship_interests'
        ]
        widgets = {
            'bio': forms.Textarea(attrs={'rows': 4}),
            'equipment': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        self.user = user
        if user:
            # Load existing data
            self.load_existing_data()
            
            # Setup form helper
            self.setup_form_helper()

    def load_existing_data(self):
        """Load existing data from related models"""
        if not self.user:
            return
            
        # Load coach data
        try:
            coach_profile = self.user.coach_profile
            self.fields['coach_specialization'].initial = coach_profile.specialization
            self.fields['coach_hourly_rate'].initial = coach_profile.hourly_rate
            self.fields['coach_is_available'].initial = coach_profile.is_available
        except CoachProfile.DoesNotExist:
            pass
            
        # Load stadium data
        try:
            stadium_profile = self.user.stadium_profile
            self.fields['stadium_name'].initial = stadium_profile.stadium_name
            self.fields['stadium_address'].initial = stadium_profile.address
            self.fields['stadium_phone'].initial = stadium_profile.phone_number
            self.fields['stadium_description'].initial = stadium_profile.description
        except StadiumProfile.DoesNotExist:
            pass
            
        # Load sponsor data
        try:
            sponsor_profile = self.user.sponsor_profile
            self.fields['sponsor_brand_name'].initial = sponsor_profile.brand_name
            self.fields['sponsor_tagline'].initial = sponsor_profile.tagline
            self.fields['sponsor_description'].initial = sponsor_profile.description
            self.fields['sponsor_website_url'].initial = sponsor_profile.website_url
            self.fields['sponsor_phone_number'].initial = sponsor_profile.phone_number
        except SponsorProfile.DoesNotExist:
            pass

    def setup_form_helper(self):
        """Setup crispy forms layout based on user roles"""
        if not self.user:
            return
            
        user_roles = self.user.profile.roles.all()
        role_ids = [role.id for role in user_roles]
        
        # Base fields for all roles
        layout_fields = [
            Fieldset(
                'Thông tin chung',
                Row(
                    Column('bio', css_class='form-group col-md-12 mb-3'),
                ),
                Row(
                    Column('location', css_class='form-group col-md-6 mb-3'),
                    Column('experience', css_class='form-group col-md-6 mb-3'),
                ),
                Row(
                    Column('equipment', css_class='form-group col-md-12 mb-3'),
                ),
            )
        ]
        
        # Coach fields
        if 'COACH' in role_ids:
            layout_fields.append(
                Fieldset(
                    'Thông tin Huấn luyện viên',
                    Row(
                        Column('coach_specialization', css_class='form-group col-md-6 mb-3'),
                        Column('coach_hourly_rate', css_class='form-group col-md-6 mb-3'),
                    ),
                    Row(
                        Column('coach_is_available', css_class='form-group col-md-12 mb-3'),
                    ),
                )
            )
        
        # Stadium fields
        if 'STADIUM' in role_ids:
            layout_fields.append(
                Fieldset(
                    'Thông tin Sân bóng',
                    Row(
                        Column('stadium_name', css_class='form-group col-md-6 mb-3'),
                        Column('stadium_phone', css_class='form-group col-md-6 mb-3'),
                    ),
                    Row(
                        Column('stadium_address', css_class='form-group col-md-12 mb-3'),
                    ),
                    Row(
                        Column('stadium_description', css_class='form-group col-md-12 mb-3'),
                    ),
                )
            )
        
        # Sponsor fields
        if 'SPONSOR' in role_ids:
            layout_fields.append(
                Fieldset(
                    'Thông tin Nhà tài trợ',
                    Row(
                        Column('sponsor_brand_name', css_class='form-group col-md-6 mb-3'),
                        Column('sponsor_brand_logo', css_class='form-group col-md-6 mb-3'),
                    ),
                    Row(
                        Column('sponsor_tagline', css_class='form-group col-md-12 mb-3'),
                    ),
                    Row(
                        Column('sponsor_description', css_class='form-group col-md-12 mb-3'),
                    ),
                    Row(
                        Column('sponsor_website_url', css_class='form-group col-md-6 mb-3'),
                        Column('sponsor_phone_number', css_class='form-group col-md-6 mb-3'),
                    ),
                )
            )
        
        # Referee fields
        if 'REFEREE' in role_ids:
            layout_fields.append(
                Fieldset(
                    'Thông tin Trọng tài',
                    Row(
                        Column('referee_level', css_class='form-group col-md-12 mb-3'),
                    ),
                )
            )
        
        # Other professional roles
        if any(role in role_ids for role in ['COMMENTATOR', 'MEDIA', 'PHOTOGRAPHER']):
            layout_fields.append(
                Fieldset(
                    'Thông tin chuyên môn khác',
                    Row(
                        Column('brand_website', css_class='form-group col-md-6 mb-3'),
                        Column('sponsorship_interests', css_class='form-group col-md-6 mb-3'),
                    ),
                )
            )

        self.helper = FormHelper()
        self.helper.layout = Layout(*layout_fields)
        self.helper.form_method = 'post'
        self.helper.form_enctype = 'multipart/form-data'

    def save(self, commit=True):
        """Save data to appropriate models"""
        profile = super().save(commit=False)
        
        if commit:
            profile.save()
            
            # Save coach data
            if 'COACH' in [role.id for role in self.user.profile.roles.all()]:
                coach_profile, created = CoachProfile.objects.get_or_create(
                    user=self.user,
                    defaults={
                        'specialization': self.cleaned_data.get('coach_specialization', ''),
                        'hourly_rate': self.cleaned_data.get('coach_hourly_rate'),
                        'is_available': self.cleaned_data.get('coach_is_available', True),
                    }
                )
                if not created:
                    coach_profile.specialization = self.cleaned_data.get('coach_specialization', '')
                    coach_profile.hourly_rate = self.cleaned_data.get('coach_hourly_rate')
                    coach_profile.is_available = self.cleaned_data.get('coach_is_available', True)
                    coach_profile.save()
            
            # Save stadium data
            if 'STADIUM' in [role.id for role in self.user.profile.roles.all()]:
                stadium_profile, created = StadiumProfile.objects.get_or_create(
                    user=self.user,
                    defaults={
                        'stadium_name': self.cleaned_data.get('stadium_name', ''),
                        'address': self.cleaned_data.get('stadium_address', ''),
                        'phone_number': self.cleaned_data.get('stadium_phone', ''),
                        'description': self.cleaned_data.get('stadium_description', ''),
                    }
                )
                if not created:
                    stadium_profile.stadium_name = self.cleaned_data.get('stadium_name', '')
                    stadium_profile.address = self.cleaned_data.get('stadium_address', '')
                    stadium_profile.phone_number = self.cleaned_data.get('stadium_phone', '')
                    stadium_profile.description = self.cleaned_data.get('stadium_description', '')
                    stadium_profile.save()
            
            # Save sponsor data
            if 'SPONSOR' in [role.id for role in self.user.profile.roles.all()]:
                sponsor_profile, created = SponsorProfile.objects.get_or_create(
                    user=self.user,
                    defaults={
                        'brand_name': self.cleaned_data.get('sponsor_brand_name', ''),
                        'tagline': self.cleaned_data.get('sponsor_tagline', ''),
                        'description': self.cleaned_data.get('sponsor_description', ''),
                        'website_url': self.cleaned_data.get('sponsor_website_url', ''),
                        'phone_number': self.cleaned_data.get('sponsor_phone_number', ''),
                    }
                )
                if not created:
                    sponsor_profile.brand_name = self.cleaned_data.get('sponsor_brand_name', '')
                    sponsor_profile.tagline = self.cleaned_data.get('sponsor_tagline', '')
                    sponsor_profile.description = self.cleaned_data.get('sponsor_description', '')
                    sponsor_profile.website_url = self.cleaned_data.get('sponsor_website_url', '')
                    sponsor_profile.phone_number = self.cleaned_data.get('sponsor_phone_number', '')
                    sponsor_profile.save()
                
                # Handle logo upload
                if self.cleaned_data.get('sponsor_brand_logo'):
                    sponsor_profile.brand_logo = self.cleaned_data['sponsor_brand_logo']
                    sponsor_profile.save()
        
        return profile