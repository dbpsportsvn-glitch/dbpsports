from django.shortcuts import render, get_object_or_404, redirect # Đã sửa ở đây
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache
from .models import Organization
from .forms import TournamentCreationForm
from tournaments.models import Tournament, Group, Team
from tournaments.utils import send_notification_email
from django.conf import settings
from django.http import HttpResponseForbidden


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
        return redirect('organizations:dashboard') 

    if request.method == 'POST':
        form = TournamentCreationForm(request.POST, request.FILES)
        if form.is_valid():
            tournament = form.save(commit=False)
            tournament.organization = organization
            tournament.save()
            return redirect('organizations:dashboard') 
    else:
        form = TournamentCreationForm()

    context = {
        'form': form,
        'organization': organization
    }
    return render(request, 'organizations/create_tournament.html', context)

@login_required
@never_cache
def manage_tournament(request, pk):
    tournament = get_object_or_404(Tournament, pk=pk)

    if not tournament.organization or not tournament.organization.members.filter(pk=request.user.pk).exists():
        return redirect('organizations:dashboard')

    if request.method == 'POST':
        # Xử lý tạo bảng đấu (giữ nguyên)
        if 'create_group' in request.POST:
            group_name = request.POST.get('group_name', '').strip()
            if group_name:
                Group.objects.create(tournament=tournament, name=group_name)
            return redirect('organizations:manage_tournament', pk=pk)

        # === BẮT ĐẦU THÊM MỚI: Xử lý duyệt đội ===
        if 'approve_payment' in request.POST:
            team_id = request.POST.get('team_id')
            if team_id:
                team_to_approve = get_object_or_404(Team, id=team_id, tournament=tournament)
                if team_to_approve.payment_status == 'PENDING':
                    team_to_approve.payment_status = 'PAID'
                    team_to_approve.save()

                    # Gửi email xác nhận cho đội trưởng
                    if team_to_approve.captain.email:
                        send_notification_email(
                            subject=f"Thanh toán thành công cho đội {team_to_approve.name}",
                            template_name='tournaments/emails/payment_confirmed.html',
                            context={'team': team_to_approve},
                            recipient_list=[team_to_approve.captain.email]
                        )
            return redirect('organizations:manage_tournament', pk=pk)

        # === BẮT ĐẦU THÊM MỚI: Xử lý thu hồi đội ===
        if 'revoke_payment' in request.POST:
            team_id = request.POST.get('team_id')
            if team_id:
                team_to_revoke = get_object_or_404(Team, id=team_id, tournament=tournament)
                # Chỉ thu hồi được đội đã thanh toán và chưa được xếp bảng
                if team_to_revoke.payment_status == 'PAID' and team_to_revoke.group is None:
                    team_to_revoke.payment_status = 'PENDING' # Chuyển về trạng thái "Chờ xác nhận"
                    team_to_revoke.save()
                # (Chúng ta có thể thêm message báo lỗi nếu đội đã được xếp bảng)
            return redirect('organizations:manage_tournament', pk=pk)
        # === KẾT THÚC THÊM MỚI ===

    groups = tournament.groups.all().order_by('name')
    
    # Lấy các đội đang chờ duyệt
    pending_teams = tournament.teams.filter(payment_status='PENDING').select_related('captain')
    # Lấy các đội đã được duyệt
    paid_teams = tournament.teams.filter(payment_status='PAID').select_related('captain')
    # === KẾT THÚC THÊM MỚI ===

    context = {
        'tournament': tournament,
        'groups': groups,
        'pending_teams': pending_teams, # Gửi danh sách ra template
        'paid_teams': paid_teams,       # Gửi danh sách ra template
    }
    return render(request, 'organizations/manage_tournament.html', context)


@login_required
def delete_group(request, pk):
    group = get_object_or_404(Group, pk=pk)
    tournament = group.tournament

    # KIỂM TRA BẢO MẬT: Đảm bảo người dùng thuộc đơn vị tổ chức của giải đấu này
    if not tournament.organization or not tournament.organization.members.filter(pk=request.user.pk).exists():
        return HttpResponseForbidden("Bạn không có quyền thực hiện hành động này.")

    # Chỉ thực hiện xóa nếu là request POST để an toàn hơn
    if request.method == 'POST':
        group.delete()
        # Sau khi xóa, quay về trang quản lý của giải đấu đó
        return redirect('organizations:manage_tournament', pk=tournament.pk)

    # Nếu là request GET, không làm gì cả và điều hướng về trang quản lý
    return redirect('organizations:manage_tournament', pk=tournament.pk)


@login_required
def delete_tournament(request, pk):
    tournament = get_object_or_404(Tournament, pk=pk)

    # KIỂM TRA BẢO MẬT: Đảm bảo người dùng thuộc đơn vị tổ chức của giải đấu này
    if not tournament.organization or not tournament.organization.members.filter(pk=request.user.pk).exists():
        return HttpResponseForbidden("Bạn không có quyền thực hiện hành động này.")

    if request.method == 'POST':
        tournament.delete()
        # Sau khi xóa, quay về trang dashboard của đơn vị
        return redirect('organizations:dashboard')

    # Nếu là request GET, không làm gì cả và điều hướng về dashboard
    return redirect('organizations:dashboard')
