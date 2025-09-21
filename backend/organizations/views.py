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
from django.utils import timezone
from .forms import SemiFinalCreationForm
from .forms import FinalCreationForm
from .forms import ThirdPlaceCreationForm

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

    if not organization or not organization.members.filter(pk=request.user.pk).exists():
        return HttpResponseForbidden("Bạn không có quyền thực hiện hành động này.")

    groups = tournament.groups.prefetch_related('teams').all()
    if not groups.exists():
        messages.warning(request, "Giải đấu chưa có bảng nào được tạo.")
        return redirect('organizations:manage_tournament', pk=pk)

    standings_by_group = {}
    qualified_teams_list = []
    for group in groups:
        standings = group.get_standings()
        standings_by_group[group.id] = {'name': group.name, 'standings': standings}
        qualified_teams_list.extend([s['team_obj'] for s in standings[:2]])
    
    qualified_teams_queryset = Team.objects.filter(id__in=[team.id for team in qualified_teams_list])

    semi_final_matches = tournament.matches.filter(match_round='SEMI', team1_score__isnull=False, team2_score__isnull=False)
    semi_final_winners = []
    semi_final_losers = [] # <-- MỚI: Danh sách đội thua
    if semi_final_matches.count() == 2:
        for match in semi_final_matches:
            if match.winner: semi_final_winners.append(match.winner)
            if match.loser: semi_final_losers.append(match.loser) # <-- MỚI: Thêm đội thua

    semi_final_winners_queryset = Team.objects.filter(id__in=[team.id for team in semi_final_winners])
    semi_final_losers_queryset = Team.objects.filter(id__in=[team.id for team in semi_final_losers]) # <-- MỚI

    semi_final_form, final_form, third_place_form = None, None, None

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'create_semi_finals':
            semi_final_form = SemiFinalCreationForm(request.POST, qualified_teams=qualified_teams_queryset)
            if semi_final_form.is_valid():
                # ... (logic tạo bán kết giữ nguyên)
                data = semi_final_form.cleaned_data
                tournament.matches.filter(match_round='SEMI').delete()
                Match.objects.create(tournament=tournament, match_round='SEMI', team1=data['sf1_team1'], team2=data['sf1_team2'], match_time=data['sf1_datetime'] or timezone.now() + timezone.timedelta(days=1))
                Match.objects.create(tournament=tournament, match_round='SEMI', team1=data['sf2_team1'], team2=data['sf2_team2'], match_time=data['sf2_datetime'] or timezone.now() + timezone.timedelta(days=1))
                messages.success(request, "Đã tạo thành công các cặp đấu Bán kết!")
                return redirect('organizations:manage_knockout', pk=pk)
        
        elif action == 'create_final':
            final_form = FinalCreationForm(request.POST, semi_final_winners=semi_final_winners_queryset)
            if final_form.is_valid():
                # ... (logic tạo chung kết giữ nguyên)
                data = final_form.cleaned_data
                tournament.matches.filter(match_round='FINAL').delete()
                Match.objects.create(tournament=tournament, match_round='FINAL', team1=data['final_team1'], team2=data['final_team2'], match_time=data['final_datetime'] or timezone.now() + timezone.timedelta(days=1))
                messages.success(request, "Đã tạo thành công trận Chung kết!")
                return redirect('organizations:manage_knockout', pk=pk)
        
        # === BẮT ĐẦU LOGIC MỚI CHO TRẬN TRANH HẠNG BA ===
        elif action == 'create_third_place':
            third_place_form = ThirdPlaceCreationForm(request.POST, semi_final_losers=semi_final_losers_queryset)
            if third_place_form.is_valid():
                data = third_place_form.cleaned_data
                tournament.matches.filter(match_round='THIRD_PLACE').delete()
                Match.objects.create(
                    tournament=tournament,
                    match_round='THIRD_PLACE',
                    team1=data['tp_team1'],
                    team2=data['tp_team2'],
                    match_time=data['tp_datetime'] or timezone.now() + timezone.timedelta(days=1)
                )
                messages.success(request, "Đã tạo thành công trận Tranh Hạng Ba!")
                return redirect('organizations:manage_knockout', pk=pk)
        # === KẾT THÚC LOGIC MỚI ===

    if not semi_final_form:
        # ... (logic khởi tạo form bán kết giữ nguyên)
        initial_semi = {}
        if len(standings_by_group) == 2:
             group_ids = list(standings_by_group.keys())
             g1_standings = standings_by_group[group_ids[0]]['standings']
             g2_standings = standings_by_group[group_ids[1]]['standings']
             if len(g1_standings) >= 2 and len(g2_standings) >= 2:
                 initial_semi = {'sf1_team1': g1_standings[0]['team_obj'].id, 'sf1_team2': g2_standings[1]['team_obj'].id, 'sf2_team1': g2_standings[0]['team_obj'].id, 'sf2_team2': g1_standings[1]['team_obj'].id}
        semi_final_form = SemiFinalCreationForm(qualified_teams=qualified_teams_queryset, initial=initial_semi)

    if not final_form:
        # ... (logic khởi tạo form chung kết giữ nguyên)
        initial_final = {}
        if len(semi_final_winners) == 2: initial_final = {'final_team1': semi_final_winners[0].id, 'final_team2': semi_final_winners[1].id}
        final_form = FinalCreationForm(semi_final_winners=semi_final_winners_queryset, initial=initial_final)

    # === KHỞI TẠO FORM TRANH HẠNG BA ===
    if not third_place_form:
        initial_third_place = {}
        if len(semi_final_losers) == 2:
            initial_third_place = {
                'tp_team1': semi_final_losers[0].id,
                'tp_team2': semi_final_losers[1].id
            }
        third_place_form = ThirdPlaceCreationForm(semi_final_losers=semi_final_losers_queryset, initial=initial_third_place)
    # === KẾT THÚC KHỞI TẠO ===

    group_matches_finished = tournament.matches.filter(match_round='GROUP', team1_score__isnull=False).exists()
    knockout_matches = tournament.matches.filter(match_round__in=['QUARTER', 'SEMI', 'THIRD_PLACE', 'FINAL']).order_by('match_time')

    context = {
        'tournament': tournament, 'organization': tournament.organization,
        'active_page': 'knockout', 'knockout_matches': knockout_matches,
        'standings_by_group': standings_by_group, 'qualified_teams': qualified_teams_list,
        'group_matches_finished': group_matches_finished,
        'semi_final_form': semi_final_form,
        'final_form': final_form,
        'third_place_form': third_place_form, # <-- GỬI FORM MỚI
        'semi_final_winners': semi_final_winners,
        'semi_final_losers': semi_final_losers, # <-- GỬI DANH SÁCH ĐỘI THUA
    }
    return render(request, 'organizations/manage_knockout.html', context)
