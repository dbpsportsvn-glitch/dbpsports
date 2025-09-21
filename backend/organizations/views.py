# File: backend/organizations/views.py

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
from .forms import TournamentCreationForm, OrganizationCreationForm, MemberInviteForm, MatchUpdateForm

#=================================

@login_required
@never_cache
def organization_dashboard(request):
    organization = Organization.objects.filter(members=request.user).first()
    if not organization:
        return render(request, 'organizations/no_organization.html')

    if organization.status == Organization.Status.PENDING:
        return render(request, 'organizations/organization_pending.html', {'organization': organization})

    if organization.status != Organization.Status.ACTIVE:
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
    tournament = get_object_or_404(Tournament.objects.select_related('organization'), pk=pk)

    if not tournament.organization or not tournament.organization.members.filter(pk=request.user.pk).exists():
        return redirect('organizations:dashboard')

    # Lấy view từ URL, mặc định là 'overview'
    view_name = request.GET.get('view', 'overview')

    # Xử lý các POST request
    if request.method == 'POST':
        # Xử lý tạo bảng đấu
        if 'create_group' in request.POST:
            group_name = request.POST.get('group_name', '').strip()
            if group_name:
                Group.objects.create(tournament=tournament, name=group_name)
            return redirect(request.path_info + '?view=groups')

        # Xử lý duyệt đội
        if 'approve_payment' in request.POST:
            team_id = request.POST.get('team_id')
            if team_id:
                team = get_object_or_404(Team, id=team_id, tournament=tournament)
                if team.payment_status == 'PENDING':
                    team.payment_status = 'PAID'
                    team.save()
                    if team.captain.email:
                        send_notification_email(
                            subject=f"Thanh toán thành công cho đội {team.name}",
                            template_name='tournaments/emails/payment_confirmed.html',
                            context={'team': team}, recipient_list=[team.captain.email]
                        )
            return redirect(request.path_info + '?view=teams')

        # Xử lý thu hồi đội
        if 'revoke_payment' in request.POST:
            team_id = request.POST.get('team_id')
            if team_id:
                team = get_object_or_404(Team, id=team_id, tournament=tournament)
                if team.payment_status == 'PAID' and team.group is None:
                    team.payment_status = 'PENDING'
                    team.save()
            return redirect(request.path_info + '?view=teams')

        # Xử lý mời thành viên
        if 'invite_member' in request.POST:
            if request.user == tournament.organization.owner:
                invite_form = MemberInviteForm(request.POST)
                if invite_form.is_valid():
                    email = invite_form.cleaned_data['email']
                    user = User.objects.get(email__iexact=email)
                    membership, created = Membership.objects.get_or_create(
                        organization=tournament.organization, user=user,
                        defaults={'role': Membership.Role.ADMIN}
                    )
                    if created: messages.success(request, f"Đã thêm {user.email} vào đơn vị.")
                    else: messages.warning(request, f"{user.email} đã là thành viên.")
                else:
                    for field, errors in invite_form.errors.items():
                        for error in errors: messages.error(request, error)
            return redirect(request.path_info + '?view=members')

    # Chuẩn bị context chung
    context = {
        'tournament': tournament,
        'organization': tournament.organization,
        'active_page': view_name, # Biến này sẽ giúp menu biết mục nào đang active
    }

    # Thêm dữ liệu vào context tùy theo view người dùng chọn
    if view_name == 'teams':
        context['pending_teams'] = tournament.teams.filter(payment_status='PENDING').select_related('captain')
        context['paid_teams'] = tournament.teams.filter(payment_status='PAID').select_related('captain')
    elif view_name == 'groups':
        context['groups'] = tournament.groups.all().order_by('name')
    elif view_name == 'matches':
        context['matches'] = tournament.matches.select_related('team1', 'team2').order_by('match_time')
    elif view_name == 'members':
        context['members'] = Membership.objects.filter(organization=tournament.organization).select_related('user').order_by('role')
    
    # Render ra template chính
    return render(request, 'organizations/manage_tournament.html', context)


