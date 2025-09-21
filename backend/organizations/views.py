from django.shortcuts import render, get_object_or_404, redirect # Đã sửa ở đây
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache
from .models import Organization
from .forms import TournamentCreationForm
from tournaments.models import Tournament, Group

@login_required
@never_cache
def organization_dashboard(request):
    """
    Hiển thị trang quản lý chính cho đơn vị tổ chức của người dùng.
    """
    organization = Organization.objects.filter(members=request.user).first()

    if not organization:
        return render(request, 'organizations/no_organization.html')

    tournaments = organization.tournaments.all().order_by('-start_date')

    context = {
        'organization': organization,
        'tournaments': tournaments,
    }
    return render(request, 'organizations/organization_dashboard.html', context)


@login_required
@never_cache
def create_tournament(request):
    organization = Organization.objects.filter(members=request.user).first()
    if not organization:
        return redirect('organizations:dashboard') # Dòng này giờ sẽ hoạt động

    if request.method == 'POST':
        form = TournamentCreationForm(request.POST, request.FILES)
        if form.is_valid():
            tournament = form.save(commit=False)
            tournament.organization = organization
            tournament.save()
            return redirect('organizations:dashboard') # Dòng này giờ sẽ hoạt động
    else:
        form = TournamentCreationForm()

    context = {
        'form': form,
        'organization': organization
    }
    return render(request, 'organizations/create_tournament.html', context)

# === BẮT ĐẦU THÊM MỚI ===
@login_required
@never_cache
def manage_tournament(request, pk):
    tournament = get_object_or_404(Tournament, pk=pk)

    # Kiểm tra quyền: người dùng phải thuộc đơn vị tổ chức của giải này
    if not tournament.organization or not tournament.organization.members.filter(pk=request.user.pk).exists():
        return redirect('organizations:dashboard') # Nếu không có quyền, đá về dashboard

    # Xử lý khi người tổ chức gửi form tạo Bảng đấu mới
    if request.method == 'POST':
        if 'create_group' in request.POST:
            group_name = request.POST.get('group_name', '').strip()
            if group_name:
                # Tạo bảng đấu mới, gán vào giải đấu này
                Group.objects.create(tournament=tournament, name=group_name)
                return redirect('organizations:manage_tournament', pk=pk) # Tải lại trang

    # Lấy danh sách các bảng đấu hiện có của giải
    groups = tournament.groups.all().order_by('name')

    context = {
        'tournament': tournament,
        'groups': groups,
    }
    return render(request, 'organizations/manage_tournament.html', context)
# === KẾT THÚC THÊM MỚI ===    