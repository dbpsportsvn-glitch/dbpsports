# backend/sponsors/views.py

from django.shortcuts import render, get_object_or_404
from django.views.generic import DetailView, UpdateView # Thêm UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin # Import mixins để kiểm tra quyền
from django.urls import reverse_lazy

from .models import SponsorProfile
from .forms import SponsorProfileForm # Import form vừa tạo

class SponsorProfileDetailView(DetailView):
    model = SponsorProfile
    template_name = 'sponsors/sponsor_profile_detail.html'
    context_object_name = 'profile'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Lấy danh sách các giải đấu mà nhà tài trợ này đã tài trợ
        # Chúng ta sẽ dùng thông tin này để hiển thị trên trang hồ sơ
        profile = self.get_object()
        sponsorships = profile.user.sponsorships.filter(is_active=True).select_related('tournament')
        context['sponsorships'] = sponsorships
        return context

# --- BẮT ĐẦU THÊM CODE MỚI ---
class SponsorProfileUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = SponsorProfile
    form_class = SponsorProfileForm
    template_name = 'sponsors/sponsor_profile_form.html'

    def get_object(self, queryset=None):
        """Chỉ cho phép user chỉnh sửa profile của chính họ."""
        return get_object_or_404(SponsorProfile, user=self.request.user)

    def test_func(self):
        """
        Kiểm tra quyền: User phải là chủ của profile này.
        Đây là lớp bảo vệ thứ hai.
        """
        profile = self.get_object()
        return self.request.user == profile.user

    def get_success_url(self):
        """Sau khi cập nhật thành công, chuyển hướng về trang hồ sơ."""
        return reverse_lazy('sponsors:profile_detail', kwargs={'pk': self.object.pk})        