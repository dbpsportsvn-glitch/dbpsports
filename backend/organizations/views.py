# File: backend/organizations/views.py

from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache
from django.core.exceptions import ValidationError
from .models import Organization, Membership
from tournaments.models import Tournament, Group, Team, Match, Goal, Card, Player
from tournaments.utils import send_notification_email
from django.conf import settings
from django.http import HttpResponseForbidden
from django.contrib.auth.models import User
from django.contrib import messages
from .forms import TournamentCreationForm, OrganizationCreationForm, MemberInviteForm, MatchUpdateForm, GoalForm, CardForm

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

# File: backend/organizations/views.py

@login_required
@never_cache
def manage_tournament(request, pk):
    tournament = get_object_or_404(Tournament.objects.select_related('organization'), pk=pk)
    if not tournament.organization or not tournament.organization.members.filter(pk=request.user.pk).exists():
        return redirect('organizations:dashboard')
    view_name = request.GET.get('view', 'overview')
    if request.method == 'POST':
        if 'quick_update_score' in request.POST:
            match_id = request.POST.get('match_id')
            try:
                match = Match.objects.get(pk=match_id, tournament=tournament)
                score1_str = request.POST.get(f'score_team1_{match_id}')
                score2_str = request.POST.get(f'score_team2_{match_id}')
                match.team1_score = int(score1_str) if score1_str else None
                match.team2_score = int(score2_str) if score2_str else None
                match.save()
                messages.success(request, f"Đã cập nhật tỉ số cho trận đấu: {match.team1.name} vs {match.team2.name}.")
            except (Match.DoesNotExist, ValueError):
                messages.error(request, "Có lỗi xảy ra khi cập nhật tỉ số.")
            return redirect(request.path_info + '?view=matches')
        if 'create_group' in request.POST:
            group_name = request.POST.get('group_name', '').strip()
            if group_name:
                Group.objects.create(tournament=tournament, name=group_name)
            return redirect(request.path_info + '?view=groups')
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
        if 'revoke_payment' in request.POST:
            team_id = request.POST.get('team_id')
            if team_id:
                team = get_object_or_404(Team, id=team_id, tournament=tournament)
                if team.payment_status == 'PAID' and team.group is None:
                    team.payment_status = 'PENDING'
                    team.save()
            return redirect(request.path_info + '?view=teams')
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

    context = {
        'tournament': tournament,
        'organization': tournament.organization,
        'active_page': view_name,
    }

    # === BẮT ĐẦU NÂNG CẤP THỐNG KÊ ===
    if view_name == 'overview':
        all_teams = tournament.teams.all()
        context['stats'] = {
            'total_teams': all_teams.count(),
            'pending_teams_count': all_teams.filter(payment_status='PENDING').count(),
            'total_matches': tournament.matches.count(),
        }
    # === KẾT THÚC NÂNG CẤP THỐNG KÊ ===
    
    elif view_name == 'teams':
        context['pending_teams'] = tournament.teams.filter(payment_status='PENDING').select_related('captain')
        context['paid_teams'] = tournament.teams.filter(payment_status='PAID').select_related('captain')
    elif view_name == 'groups':
        context['groups'] = tournament.groups.all().order_by('name')
    elif view_name == 'matches':
        context['matches'] = tournament.matches.select_related('team1', 'team2').order_by('match_time')
    elif view_name == 'members':
        context['members'] = Membership.objects.filter(organization=tournament.organization).select_related('user').order_by('role')
    
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
    match = get_object_or_404(Match.objects.select_related('tournament__organization', 'team1', 'team2'), pk=pk)
    tournament = match.tournament
    organization = tournament.organization
    if not organization or not organization.members.filter(pk=request.user.pk).exists():
        return HttpResponseForbidden("Bạn không có quyền thực hiện hành động này.")
    players_in_match = Player.objects.filter(team__in=[match.team1, match.team2]).select_related('team').order_by('team__name', 'full_name')
    
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'update_match':
            form = MatchUpdateForm(request.POST, instance=match)
            if form.is_valid():
                form.save()
                messages.success(request, "Đã cập nhật thông tin chung của trận đấu.")
                return redirect('organizations:manage_match', pk=match.pk)
        
        # === PHẦN SỬA LỖI CHO BÀN THẮNG ===
        elif action == 'add_goal':
            goal_form = GoalForm(request.POST)
            goal_form.fields['player'].queryset = players_in_match
            if goal_form.is_valid():
                goal = goal_form.save(commit=False)
                goal.match = match
                try:
                    goal.full_clean()
                    goal.save()
                    messages.success(request, f"Đã thêm bàn thắng của {goal.player.full_name}.")
                except ValidationError as e:
                    messages.error(request, f"Lỗi: {e.messages[0]}")
                return redirect(reverse('organizations:manage_match', args=[pk]) + '?tab=goals')

        # === PHẦN SỬA LỖI CHO THẺ PHẠT ===
        elif action == 'add_card':
            card_form = CardForm(request.POST)
            card_form.fields['player'].queryset = players_in_match
            if card_form.is_valid():
                card = card_form.save(commit=False)
                card.match = match
                try:
                    card.full_clean()
                    card.save()
                    messages.success(request, f"Đã thêm thẻ phạt cho {card.player.full_name}.")
                except ValidationError as e:
                    messages.error(request, f"Lỗi: {e.messages[0]}")
                return redirect(reverse('organizations:manage_match', args=[pk]) + '?tab=cards')

    form = MatchUpdateForm(instance=match)
    goal_form = GoalForm()
    card_form = CardForm()
    goal_form.fields['player'].queryset = players_in_match
    card_form.fields['player'].queryset = players_in_match
    goals = match.goals.select_related('player', 'team').order_by('-minute')
    cards = match.cards.select_related('player', 'team').order_by('-minute')
    context = {
        'form': form,
        'goal_form': goal_form,
        'card_form': card_form,
        'match': match,
        'tournament': tournament,
        'organization': tournament.organization,
        'goals': goals,
        'cards': cards,
        'active_page': 'matches'
    }
    return render(request, 'organizations/manage_match.html', context)

