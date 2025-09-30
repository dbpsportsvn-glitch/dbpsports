# backend/organizations/views.py

from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache
from django.core.exceptions import ValidationError
from .models import Organization, Membership
from django.conf import settings
from django.http import HttpResponseForbidden
from django.contrib.auth.models import User
from django.contrib import messages
from django.db.models import Q
from collections import defaultdict
from tournaments.forms import TournamentForm
from tournaments.models import Tournament, Group, Team, Match, Goal, Card, Player, TournamentPhoto, Notification, TournamentStaff
from tournaments.utils import send_notification_email, send_schedule_notification
from .forms import AnnouncementForm
from tournaments.models import Announcement
from .forms import (
    OrganizationCreationForm, MemberInviteForm, 
    MatchUpdateForm, GoalForm, CardForm, QuarterFinalCreationForm, 
    SemiFinalCreationForm, FinalCreationForm, ThirdPlaceCreationForm, 
    MatchCreationForm, PlayerUpdateForm, TournamentStaffInviteForm
)
from django.utils import timezone
from django.db import transaction
from django.utils.http import url_has_allowed_host_and_scheme
from users.models import Role
from .forms import MatchMediaUpdateForm

# import cho thị trường công việc
from .models import JobPosting, JobApplication
from .forms import JobPostingForm, JobApplicationUpdateForm
from django.views.decorators.http import require_POST
from .models import ProfessionalReview
from .forms import ProfessionalReviewForm

# === HÀM KIỂM TRA QUYỀN MỚI ===

def user_is_org_member(user, organization):
    """Kiểm tra xem user có phải là thành viên (Owner/Admin) của BTC không."""
    if not user.is_authenticated or not organization:
        return False
    if user.is_staff:
        return True
    return organization.members.filter(pk=user.pk).exists()

def user_has_tournament_role(user, tournament, role_ids):
    """Kiểm tra xem user có vai trò cụ thể nào trong giải đấu không."""
    if not user.is_authenticated:
        return False
    # Đảm bảo role_ids luôn là một list/tuple để truy vấn an toàn
    if isinstance(role_ids, str):
        role_ids = [role_ids]
    return TournamentStaff.objects.filter(
        tournament=tournament,
        user=user,
        role_id__in=role_ids
    ).exists()

# === CẬP NHẬT CÁC HÀM KIỂM TRA CHỨC NĂNG ===

def user_can_manage_tournament(user, tournament):
    """Quyền quản lý toàn bộ giải đấu (Sửa cài đặt, tạo trận, duyệt đội...)."""
    # Chỉ Superuser, thành viên BTC, hoặc Quản lý Giải đấu mới có quyền này.
    return user_is_org_member(user, tournament.organization) or \
           user_has_tournament_role(user, tournament, ['TOURNAMENT_MANAGER'])

def user_can_control_match(user, match):
    """Quyền truy cập phòng Live Control (cập nhật tỉ số, sự kiện)."""
    # Bao gồm BTC, Quản lý giải, và cả Bình Luận Viên.
    allowed_roles = ['TOURNAMENT_MANAGER', 'COMMENTATOR']
    return user_is_org_member(user, match.tournament.organization) or \
           user_has_tournament_role(user, match.tournament, allowed_roles)

def user_can_upload_gallery(user, tournament):
    """Quyền tải ảnh và quản lý thư viện ảnh."""
    # Bao gồm BTC, Quản lý giải, Media và Nhiếp ảnh gia.
    allowed_roles = ['TOURNAMENT_MANAGER', 'MEDIA', 'PHOTOGRAPHER']
    return user_is_org_member(user, tournament.organization) or \
           user_has_tournament_role(user, tournament, allowed_roles)


def safe_redirect(request, default_url: str):
    next_url = request.GET.get('next')
    if next_url and url_has_allowed_host_and_scheme(
        next_url,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure()
    ):
        return redirect(next_url)
    return redirect(default_url)

# Helper: ưu tiên ?next= nếu hợp lệ, nếu không quay về default_url
def safe_redirect(request, default_url: str):
    next_url = request.GET.get('next')
    if next_url and url_has_allowed_host_and_scheme(
        next_url,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure()
    ):
        return redirect(next_url)
    return redirect(default_url)

#=================================

# === THAY THẾ TOÀN BỘ HÀM NÀY ===
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

    if request.method == 'POST':
        if 'invite_member' in request.POST:
            if request.user == organization.owner:
                invite_form = MemberInviteForm(request.POST)
                if invite_form.is_valid():
                    email = invite_form.cleaned_data['email']
                    user_to_invite = User.objects.get(email__iexact=email)
                    membership, created = Membership.objects.get_or_create(
                        organization=organization, user=user_to_invite,
                        defaults={'role': Membership.Role.ADMIN}
                    )
                    if created: 
                        messages.success(request, f"Đã thêm {user_to_invite.email} vào đơn vị.")
                    else: 
                        messages.warning(request, f"{user_to_invite.email} đã là thành viên.")
                else:
                    for field, errors in invite_form.errors.items():
                        for error in errors: messages.error(request, error)
            return redirect('organizations:dashboard')

    tournaments = organization.tournaments.all().order_by('-start_date')
    # Lấy danh sách thành viên để hiển thị trong tab mới
    members = Membership.objects.filter(organization=organization).select_related('user').order_by('role')
    # Form để mời thành viên
    invite_form = MemberInviteForm()

    context = {
        'organization': organization,
        'tournaments': tournaments,
        'members': members,
        'invite_form': invite_form,
    }
    return render(request, 'organizations/organization_dashboard.html', context)


def create_tournament(request):
    organization = Organization.objects.filter(members=request.user).first()
    if not organization:
        return redirect('organizations:dashboard')
    
    if request.method == 'POST':
        # SỬA DÒNG NÀY: Dùng TournamentForm thay vì TournamentCreationForm
        form = TournamentForm(request.POST, request.FILES)
        if form.is_valid():
            tournament = form.save(commit=False)
            tournament.organization = organization
            tournament.save()
            # Thêm thông báo thành công
            messages.success(request, f"Đã tạo thành công giải đấu '{tournament.name}'!")
            return redirect('organizations:dashboard')
    else:
        # VÀ SỬA DÒNG NÀY
        form = TournamentForm()
        
    context = {
        'form': form,
        'organization': organization
    }
    return render(request, 'organizations/create_tournament.html', context)


