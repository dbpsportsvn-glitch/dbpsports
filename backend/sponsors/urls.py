# backend/sponsors/urls.py

from django.urls import path
# Cập nhật dòng import
from .views import SponsorProfileDetailView, SponsorProfileUpdateView

app_name = 'sponsors'

urlpatterns = [
    path('profile/<int:pk>/', SponsorProfileDetailView.as_view(), name='profile_detail'),
    # THÊM DÒNG NÀY: Dùng chung 1 URL, nhưng cho trang chỉnh sửa
    path('profile/edit/', SponsorProfileUpdateView.as_view(), name='profile_edit'),
]