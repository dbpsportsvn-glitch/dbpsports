# backend/sponsors/views.py

from django.shortcuts import render, get_object_or_404, redirect # Thêm redirect
from django.views.generic import DetailView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy, reverse # Thêm reverse
from django.contrib import messages # Thêm messages

from .models import SponsorProfile, Testimonial
from .forms import SponsorProfileForm, TestimonialForm
# =====================================

class SponsorProfileDetailView(DetailView):
    model = SponsorProfile
    template_name = 'sponsors/sponsor_profile_detail.html'
    context_object_name = 'profile'

    def get_context_data(self, **kwargs):
        # ... (code cũ của get_context_data giữ nguyên) ...
        context = super().get_context_data(**kwargs)
        profile = self.get_object()
        sponsorships = profile.user.sponsorships.filter(is_active=True).select_related('tournament')
        context['sponsorships'] = sponsorships
        testimonials = profile.testimonials.filter(is_approved=True).select_related('author__profile')
        context['testimonials'] = testimonials
        context['testimonial_form'] = TestimonialForm()
        return context

    # --- BẮT ĐẦU THÊM PHƯƠNG THỨC MỚI ---
    def post(self, request, *args, **kwargs):
        # Chỉ xử lý nếu người dùng đã đăng nhập
        if not request.user.is_authenticated:
            return redirect('account_login')

        self.object = self.get_object() # Lấy profile của nhà tài trợ đang xem
        form = TestimonialForm(request.POST)

        if form.is_valid():
            # Tạo một đối tượng Testimonial nhưng chưa lưu vào database
            testimonial = form.save(commit=False)
            # Gán các thông tin còn thiếu
            testimonial.sponsor_profile = self.object
            testimonial.author = request.user
            testimonial.save() # Lưu vào database

            messages.success(request, "Cảm ơn bạn! Nhận xét của bạn đã được gửi và đang chờ nhà tài trợ duyệt.")

            # Chuyển hướng về chính trang hồ sơ này
            return redirect(self.object.get_absolute_url())
        else:
            # Nếu form không hợp lệ, render lại trang với form và lỗi
            messages.error(request, "Gửi nhận xét thất bại. Vui lòng kiểm tra lại thông tin.")
            context = self.get_context_data()
            context['testimonial_form'] = form # Gửi lại form có lỗi để hiển thị
            return self.render_to_response(context)
            

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