# Sắp Xếp các cặp đấu
@login_required
@never_cache
def manage_tournament(request, pk):
    tournament = get_object_or_404(Tournament.objects.select_related('organization'), pk=pk)
    
    if not user_can_manage_tournament(request.user, tournament):
        return HttpResponseForbidden("Bạn không có quyền truy cập trang quản lý này.")

    view_name = request.GET.get('view', 'overview')

    if request.method == 'POST':
        # (Toàn bộ logic xử lý POST không thay đổi, giữ nguyên như cũ)
        if 'quick_save_match' in request.POST:
            match_id = request.POST.get('quick_save_match')
            try:
                match = Match.objects.get(pk=match_id, tournament=tournament)
                score1_str = request.POST.get(f'score_team1_{match_id}')
                score2_str = request.POST.get(f'score_team2_{match_id}')
                
                s1 = int(score1_str) if score1_str and score1_str.isdigit() else None
                s2 = int(score2_str) if score2_str and score2_str.isdigit() else None

                match.team1_score = s1
                match.team2_score = s2
                match.save()
                messages.success(request, f"Đã lưu nhanh kết quả trận: {match}.")
            except (Match.DoesNotExist, ValueError):
                messages.error(request, "Có lỗi xảy ra khi lưu nhanh trận đấu.")
            return redirect(request.path_info + '?view=matches')
    
        if 'save_all_scores' in request.POST:
            match_ids = request.POST.getlist('match_ids')
            try:
                with transaction.atomic():
                    for match_id in match_ids:
                        match = Match.objects.get(pk=match_id, tournament=tournament)
                        score1_str = request.POST.get(f'score_team1_{match_id}')
                        score2_str = request.POST.get(f'score_team2_{match_id}')
                        
                        s1 = int(score1_str) if score1_str and score1_str.isdigit() else None
                        s2 = int(score2_str) if score2_str and score2_str.isdigit() else None

                        match.team1_score = s1
                        match.team2_score = s2
                        match.save()
                messages.success(request, "Đã cập nhật thành công tất cả tỉ số.")
            except (Match.DoesNotExist, ValueError):
                messages.error(request, "Có lỗi xảy ra khi cập nhật tỉ số.")
            return redirect(request.path_info + '?view=matches')

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
    if view_name == 'overview':
        all_teams = tournament.teams.all()
        unassigned_teams = all_teams.filter(payment_status='PAID', group__isnull=True)
        has_paid_teams = all_teams.filter(payment_status='PAID').exists()
        context['unassigned_teams'] = unassigned_teams
        context['has_paid_teams'] = has_paid_teams
        context['stats'] = {
            'total_teams': all_teams.count(),
            'pending_teams_count': all_teams.filter(payment_status='PENDING').count(),
            'total_matches': tournament.matches.count(),
        }
    
    elif view_name == 'teams':
        all_tournaments = tournament.organization.tournaments.all().order_by('-start_date')
        context['all_tournaments'] = all_tournaments
        search_query = request.GET.get('q', '')
        tournament_filter_id = request.GET.get('tournament_filter')
        context['search_query'] = search_query
        base_teams_qs = Team.objects.filter(tournament__organization=tournament.organization)
        if tournament_filter_id and tournament_filter_id.isdigit():
            base_teams_qs = base_teams_qs.filter(tournament_id=int(tournament_filter_id))
            context['selected_tournament_id'] = int(tournament_filter_id)
        if search_query:
            base_teams_qs = base_teams_qs.filter(name__icontains=search_query)
        context['unpaid_teams'] = base_teams_qs.filter(payment_status='UNPAID').select_related('captain', 'tournament')
        context['pending_teams'] = base_teams_qs.filter(payment_status='PENDING').select_related('captain', 'tournament')
        context['paid_teams'] = base_teams_qs.filter(payment_status='PAID').select_related('captain', 'tournament')

    elif view_name == 'groups':
        context['groups'] = tournament.groups.all().order_by('name')
        standings_by_group = {}
        for group in context['groups']:
            standings = group.get_standings()
            standings_by_group[group.id] = {'name': group.name, 'standings': standings}
        context['standings_by_group'] = standings_by_group
 
    elif view_name == 'matches':
        all_matches = tournament.matches.select_related('team1__group', 'team2__group').order_by('match_time')
        group_matches = all_matches.filter(match_round='GROUP')
        matches_by_group = defaultdict(list)
        for match in group_matches:
            if match.team1.group:
                matches_by_group[match.team1.group].append(match)
        sorted_matches_by_group = sorted(matches_by_group.items(), key=lambda item: item[0].name)
        context['sorted_matches_by_group'] = sorted_matches_by_group
        knockout_matches_list = list(all_matches.exclude(match_round='GROUP'))
        round_order = {'QUARTER': 1, 'SEMI': 2, 'THIRD_PLACE': 3, 'FINAL': 4}
        knockout_matches_list.sort(key=lambda m: round_order.get(m.match_round, 99))
        context['knockout_matches'] = knockout_matches_list

    # === PHẦN CẬP NHẬT CHÍNH NẰM Ở ĐÂY ===
    elif view_name == 'staff':
        context['active_page'] = 'staff'
        context['staff_invite_form'] = TournamentStaffInviteForm()
        # Lấy thêm `user__profile` để có thể truy cập avatar
        context['org_members'] = Membership.objects.filter(
            organization=tournament.organization
        ).select_related('user', 'user__profile').order_by('role')
        
        context['tournament_staff'] = TournamentStaff.objects.filter(
            tournament=tournament
        ).select_related('user', 'user__profile', 'role')
    # === KẾT THÚC CẬP NHẬT ===

    elif view_name == 'players':
        all_tournaments_in_org = tournament.organization.tournaments.all().order_by('-start_date')
        context['all_tournaments_in_org'] = all_tournaments_in_org
        players_qs = Player.objects.filter(team__tournament__organization=tournament.organization).select_related('team').order_by('team__tournament__name', 'team__name', 'full_name')
        tournament_filter_id = request.GET.get('tournament_filter')
        if tournament_filter_id and tournament_filter_id.isdigit():
            players_qs = players_qs.filter(team__tournament_id=int(tournament_filter_id))
            context['selected_tournament_id'] = int(tournament_filter_id)
        else:
            players_qs = players_qs.filter(team__tournament=tournament)
            context['selected_tournament_id'] = tournament.pk
        team_filter_id = request.GET.get('team_filter')
        if team_filter_id and team_filter_id.isdigit():
            players_qs = players_qs.filter(team_id=int(team_filter_id))
            context['selected_team_id'] = int(team_filter_id)
        search_query = request.GET.get('q', '')
        if search_query:
            players_qs = players_qs.filter(full_name__icontains=search_query)
            context['search_query'] = search_query
        context['players_list'] = players_qs
        selected_tourn_id = context.get('selected_tournament_id', tournament.pk)
        context['teams_in_tournament'] = Team.objects.filter(tournament_id=selected_tourn_id).order_by('name')

    elif view_name == 'announcements':
        context['announcements'] = Announcement.objects.filter(tournament=tournament).order_by('-created_at')

    return render(request, 'organizations/manage_tournament.html', context)

