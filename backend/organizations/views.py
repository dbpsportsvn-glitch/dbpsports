from django.shortcuts import render, get_object_or_404, redirect 
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache
from .models import Organization, Membership
from tournaments.models import Tournament, Group, Team, Match
from tournaments.utils import send_notification_email
from django.conf import settings
from django.http import HttpResponseForbidden
from django.contrib.auth.models import User 
from django.contrib import messages 
from .forms import TournamentCreationForm, OrganizationCreationForm, MemberInviteForm, MatchUpdateForm # Thêm MatchUpdateForm

#=================================

@login_required
@never_cache
def organization_dashboard(request):
    # Sửa lại logic: tìm đơn vị của người dùng
    organization = Organization.objects.filter(members=request.user).first()

    if not organization:
        return render(request, 'organizations/no_organization.html')

    # === BẮT ĐẦU THAY ĐỔI: Kiểm tra trạng thái ===
    # Nếu đơn vị đang chờ duyệt, hiển thị trang chờ
    if organization.status == Organization.Status.PENDING:
        return render(request, 'organizations/organization_pending.html', {'organization': organization})

    # Nếu đơn vị bị từ chối hoặc vô hiệu hóa, có thể thêm trang thông báo riêng sau
    if organization.status != Organization.Status.ACTIVE:
         return render(request, 'organizations/no_organization.html') # Tạm thời về trang này
    # === KẾT THÚC THAY ĐỔI ===

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

        # === BẮT ĐẦU THÊM MỚI: Xử lý mời thành viên ===
        if 'invite_member' in request.POST:
            # Chỉ chủ sở hữu mới có quyền mời
            if request.user == tournament.organization.owner:
                invite_form = MemberInviteForm(request.POST)
                if invite_form.is_valid():
                    email = invite_form.cleaned_data['email']
                    user_to_invite = User.objects.get(email__iexact=email)

                    # Tạo membership, nếu đã tồn tại thì bỏ qua lỗi
                    membership, created = Membership.objects.get_or_create(
                        organization=tournament.organization,
                        user=user_to_invite,
                        defaults={'role': Membership.Role.ADMIN}
                    )

                    if created:
                        messages.success(request, f"Đã thêm {user_to_invite.email} vào đơn vị thành công.")
                    else:
                        messages.warning(request, f"{user_to_invite.email} đã là thành viên.")
                else:
                    # Gửi lỗi của form ra message để hiển thị
                    for field, errors in invite_form.errors.items():
                        for error in errors:
                            messages.error(request, error)

            return redirect('organizations:manage_tournament', pk=pk)
        # === KẾT THÚC THÊM MỚI ===

    groups = tournament.groups.all().order_by('name')
    
    # Lấy các đội đang chờ duyệt
    pending_teams = tournament.teams.filter(payment_status='PENDING').select_related('captain')
    # Lấy các đội đã được duyệt
    paid_teams = tournament.teams.filter(payment_status='PAID').select_related('captain')
    members = Membership.objects.filter(organization=tournament.organization).select_related('user').order_by('role')  
    matches = tournament.matches.select_related('team1', 'team2').order_by('match_time') 

    context = {
        'tournament': tournament,
        'groups': groups,
        'pending_teams': pending_teams, # Gửi danh sách ra template
        'paid_teams': paid_teams,       # Gửi danh sách ra template
        'members': members,
        'matches': matches,
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


# === BẮT ĐẦU THÊM MỚI ===
@login_required
@never_cache
def create_organization(request):
    if Organization.objects.filter(members=request.user).exists():
        return redirect('organizations:dashboard')

    if request.method == 'POST':
        form = OrganizationCreationForm(request.POST, request.FILES)
        if form.is_valid():
            organization = form.save(commit=False)
            organization.owner = request.user
            organization.save()

            # === BẮT ĐẦU SỬA LỖI ĐƯỜNG DẪN TEMPLATE ===
            send_notification_email(
                subject=f"Có đơn vị mới đăng ký: {organization.name}",
                # Bỏ đi phần "organizations/templates/" ở đầu
                template_name='organizations/emails/new_organization_notification.html',
                context={'organization': organization},
                recipient_list=[settings.ADMIN_EMAIL]
            )
            # === KẾT THÚC SỬA LỖI ===

            return redirect('organizations:dashboard')
    else:
        form = OrganizationCreationForm()

    return render(request, 'organizations/create_organization.html', {'form': form})

# === BẮT ĐẦU THÊM MỚI ===
@login_required
def remove_member(request, pk):
    membership_to_delete = get_object_or_404(Membership, pk=pk)
    organization = membership_to_delete.organization
    tournament_id_to_return = request.GET.get('tournament_id')

    # KIỂM TRA BẢO MẬT: 
    # 1. Người thực hiện phải là chủ sở hữu của đơn vị này
    # 2. Chủ sở hữu không được tự xóa chính mình (phải là người khác)
    if request.user != organization.owner or membership_to_delete.user == organization.owner:
        return HttpResponseForbidden("Bạn không có quyền thực hiện hành động này.")

    if request.method == 'POST':
        membership_to_delete.delete()
        messages.success(request, f"Đã xóa thành viên {membership_to_delete.user.email} khỏi đơn vị.")

    # Quay về trang quản lý giải đấu trước đó
    if tournament_id_to_return:
        return redirect('organizations:manage_tournament', pk=tournament_id_to_return)

    return redirect('organizations:dashboard') # Fallback nếu không có tournament_id
# === KẾT THÚC THÊM MỚI ===

# === Logic sửa From cho BTC ===
@login_required
def edit_tournament(request, pk):
    tournament = get_object_or_404(Tournament, pk=pk)

    # Kiểm tra quyền: người dùng phải thuộc đơn vị tổ chức của giải này
    if not tournament.organization or not tournament.organization.members.filter(pk=request.user.pk).exists():
        return HttpResponseForbidden("Bạn không có quyền truy cập trang này.")

    if request.method == 'POST':
        # Sửa ở đây: dùng TournamentCreationForm
        form = TournamentCreationForm(request.POST, request.FILES, instance=tournament)
        if form.is_valid():
            form.save()
            messages.success(request, "Đã cập nhật thông tin giải đấu thành công!")
            return redirect('organizations:manage_tournament', pk=pk)
    else:
        # Sửa ở đây: dùng TournamentCreationForm
        form = TournamentCreationForm(instance=tournament)

    context = {
        'form': form,
        'tournament': tournament,
    }
    return render(request, 'organizations/edit_tournament.html', context)

# === BẮT ĐẦU THÊM MỚI ===
@login_required
@never_cache
def manage_match(request, pk):
    match = get_object_or_404(Match.objects.select_related('tournament__organization'), pk=pk)
    tournament = match.tournament
    organization = tournament.organization

    # KIỂM TRA BẢO MẬT: Đảm bảo người dùng thuộc BTC của giải đấu này
    if not organization or not organization.members.filter(pk=request.user.pk).exists():
        return HttpResponseForbidden("Bạn không có quyền thực hiện hành động này.")

    if request.method == 'POST':
        form = MatchUpdateForm(request.POST, instance=match)
        if form.is_valid():
            form.save()
            messages.success(request, "Đã cập nhật thông tin trận đấu thành công!")
            # Quay về trang chi tiết giải đấu, tab lịch thi đấu
            return redirect(reverse('tournament_detail', args=[tournament.pk]) + '?tab=schedule#schedule')
    else:
        form = MatchUpdateForm(instance=match)

    context = {
        'form': form,
        'match': match,
        'tournament': tournament,
    }
    return render(request, 'organizations/manage_match.html', context)
# === KẾT THÚC THÊM MỚI ===    