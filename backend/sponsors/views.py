# backend/sponsors/views.py

from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import DetailView, UpdateView, ListView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.decorators import login_required
from django.urls import reverse_lazy
from django.contrib import messages
from django.views import View
from django.http import HttpResponseForbidden
from django.db.models import F, Case, When, BooleanField # <-- THÊM IMPORT NÀY

from .models import SponsorProfile, Testimonial
from .forms import SponsorProfileForm, TestimonialForm

# --- CÁC CLASS VIEW CŨ GIỮ NGUYÊN ---
class SponsorProfileDetailView(DetailView):
    model = SponsorProfile
    template_name = 'sponsors/sponsor_profile_detail.html'
    context_object_name = 'profile'

    def get(self, request, *args, **kwargs):
        """Redirect to unified public profile"""
        profile = self.get_object()
        return redirect('public_profile', username=profile.user.username or profile.user.email)

class SponsorProfileUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = SponsorProfile
    form_class = SponsorProfileForm
    template_name = 'sponsors/sponsor_profile_form.html'
    
    def get_object(self, queryset=None):
        return get_object_or_404(SponsorProfile, user=self.request.user)

    def test_func(self):
        profile = self.get_object()
        return self.request.user == profile.user

    def get_success_url(self):
        # Redirect về public profile tab Chuyên môn thay vì sponsor detail page cũ
        from django.urls import reverse
        username = self.request.user.username or self.request.user.email
        return reverse('public_profile', kwargs={'username': username}) + '#professional'

class ManageTestimonialsView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = Testimonial
    template_name = 'sponsors/manage_testimonials.html'
    context_object_name = 'testimonials'

    def test_func(self):
        return hasattr(self.request.user, 'sponsor_profile')

    def get_queryset(self):
        profile = self.request.user.sponsor_profile
        return Testimonial.objects.filter(sponsor_profile=profile).order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['profile'] = self.request.user.sponsor_profile
        return context

# --- Kiểm soát nhận xét của ntt ---
class ToggleTestimonialView(LoginRequiredMixin, View):
    """
    View chuyên dụng để Ẩn/Hiện Testimonial bằng phương pháp update trực tiếp.
    """
    def get(self, request, *args, **kwargs):
        messages.warning(request, "Hành động không hợp lệ.")
        return redirect('sponsors:manage_testimonials')

    def post(self, request, *args, **kwargs):
        pk = self.kwargs.get('pk')
        profile = request.user.sponsor_profile

        # Lọc testimonial cần update một cách an toàn
        # Đảm bảo chỉ update testimonial có pk này VÀ thuộc về profile này
        updated_count = Testimonial.objects.filter(pk=pk, sponsor_profile=profile).update(
            is_approved=Case(
                When(is_approved=True, then=False),
                default=True,
                output_field=BooleanField()
            )
        )

        if updated_count > 0:
            messages.success(request, "Đã cập nhật trạng thái nhận xét thành công.")
        else:
            messages.error(request, "Không tìm thấy nhận xét hoặc bạn không có quyền thay đổi.")

        return redirect('sponsors:manage_testimonials')

class DeleteTestimonialView(LoginRequiredMixin, View):
    """
    View chuyên dụng để xóa Testimonial.
    """
    def get(self, request, *args, **kwargs):
        messages.warning(request, "Hành động không hợp lệ.")
        return redirect('sponsors:manage_testimonials')

    def post(self, request, *args, **kwargs):
        testimonial = get_object_or_404(Testimonial, pk=self.kwargs.get('pk'))

        if not hasattr(request.user, 'sponsor_profile') or testimonial.sponsor_profile != request.user.sponsor_profile:
            return HttpResponseForbidden("Bạn không có quyền thực hiện hành động này.")

        try:
            testimonial.delete()
            messages.success(request, "Đã xóa nhận xét vĩnh viễn.")
        except Exception as e:
            messages.error(request, f"Không thể xóa nhận xét. Lỗi: {e}")

        return redirect('sponsors:manage_testimonials')


@login_required
def create_testimonial_view(request, sponsor_pk):
    """Tạo testimonial cho sponsor"""
    sponsor_profile = get_object_or_404(SponsorProfile, pk=sponsor_pk)
    
    # Không cho phép tự đánh giá
    if request.user == sponsor_profile.user:
        messages.error(request, "Bạn không thể đánh giá chính mình.")
        return redirect('public_profile', username=request.user.username or request.user.email)
    
    # Kiểm tra đã đánh giá chưa
    existing_testimonial = Testimonial.objects.filter(
        sponsor_profile=sponsor_profile,
        author=request.user
    ).first()
    
    if existing_testimonial:
        messages.info(request, "Bạn đã đánh giá nhà tài trợ này rồi.")
        return redirect('public_profile', username=sponsor_profile.user.username or sponsor_profile.user.email)
    
    if request.method == 'POST':
        form = TestimonialForm(request.POST)
        if form.is_valid():
            testimonial = form.save(commit=False)
            testimonial.sponsor_profile = sponsor_profile
            testimonial.author = request.user
            testimonial.save()
            messages.success(request, f"Đã tạo đánh giá {testimonial.rating}/5 sao cho {sponsor_profile.brand_name}!")
            return redirect('public_profile', username=sponsor_profile.user.username or sponsor_profile.user.email)
        else:
            messages.error(request, "Có lỗi xảy ra. Vui lòng kiểm tra lại thông tin.")
    else:
        form = TestimonialForm()
    
    context = {
        'form': form,
        'sponsor_profile': sponsor_profile,
        'existing_testimonial': existing_testimonial,
    }
    
    return render(request, 'sponsors/create_testimonial.html', context)