@login_required
def delete_group(request, pk):
    group = get_object_or_404(Group, pk=pk)
    tournament = group.tournament
    if not user_can_manage_tournament(request.user, tournament):
        return HttpResponseForbidden("Bạn không có quyền thực hiện hành động này.")
    default_url = f"{reverse('organizations:manage_tournament', args=[tournament.pk])}?view=groups"
    if request.method == 'POST':
        group.delete()
        messages.success(request, "Đã xoá bảng thành công.")
        return safe_redirect(request, default_url)
    return safe_redirect(request, default_url)

@login_required
def delete_tournament(request, pk):
    tournament = get_object_or_404(Tournament, pk=pk)
    # QUYỀN HẠN CAO NHẤT: Chỉ thành viên BTC gốc mới được xóa giải đấu
    if not tournament.organization or not tournament.organization.members.filter(pk=request.user.pk).exists():
        return HttpResponseForbidden("Chỉ thành viên Ban Tổ Chức gốc mới có quyền xóa giải đấu.")
    default_url = reverse('organizations:dashboard')
    if request.method == 'POST':
        tournament.delete()
        messages.success(request, "Đã xoá giải đấu.")
        return safe_redirect(request, default_url)
    return safe_redirect(request, default_url)

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
    default_url = reverse('organizations:dashboard')
    if tournament_id_to_return:
        default_url = f"{reverse('organizations:manage_tournament', args=[tournament_id_to_return])}?view=members"
    if request.method == 'POST':
        member_email = membership_to_delete.user.email
        membership_to_delete.delete()
        messages.success(request, f"Đã xóa thành viên {member_email} khỏi đơn vị.")
        return safe_redirect(request, default_url)
    return safe_redirect(request, default_url)

@login_required
@never_cache
def edit_tournament(request, pk):
    tournament = get_object_or_404(Tournament, pk=pk)
    
    # === DÒNG KIỂM TRA QUYỀN ĐÃ ĐƯỢC CẬP NHẬT ===
    if not user_can_manage_tournament(request.user, tournament):
        return HttpResponseForbidden("Bạn không có quyền truy cập trang này.")
    
    if request.method == 'POST':
        form = TournamentForm(request.POST, request.FILES, instance=tournament)
        if form.is_valid():
            form.save()
            messages.success(request, "Đã cập nhật thông tin giải đấu thành công!")
            return redirect('organizations:edit_tournament', pk=pk)
    else:
        form = TournamentForm(instance=tournament)
        
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

    # 1. KIỂM TRA QUYỀN HẠN (LOGIC MỚI)
    # Kiểm tra xem người dùng có phải là Quản lý/BTC không
    is_manager_or_btc = user_can_manage_tournament(request.user, tournament)
    # Kiểm tra xem người dùng có phải là Media của giải này không
    is_media_staff = TournamentStaff.objects.filter(
        tournament=tournament, user=request.user, role__id='MEDIA'
    ).exists()

    # Nếu không phải cả hai thì từ chối truy cập
    if not is_manager_or_btc and not is_media_staff:
        return HttpResponseForbidden("Bạn không có quyền thực hiện hành động này.")

    # 2. LẤY DỮ LIỆU CHUNG
    players_in_match = Player.objects.filter(team__in=[match.team1, match.team2]).select_related('team').order_by('team__name', 'full_name')
    teams_in_tournament = tournament.teams.all().order_by('name')

    # 3. CHỌN FORM PHÙ HỢP DỰA TRÊN VAI TRÒ (LOGIC MỚI ĐỂ SỬA LỖI)
    if is_media_staff and not is_manager_or_btc:
        # Nếu là Media (và không phải BTC/Quản lý), dùng form giới hạn
        form_class = MatchMediaUpdateForm
    else:
        # Ngược lại, dùng form đầy đủ quyền
        form_class = MatchUpdateForm

    # 4. XỬ LÝ KHI NGƯỜI DÙNG GỬI DỮ LIỆU (POST)
    if request.method == 'POST':
        action = request.POST.get('action')
        
        # Xử lý cập nhật thông tin chung/media
        if action == 'update_match':
            form = form_class(request.POST, request.FILES, instance=match)
            # Chỉ gán queryset cho các trường team nếu chúng tồn tại trong form
            if 'team1' in form.fields:
                form.fields['team1'].queryset = teams_in_tournament
            if 'team2' in form.fields:
                form.fields['team2'].queryset = teams_in_tournament
            
            if form.is_valid():
                form.save()
                messages.success(request, "Đã cập nhật thông tin trận đấu.")
                return redirect('organizations:manage_match', pk=match.pk)
        
        # Xử lý thêm bàn thắng (chỉ BTC/Quản lý mới có quyền)
        elif action == 'add_goal' and is_manager_or_btc:
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

        # Xử lý thêm thẻ phạt (chỉ BTC/Quản lý mới có quyền)
        elif action == 'add_card' and is_manager_or_btc:
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

    # 5. HIỂN THỊ TRANG (GET)
    form = form_class(instance=match)
    if 'team1' in form.fields:
        form.fields['team1'].queryset = teams_in_tournament
    if 'team2' in form.fields:
        form.fields['team2'].queryset = teams_in_tournament

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
        'active_page': 'matches',
        'is_manager_or_btc': is_manager_or_btc, # Gửi biến này để template ẩn/hiện tab
    }
    return render(request, 'organizations/manage_match.html', context)