@login_required
def delete_goal(request, pk):
    goal = get_object_or_404(Goal, pk=pk)
    match = goal.match
    organization = match.tournament.organization
    if not organization or not organization.members.filter(pk=request.user.pk).exists():
        return HttpResponseForbidden("Bạn không có quyền thực hiện hành động này.")
    if request.method == 'POST':
        player_name = goal.player.full_name
        goal.delete()
        messages.success(request, f"Đã xóa bàn thắng của {player_name}.")
    return redirect(reverse('organizations:manage_match', args=[match.pk]) + '?tab=goals')

@login_required
def delete_card(request, pk):
    card = get_object_or_404(Card, pk=pk)
    match = card.match
    organization = match.tournament.organization
    if not organization or not organization.members.filter(pk=request.user.pk).exists():
        return HttpResponseForbidden("Bạn không có quyền thực hiện hành động này.")
    if request.method == 'POST':
        player_name = card.player.full_name
        card.delete()
        messages.success(request, f"Đã xóa thẻ phạt của {player_name}.")
    return redirect(reverse('organizations:manage_match', args=[match.pk]) + '?tab=cards')


@login_required
@never_cache
def manage_knockout(request, pk):
    tournament = get_object_or_404(Tournament.objects.select_related('organization'), pk=pk)
    organization = tournament.organization

    # Kiểm tra quyền
    if not organization or not organization.members.filter(pk=request.user.pk).exists():
        return HttpResponseForbidden("Bạn không có quyền thực hiện hành động này.")

    # Lấy tất cả các đội đã được xếp bảng
    teams_in_groups = Team.objects.filter(tournament=tournament, group__isnull=False)
    if not teams_in_groups.exists():
        messages.warning(request, "Chưa có đội nào được xếp bảng để bắt đầu vòng loại trực tiếp.")
        return redirect('organizations:manage_tournament', pk=pk)

    # Lấy các trận knockout đã tồn tại
    knockout_matches = tournament.matches.filter(match_round__in=['QUARTER', 'SEMI', 'FINAL']).order_by('match_time')

    context = {
        'tournament': tournament,
        'organization': tournament.organization,
        'active_page': 'knockout', # <-- SỬA DÒNG NÀY
        'knockout_matches': knockout_matches,
    }

    return render(request, 'organizations/manage_knockout.html', context)
