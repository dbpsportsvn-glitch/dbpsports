# backend/sponsors/urls.py

from django.urls import path
from .views import (
    SponsorProfileDetailView, 
    SponsorProfileUpdateView, 
    ManageTestimonialsView,
    ToggleTestimonialView, # <-- Sửa
    DeleteTestimonialView, # <-- Sửa
)

app_name = 'sponsors'

urlpatterns = [
    path('profile/<int:pk>/', SponsorProfileDetailView.as_view(), name='profile_detail'),
    path('profile/edit/', SponsorProfileUpdateView.as_view(), name='profile_edit'),
    path('profile/testimonials/', ManageTestimonialsView.as_view(), name='manage_testimonials'),

    # --- SỬA LẠI 2 DÒNG NÀY ---
    path('testimonials/<int:pk>/toggle/', ToggleTestimonialView.as_view(), name='toggle_testimonial'),
    path('testimonials/<int:pk>/delete/', DeleteTestimonialView.as_view(), name='delete_testimonial'),
]