@login_required
def delete_goal(request, pk):
    goal = get_object_or_404(Goal, pk=pk)
    if not user_can_manage_tournament(request.user, goal.match.tournament):
        return HttpResponseForbidden("Bạn không có quyền thực hiện hành động này.")
    default_url = reverse('organizations:manage_match', args=[match.pk]) + '?tab=goals'
    if request.method == 'POST':
        player_name = goal.player.full_name
        goal.delete()
        messages.success(request, f"Đã xóa bàn thắng của {player_name}.")
        return safe_redirect(request, default_url)
    return safe_redirect(request, default_url)

@login_required
def delete_card(request, pk):
    card = get_object_or_404(Card, pk=pk)
    if not user_can_manage_tournament(request.user, card.match.tournament):
        return HttpResponseForbidden("Bạn không có quyền thực hiện hành động này.")
    default_url = reverse('organizations:manage_match', args=[match.pk]) + '?tab=cards'
    if request.method == 'POST':
        player_name = card.player.full_name
        card.delete()
        messages.success(request, f"Đã xóa thẻ phạt của {player_name}.")
        return safe_redirect(request, default_url)
    return safe_redirect(request, default_url)


# backend/organizations/views.py

@login_required
@never_cache
def manage_knockout(request, pk):
    tournament = get_object_or_404(Tournament.objects.select_related('organization'), pk=pk)
    
    # === DÒNG KIỂM TRA QUYỀN ĐÃ ĐƯỢC CẬP NHẬT ===
    if not user_can_manage_tournament(request.user, tournament):
        return HttpResponseForbidden("Bạn không có quyền thực hiện hành động này.")

    groups = tournament.groups.prefetch_related('teams').all().order_by('name')

    # --- Lấy dữ liệu các đội và các vòng đấu ---
    standings_by_group = {}
    qualified_teams_list = []
    num_qualified_per_group = 2 # Mặc định lấy 2 đội mỗi bảng
    for group in groups:
        standings = group.get_standings()
        standings_by_group[group.id] = {'name': group.name, 'standings': standings}
        qualified_teams_list.extend([s['team_obj'] for s in standings[:num_qualified_per_group]])
    
    qualified_teams_queryset = Team.objects.filter(id__in=[team.id for team in qualified_teams_list])

    # Lấy đội thắng Tứ kết
    quarter_final_matches = tournament.matches.filter(match_round='QUARTER', team1_score__isnull=False, team2_score__isnull=False)
    quarter_final_winners = [match.winner for match in quarter_final_matches if match.winner]
    quarter_final_winners_queryset = Team.objects.filter(id__in=[team.id for team in quarter_final_winners])

    # Lấy đội thắng/thua Bán kết
    semi_final_matches = tournament.matches.filter(match_round='SEMI', team1_score__isnull=False, team2_score__isnull=False)
    semi_final_winners = [match.winner for match in semi_final_matches if match.winner]
    semi_final_losers = [match.loser for match in semi_final_matches if match.loser]
    semi_final_winners_queryset = Team.objects.filter(id__in=[team.id for team in semi_final_winners])
    semi_final_losers_queryset = Team.objects.filter(id__in=[team.id for team in semi_final_losers])

    # Khởi tạo các form
    quarter_final_form, semi_final_form, final_form, third_place_form = None, None, None, None

    # Xử lý POST request (giữ nguyên logic POST)
    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'create_quarter_finals':
            quarter_final_form = QuarterFinalCreationForm(request.POST, qualified_teams=qualified_teams_queryset)
            if quarter_final_form.is_valid():
                data = quarter_final_form.cleaned_data
                tournament.matches.filter(match_round='QUARTER').delete()
                for i in range(1, 5):
                    Match.objects.create(
                        tournament=tournament, match_round='QUARTER',
                        team1=data[f'qf{i}_team1'], team2=data[f'qf{i}_team2'],
                        match_time=data[f'qf{i}_datetime'] or timezone.now() + timezone.timedelta(days=1)
                    )
                messages.success(request, "Đã tạo thành công các cặp đấu Tứ kết!")
                # GỬI THÔNG BÁO
                send_schedule_notification(
                    tournament, Notification.NotificationType.SCHEDULE_CREATED,
                    f"Giải '{tournament.name}' có lịch Tứ kết",
                    "Các cặp đấu Tứ kết đã được thiết lập. Xem ngay!",
                    'tournament_detail'
                )                
                return redirect('organizations:manage_knockout', pk=pk)

        elif action == 'create_semi_finals':
            source_teams = quarter_final_winners_queryset if quarter_final_matches.exists() else qualified_teams_queryset
            semi_final_form = SemiFinalCreationForm(request.POST, quarter_final_winners=source_teams)
            if semi_final_form.is_valid():
                data = semi_final_form.cleaned_data
                tournament.matches.filter(match_round='SEMI').delete()
                Match.objects.create(tournament=tournament, match_round='SEMI', team1=data['sf1_team1'], team2=data['sf1_team2'], match_time=data['sf1_datetime'] or timezone.now() + timezone.timedelta(days=1))
                Match.objects.create(tournament=tournament, match_round='SEMI', team1=data['sf2_team1'], team2=data['sf2_team2'], match_time=data['sf2_datetime'] or timezone.now() + timezone.timedelta(days=1))
                messages.success(request, "Đã tạo thành công các cặp đấu Bán kết!")
                # GỬI THÔNG BÁO
                send_schedule_notification(
                    tournament, Notification.NotificationType.SCHEDULE_CREATED,
                    f"Giải '{tournament.name}' có lịch Bán kết",
                    "Các cặp đấu Bán kết đã được thiết lập. Xem ngay!",
                    'tournament_detail'
                )                
                return redirect('organizations:manage_knockout', pk=pk)
        
        elif action == 'create_final':
            final_form = FinalCreationForm(request.POST, semi_final_winners=semi_final_winners_queryset)
            if final_form.is_valid():
                data = final_form.cleaned_data
                tournament.matches.filter(match_round='FINAL').delete()
                Match.objects.create(tournament=tournament, match_round='FINAL', team1=data['final_team1'], team2=data['final_team2'], match_time=data['final_datetime'] or timezone.now() + timezone.timedelta(days=1))
                messages.success(request, "Đã tạo thành công trận Chung kết!")
                # GỬI THÔNG BÁO
                send_schedule_notification(
                    tournament, Notification.NotificationType.SCHEDULE_CREATED,
                    f"Giải '{tournament.name}' có lịch Chung kết",
                    "Trận Chung kết đã được thiết lập. Xem ngay!",
                    'tournament_detail'
                )                
                return redirect('organizations:manage_knockout', pk=pk)
        
        elif action == 'create_third_place':
            third_place_form = ThirdPlaceCreationForm(request.POST, semi_final_losers=semi_final_losers_queryset)
            if third_place_form.is_valid():
                data = third_place_form.cleaned_data
                tournament.matches.filter(match_round='THIRD_PLACE').delete()
                Match.objects.create(
                    tournament=tournament, match_round='THIRD_PLACE',
                    team1=data['tp_team1'], team2=data['tp_team2'],
                    match_time=data['tp_datetime'] or timezone.now() + timezone.timedelta(days=1)
                )
                messages.success(request, "Đã tạo thành công trận Tranh Hạng Ba!")
                # GỬI THÔNG BÁO
                send_schedule_notification(
                    tournament, Notification.NotificationType.SCHEDULE_CREATED,
                    f"Giải '{tournament.name}' có lịch Tranh Hạng Ba",
                    "Trận Tranh Hạng Ba đã được thiết lập. Xem ngay!",
                    'tournament_detail'
                )                
                return redirect('organizations:manage_knockout', pk=pk)

    # Khởi tạo form cho GET request
    if not quarter_final_form:
        # === LOGIC MỚI: TỰ ĐỘNG XẾP CẶP TỨ KẾT ===
        initial_qf = {}
        if len(qualified_teams_list) >= 8 and not tournament.matches.filter(match_round='QUARTER').exists():
            # Logic xếp cặp chéo kinh điển (giả định 4 bảng A, B, C, D)
            # A1 vs B2, B1 vs A2, C1 vs D2, D1 vs C2
            # Vị trí trong list: 0=A1, 1=A2, 2=B1, 3=B2, 4=C1, 5=C2, 6=D1, 7=D2
            initial_qf = {
                'qf1_team1': qualified_teams_list[0].id, 'qf1_team2': qualified_teams_list[3].id,
                'qf2_team1': qualified_teams_list[2].id, 'qf2_team2': qualified_teams_list[1].id,
                'qf3_team1': qualified_teams_list[4].id, 'qf3_team2': qualified_teams_list[7].id,
                'qf4_team1': qualified_teams_list[6].id, 'qf4_team2': qualified_teams_list[5].id,
            }
        quarter_final_form = QuarterFinalCreationForm(
            qualified_teams=qualified_teams_queryset, 
            initial=initial_qf
        )
    
    if not semi_final_form:
        source_teams_for_semi = quarter_final_winners_queryset if quarter_final_matches.exists() else qualified_teams_queryset
        initial_semi = {}
        if quarter_final_matches.exists() and len(quarter_final_winners) == 4:
            initial_semi = {
                'sf1_team1': quarter_final_winners[0].id, 'sf1_team2': quarter_final_winners[1].id, 
                'sf2_team1': quarter_final_winners[2].id, 'sf2_team2': quarter_final_winners[3].id
            }
        semi_final_form = SemiFinalCreationForm(quarter_final_winners=source_teams_for_semi, initial=initial_semi)

    if not final_form:
        initial_final = {}
        if len(semi_final_winners) == 2:
            initial_final = {'final_team1': semi_final_winners[0].id, 'final_team2': semi_final_winners[1].id}
        final_form = FinalCreationForm(semi_final_winners=semi_final_winners_queryset, initial=initial_final)

    if not third_place_form:
        initial_third_place = {}
        if len(semi_final_losers) == 2:
            initial_third_place = {'tp_team1': semi_final_losers[0].id, 'tp_team2': semi_final_losers[1].id}
        third_place_form = ThirdPlaceCreationForm(semi_final_losers=semi_final_losers_queryset, initial=initial_third_place)

    group_matches_finished = tournament.matches.filter(match_round='GROUP', team1_score__isnull=False).exists()
    knockout_matches = tournament.matches.filter(match_round__in=['QUARTER', 'SEMI', 'THIRD_PLACE', 'FINAL']).order_by('match_time')

    context = {
        'tournament': tournament, 'organization': tournament.organization,
        'active_page': 'knockout', 'knockout_matches': knockout_matches,
        'standings_by_group': standings_by_group, 'qualified_teams': qualified_teams_list,
        'group_matches_finished': group_matches_finished,
        
        'quarter_final_form': quarter_final_form,
        'quarter_final_winners': quarter_final_winners,
        
        'semi_final_form': semi_final_form,
        'semi_final_winners': semi_final_winners,
        'semi_final_losers': semi_final_losers,
        
        'final_form': final_form,
        'third_place_form': third_place_form,
    }
    return render(request, 'organizations/manage_knockout.html', context)