@login_required
def delete_group(request, pk):
    group = get_object_or_404(Group, pk=pk)
    tournament = group.tournament
    if not tournament.organization or not tournament.organization.members.filter(pk=request.user.pk).exists():
        return HttpResponseForbidden("Bạn không có quyền thực hiện hành động này.")
    if request.method == 'POST':
        group.delete()
        return redirect('organizations:manage_tournament', pk=tournament.pk)
    return redirect('organizations:manage_tournament', pk=tournament.pk)


@login_required
def delete_tournament(request, pk):
    tournament = get_object_or_404(Tournament, pk=pk)
    if not tournament.organization or not tournament.organization.members.filter(pk=request.user.pk).exists():
        return HttpResponseForbidden("Bạn không có quyền thực hiện hành động này.")
    if request.method == 'POST':
        tournament.delete()
        return redirect('organizations:dashboard')
    return redirect('organizations:dashboard')


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
            send_notification_email(
                subject=f"Có đơn vị mới đăng ký: {organization.name}",
                template_name='organizations/emails/new_organization_notification.html',
                context={'organization': organization},
                recipient_list=[settings.ADMIN_EMAIL]
            )
            return redirect('organizations:dashboard')
    else:
        form = OrganizationCreationForm()
    return render(request, 'organizations/create_organization.html', {'form': form})


@login_required
def remove_member(request, pk):
    membership_to_delete = get_object_or_404(Membership, pk=pk)
    organization = membership_to_delete.organization
    tournament_id_to_return = request.GET.get('tournament_id')
    if request.user != organization.owner or membership_to_delete.user == organization.owner:
        return HttpResponseForbidden("Bạn không có quyền thực hiện hành động này.")
    if request.method == 'POST':
        membership_to_delete.delete()
        messages.success(request, f"Đã xóa thành viên {membership_to_delete.user.email} khỏi đơn vị.")
    if tournament_id_to_return:
        return redirect('organizations:manage_tournament', pk=tournament_id_to_return)
    return redirect('organizations:dashboard')


@login_required
def edit_tournament(request, pk):
    tournament = get_object_or_404(Tournament, pk=pk)
    if not tournament.organization or not tournament.organization.members.filter(pk=request.user.pk).exists():
        return HttpResponseForbidden("Bạn không có quyền truy cập trang này.")
    if request.method == 'POST':
        form = TournamentCreationForm(request.POST, request.FILES, instance=tournament)
        if form.is_valid():
            form.save()
            messages.success(request, "Đã cập nhật thông tin giải đấu thành công!")
            return redirect('organizations:manage_tournament', pk=pk)
    else:
        form = TournamentCreationForm(instance=tournament)
    context = {
        'form': form,
        'tournament': tournament,
        'organization': tournament.organization,
        'active_page': 'settings'
    }
    return render(request, 'organizations/edit_tournament.html', context)


@login_required
@never_cache
def manage_match(request, pk):
    match = get_object_or_404(Match.objects.select_related('tournament__organization'), pk=pk)
    tournament = match.tournament
    organization = tournament.organization
    if not organization or not organization.members.filter(pk=request.user.pk).exists():
        return HttpResponseForbidden("Bạn không có quyền thực hiện hành động này.")
    if request.method == 'POST':
        form = MatchUpdateForm(request.POST, instance=match)
        if form.is_valid():
            form.save()
            messages.success(request, "Đã cập nhật thông tin trận đấu thành công!")
            return redirect(reverse('organizations:manage_tournament', args=[tournament.pk]) + '?view=matches')
    else:
        form = MatchUpdateForm(instance=match)
    context = {
        'form': form,
        'match': match,
        'tournament': tournament,
    }
    return render(request, 'organizations/manage_match.html', context)