@login_required
def delete_photo(request, pk):
    photo = get_object_or_404(TournamentPhoto, pk=pk)
    tournament = photo.tournament
    organization = tournament.organization

    # Kiểm tra quyền: chỉ BTC hoặc superuser mới được xóa
    is_organizer = organization and request.user in organization.members.all()
    if not request.user.is_superuser and not is_organizer:
        return HttpResponseForbidden("Bạn không có quyền thực hiện hành động này.")

    default_url = reverse('tournament_detail', args=[tournament.pk]) + '?tab=gallery'
    if request.method == 'POST':
        # Xóa file ảnh vật lý khỏi server
        photo.image.delete(save=False)
        # Xóa bản ghi trong database
        photo.delete()
        messages.success(request, "Đã xóa ảnh thành công.")
        # Chuyển hướng người dùng về lại tab thư viện ảnh (hoặc ?next= nếu có)
        return safe_redirect(request, default_url)

    # Chuyển hướng về tab thư viện
    return safe_redirect(request, default_url)

@login_required
def delete_all_photos(request, tournament_pk):
    tournament = get_object_or_404(Tournament, pk=tournament_pk)
    organization = tournament.organization

    # Kiểm tra quyền
    is_organizer = organization and request.user in organization.members.all()
    if not request.user.is_superuser and not is_organizer:
        return HttpResponseForbidden("Bạn không có quyền thực hiện hành động này.")

    default_url = reverse('tournament_detail', args=[tournament.pk]) + '?tab=gallery'
    if request.method == 'POST':
        photos = tournament.photos.all()
        photo_count = photos.count()

        if photo_count > 0:
            # Xóa các file vật lý trước
            for photo in photos:
                photo.image.delete(save=False)
            
            # Xóa các bản ghi trong database
            photos.delete()
            messages.success(request, f"Đã xóa thành công toàn bộ {photo_count} ảnh.")
        else:
            messages.info(request, "Thư viện ảnh đã trống.")

    # Chuyển hướng về tab thư viện
    return safe_redirect(request, default_url)


# XOÁ TRẬN ĐẤU CỦA BTC
@login_required
def delete_match(request, pk):
    match = get_object_or_404(Match, pk=pk)
    tournament = match.tournament
    
    # Kiểm tra quyền của người dùng
    if not tournament.organization or not tournament.organization.members.filter(pk=request.user.pk).exists():
        return HttpResponseForbidden("Bạn không có quyền thực hiện hành động này.")

    default_url = f"{reverse('organizations:manage_tournament', args=[tournament.pk])}?view=matches"
    if request.method == 'POST':
        match_name = f"{match.team1.name} vs {match.team2.name}"
        match.delete()
        messages.success(request, f"Đã xóa thành công trận đấu: {match_name}.")
        # Quay trở lại trang quản lý trận đấu của giải (hoặc ?next= nếu có)
        return safe_redirect(request, default_url)

    # Nếu không phải POST request, đơn giản là quay về trang trước/đúng tab
    return safe_redirect(request, default_url)


# === HIỂN THỊ FROM TẠO TRẬN ĐẤU CỦA BTC ===
@login_required
@never_cache
def create_match(request, tournament_pk):
    tournament = get_object_or_404(Tournament, pk=tournament_pk)
    
    # Kiểm tra quyền
    if not tournament.organization or not tournament.organization.members.filter(pk=request.user.pk).exists():
        return HttpResponseForbidden("Bạn không có quyền thực hiện hành động này.")

    teams_in_tournament = tournament.teams.all().order_by('name')

    if request.method == 'POST':
        form = MatchCreationForm(request.POST)
        # Cung cấp queryset cho form trước khi validate
        form.fields['team1'].queryset = teams_in_tournament
        form.fields['team2'].queryset = teams_in_tournament

        if form.is_valid():
            match = form.save(commit=False)
            match.tournament = tournament
            match.save()
            messages.success(request, "Đã tạo trận đấu mới thành công!")
            default_url = f"{reverse('organizations:manage_tournament', args=[tournament.pk])}?view=matches"
            return safe_redirect(request, default_url)
    else:
        form = MatchCreationForm()
        # Cung cấp queryset cho form khi hiển thị lần đầu
        form.fields['team1'].queryset = teams_in_tournament
        form.fields['team2'].queryset = teams_in_tournament

    context = {
        'form': form,
        'tournament': tournament,
        'organization': tournament.organization,
        'active_page': 'matches' # Để giữ cho menu được highlight đúng
    }
    return render(request, 'organizations/create_match.html', context)

# === XOÁ ĐỘI ĐĂNG KÝ ===
@login_required
def delete_team(request, pk):
    team = get_object_or_404(Team, pk=pk)
    tournament = team.tournament
    
    # Kiểm tra quyền của người dùng (phải là thành viên BTC của giải đấu đó)
    if not tournament.organization or not tournament.organization.members.filter(pk=request.user.pk).exists():
        return HttpResponseForbidden("Bạn không có quyền thực hiện hành động này.")

    # URL để quay lại trang quản lý đội
    default_url = f"{reverse('organizations:manage_tournament', args=[tournament.pk])}?view=teams"
    
    if request.method == 'POST':
        team_name = team.name
        team.delete()
        messages.success(request, f"Đã xóa thành công đội: {team_name}.")
        return safe_redirect(request, default_url)

    # Nếu không phải POST request, chỉ đơn giản là quay về trang trước
    return safe_redirect(request, default_url)

@login_required
@never_cache
def edit_player(request, pk):
    player = get_object_or_404(Player.objects.select_related('team__tournament__organization'), pk=pk)
    tournament = player.team.tournament
    organization = tournament.organization

    if not organization or not organization.members.filter(pk=request.user.pk).exists():
        return HttpResponseForbidden("Bạn không có quyền thực hiện hành động này.")

    # === LOGIC KIỂM TRA MỚI CHO BTC ===
    can_edit = player.votes == 0 and player.edit_count < 3
    if not can_edit:
        if player.votes > 0:
            messages.error(request, f"Không thể chỉnh sửa. Cầu thủ {player.full_name} đã có phiếu bầu.")
        else:
            messages.error(request, f"Không thể chỉnh sửa. Đã hết số lần cho phép (3 lần) cho cầu thủ {player.full_name}.")
        return redirect(f"{reverse('organizations:manage_tournament', args=[tournament.pk])}?view=players")
    # === KẾT THÚC LOGIC MỚI ===

    if request.method == 'POST':
        form = PlayerUpdateForm(request.POST, request.FILES, instance=player)
        if form.is_valid():
            # Tăng số lần chỉnh sửa trước khi lưu
            player.edit_count += 1
            form.save()
            remaining = 3 - player.edit_count
            messages.success(request, f"Đã cập nhật thành công thông tin cho cầu thủ {player.full_name}. Số lần sửa còn lại: {remaining}.")
            return redirect(f"{reverse('organizations:manage_tournament', args=[tournament.pk])}?view=players")
    else:
        form = PlayerUpdateForm(instance=player)

    context = {
        'form': form,
        'player': player,
        'tournament': tournament,
        'organization': organization,
        'active_page': 'players',
        'remaining_edits': 3 - player.edit_count, # Gửi số lần sửa còn lại
    }
    return render(request, 'organizations/edit_player.html', context)

@login_required
def delete_player(request, pk):
    player = get_object_or_404(Player.objects.select_related('team__tournament__organization'), pk=pk)
    tournament = player.team.tournament
    organization = tournament.organization

    # Kiểm tra quyền
    if not organization or not organization.members.filter(pk=request.user.pk).exists():
        return HttpResponseForbidden("Bạn không có quyền thực hiện hành động này.")

    default_url = f"{reverse('organizations:manage_tournament', args=[tournament.pk])}?view=players"
    if request.method == 'POST':
        player_name = player.full_name
        player.delete()
        messages.success(request, f"Đã xóa thành công cầu thủ {player_name}.")
        return safe_redirect(request, default_url)

    return safe_redirect(request, default_url)

# === THÊM CÁC HÀM MỚI VÀO CUỐI FILE ===
@login_required
@never_cache
def create_announcement(request, tournament_pk):
    tournament = get_object_or_404(Tournament, pk=tournament_pk)
    # Kiểm tra quyền
    if not tournament.organization or request.user not in tournament.organization.members.all():
        return HttpResponseForbidden("Bạn không có quyền truy cập.")

    if request.method == 'POST':
        form = AnnouncementForm(request.POST)
        if form.is_valid():
            announcement = form.save(commit=False)
            announcement.tournament = tournament
            announcement.save()
            messages.success(request, "Đã tạo thông báo mới thành công!")
            return redirect(f"{reverse('organizations:manage_tournament', args=[tournament_pk])}?view=announcements")
    else:
        form = AnnouncementForm()

    context = {
        'form': form,
        'tournament': tournament,
        'organization': tournament.organization
    }
    return render(request, 'organizations/announcement_form.html', context)

@login_required
@never_cache
def edit_announcement(request, pk):
    announcement = get_object_or_404(Announcement, pk=pk)
    tournament = announcement.tournament
    # Kiểm tra quyền
    if not tournament.organization or request.user not in tournament.organization.members.all():
        return HttpResponseForbidden("Bạn không có quyền truy cập.")

    if request.method == 'POST':
        form = AnnouncementForm(request.POST, instance=announcement)
        if form.is_valid():
            form.save()
            messages.success(request, "Đã cập nhật thông báo thành công!")
            return redirect(f"{reverse('organizations:manage_tournament', args=[tournament.pk])}?view=announcements")
    else:
        form = AnnouncementForm(instance=announcement)

    context = {
        'form': form,
        'tournament': tournament,
        'organization': tournament.organization
    }
    return render(request, 'organizations/announcement_form.html', context)

@login_required
def delete_announcement(request, pk):
    announcement = get_object_or_404(Announcement, pk=pk)
    tournament = announcement.tournament
    # Kiểm tra quyền
    if not tournament.organization or request.user not in tournament.organization.members.all():
        return HttpResponseForbidden("Bạn không có quyền truy cập.")

    if request.method == 'POST':
        announcement.delete()
        messages.success(request, "Đã xóa thông báo thành công.")
        return redirect(f"{reverse('organizations:manage_tournament', args=[tournament.pk])}?view=announcements")

    # === DÒNG SỬA LỖI NẰM Ở ĐÂY ===
    # Thêm 'tournament' và 'organization' vào context để template có thể dùng
    context = {
        'announcement': announcement,
        'tournament': tournament,
        'organization': tournament.organization
    }
    return render(request, 'organizations/announcement_confirm_delete.html', context)


@login_required
def send_announcement_email(request, pk):
    announcement = get_object_or_404(Announcement, pk=pk)
    tournament = announcement.tournament
    # Kiểm tra quyền
    if not tournament.organization or request.user not in tournament.organization.members.all():
        return HttpResponseForbidden("Bạn không có quyền truy cập.")

    if not announcement.is_published:
        messages.warning(request, "Thông báo này là bản nháp và chưa được công khai nên không thể gửi.")
        return redirect(f"{reverse('organizations:manage_tournament', args=[tournament.pk])}?view=announcements")
    
    # Lấy danh sách email đội trưởng
    captains = Team.objects.filter(tournament=tournament, payment_status='PAID').select_related('captain')
    recipient_list = {c.captain.email for c in captains if c.captain.email}

    if recipient_list:
        success = send_notification_email(
            subject=f"[Thông báo] {tournament.name}: {announcement.title}",
            template_name='tournaments/emails/announcement_notification.html',
            context={'announcement': announcement},
            recipient_list=list(recipient_list),
            request=request
        )
        if success:
            messages.success(request, f"Đã gửi thành công email thông báo đến {len(recipient_list)} đội trưởng.")
    else:
        messages.warning(request, "Không tìm thấy email của đội trưởng nào đã đăng ký thành công để gửi.")

    return redirect(f"{reverse('organizations:manage_tournament', args=[tournament.pk])}?view=announcements")

# === CÁC HÀM MỚI ĐỂ QUẢN LÝ NHÂN SỰ CHUYÊN MÔN ===
@login_required
def add_tournament_staff(request, tournament_pk):
    tournament = get_object_or_404(Tournament, pk=tournament_pk)
    # Chỉ BTC gốc mới có quyền thêm/xóa nhân sự
    if not tournament.organization or request.user not in tournament.organization.members.all():
        return HttpResponseForbidden("Bạn không có quyền thực hiện hành động này.")

    if request.method == 'POST':
        form = TournamentStaffInviteForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            role = form.cleaned_data['role']
            user_to_add = User.objects.get(email__iexact=email)

            staff, created = TournamentStaff.objects.get_or_create(
                tournament=tournament,
                user=user_to_add,
                role=role
            )
            if created:
                messages.success(request, f"Đã thêm {user_to_add.get_full_name() or user_to_add.username} với vai trò {role.name} vào giải đấu.")
            else:
                messages.warning(request, f"{user_to_add.get_full_name() or user_to_add.username} đã có vai trò này trong giải đấu.")
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{form.fields[field].label}: {error}")
    
    return redirect(f"{reverse('organizations:manage_tournament', args=[tournament_pk])}?view=staff")

@login_required
def remove_tournament_staff(request, pk):
    staff_entry = get_object_or_404(TournamentStaff, pk=pk)
    tournament = staff_entry.tournament
    # Chỉ BTC gốc mới có quyền thêm/xóa nhân sự
    if not tournament.organization or request.user not in tournament.organization.members.all():
        return HttpResponseForbidden("Bạn không có quyền thực hiện hành động này.")

    if request.method == 'POST':
        staff_entry.delete()
        messages.success(request, "Đã xóa thành viên khỏi đội ngũ chuyên môn của giải đấu.")
    
    return redirect(f"{reverse('organizations:manage_tournament', args=[tournament.pk])}?view=staff")    


# === 3 HÀM VIEW CHO THỊ TRƯỜNG CÔNG VIỆC ===
@login_required
@never_cache
def manage_jobs_view(request, tournament_pk):
    tournament = get_object_or_404(Tournament, pk=tournament_pk)
    if not user_can_manage_tournament(request.user, tournament):
        return HttpResponseForbidden("Bạn không có quyền truy cập.")

    if request.method == 'POST':
        form = JobPostingForm(request.POST)
        if form.is_valid():
            job = form.save(commit=False)
            job.tournament = tournament
            job.save()
            messages.success(request, "Đã đăng tin tuyển dụng mới thành công!")
            return redirect('organizations:manage_jobs', tournament_pk=tournament.pk)
    else:
        form = JobPostingForm()

    jobs = JobPosting.objects.filter(tournament=tournament).prefetch_related('applications')
    context = {
        'tournament': tournament,
        'organization': tournament.organization,
        'jobs': jobs,
        'form': form,
        'active_page': 'jobs', # Để highlight menu
    }
    return render(request, 'organizations/manage_jobs.html', context)

@login_required
@never_cache
def edit_job_view(request, pk):
    job = get_object_or_404(JobPosting, pk=pk)
    tournament = job.tournament
    if not user_can_manage_tournament(request.user, tournament):
        return HttpResponseForbidden("Bạn không có quyền truy cập.")

    if request.method == 'POST':
        form = JobPostingForm(request.POST, instance=job)
        if form.is_valid():
            form.save()
            messages.success(request, "Đã cập nhật tin tuyển dụng.")
            return redirect('organizations:manage_jobs', tournament_pk=tournament.pk)
    else:
        form = JobPostingForm(instance=job)
    
    context = {
        'form': form,
        'job': job,
        'tournament': tournament,
        'organization': tournament.organization,
        'active_page': 'jobs',
    }
    return render(request, 'organizations/edit_job.html', context)


@login_required
@require_POST
def update_application_status_view(request, pk):
    application = get_object_or_404(JobApplication.objects.select_related('applicant', 'job__tournament'), pk=pk)
    tournament = application.job.tournament
    if not user_can_manage_tournament(request.user, tournament):
        return HttpResponseForbidden("Bạn không có quyền truy cập.")
    
    form = JobApplicationUpdateForm(request.POST, instance=application)
    if form.is_valid():
        updated_application = form.save()
        messages.success(request, "Đã cập nhật trạng thái đơn ứng tuyển.")

        applicant = updated_application.applicant
        job = updated_application.job
        status_display = updated_application.get_status_display()
        notification_title = f"Cập nhật trạng thái ứng tuyển"
        notification_message = f"Đơn ứng tuyển của bạn cho vị trí '{job.title}' đã được cập nhật thành: {status_display}."
        notification_url = request.build_absolute_uri(reverse('job_detail', kwargs={'pk': job.pk}))

        # Gửi thông báo trên web (đã có)
        Notification.objects.create(
            user=applicant, title=notification_title, message=notification_message, related_url=notification_url
        )

        # === BẮT ĐẦU NÂNG CẤP: GỬI EMAIL ===
        if applicant.email:
            send_notification_email(
                subject=f"[DBP Sports] {notification_title}",
                template_name='organizations/emails/application_status_update.html',
                context={
                    'job': job,
                    'applicant': applicant,
                    'application': updated_application
                },
                recipient_list=[applicant.email],
                request=request
            )
        # === KẾT THÚC NÂNG CẤP ===
    
    return redirect('organizations:manage_jobs', tournament_pk=tournament.pk)

# === Rivew cong viec ===
@login_required
@never_cache
def create_review_view(request, application_pk):
    application = get_object_or_404(
        JobApplication.objects.select_related('job__tournament', 'applicant'), 
        pk=application_pk
    )
    tournament = application.job.tournament

    # Kiểm tra quyền
    if not user_can_manage_tournament(request.user, tournament):
        return HttpResponseForbidden("Bạn không có quyền truy cập.")
    
    # Kiểm tra điều kiện hợp lệ
    if application.status != 'APPROVED':
        messages.error(request, "Bạn chỉ có thể đánh giá các ứng viên đã được 'Chấp thuận'.")
        return redirect('organizations:manage_jobs', tournament_pk=tournament.pk)
    
    if hasattr(application, 'review'):
        messages.warning(request, "Bạn đã đánh giá cho công việc này rồi.")
        return redirect('organizations:manage_jobs', tournament_pk=tournament.pk)

    if request.method == 'POST':
        form = ProfessionalReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.job_application = application
            review.reviewer = request.user
            review.reviewee = application.applicant
            review.save()
            messages.success(request, f"Cảm ơn bạn đã gửi đánh giá cho {application.applicant.username}.")
            return redirect('organizations:manage_jobs', tournament_pk=tournament.pk)
    else:
        form = ProfessionalReviewForm()

    context = {
        'form': form,
        'application': application,
        'tournament': tournament,
        'organization': tournament.organization,
        'active_page': 'jobs',
    }
    return render(request, 'organizations/create_review.html', context)    