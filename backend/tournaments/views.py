# Python Standard Library
import json
import random
from collections import defaultdict
from datetime import datetime, time, timedelta
from itertools import combinations

# Django Core
from django.conf import settings
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.db.models import Count, Prefetch, Q, Sum
from django.http import HttpResponseForbidden, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.cache import never_cache

# Local Application Imports
from organizations.models import Organization

from .forms import (CommentForm, GalleryURLForm, PaymentProofForm,
                    PlayerCreationForm, ScheduleGenerationForm,
                    TeamCreationForm)
from .models import (Announcement, Card, Goal, Group, HomeBanner, Lineup, Match,
                     Player, Team, Tournament, TournamentPhoto, MAX_STARTERS)
from .utils import send_notification_email


#==================================

def home(request):
    # Giải chưa kết thúc
    active_tournaments = Tournament.objects.exclude(status='FINISHED').order_by('start_date')

    # Lấy mọi banner đang bật
    banners = HomeBanner.objects.filter(is_active=True).order_by('order', 'id')

    return render(
        request,
        'tournaments/home.html',
        {'tournaments_list': active_tournaments, 'banners': banners}
    )

def tournaments_active(request):
    # Lấy tham số lọc từ URL (ví dụ: ?region=MIEN_BAC)
    region_filter = request.GET.get('region', '')
    org_filter = request.GET.get('org', '')

    # Bắt đầu với việc lấy tất cả các giải đang hoạt động
    tournaments_list = Tournament.objects.exclude(status='FINISHED').select_related('organization').order_by('-start_date')

    # Áp dụng bộ lọc nếu có
    if region_filter:
        tournaments_list = tournaments_list.filter(region=region_filter)
    
    if org_filter:
        tournaments_list = tournaments_list.filter(organization__id=org_filter)

    # Lấy danh sách các đơn vị tổ chức có giải đấu để đưa vào bộ lọc
    active_orgs_ids = tournaments_list.values_list('organization__id', flat=True).distinct()
    all_organizations = Organization.objects.filter(id__in=active_orgs_ids).order_by('name')

    context = {
        'tournaments': tournaments_list,
        'all_organizations': all_organizations, # Gửi danh sách đơn vị ra template
        'all_regions': Tournament.Region.choices, # Gửi danh sách khu vực ra template
        'current_region': region_filter, # Giữ lại lựa chọn của người dùng
        'current_org': org_filter, # Giữ lại lựa chọn của người dùng
    }
    return render(request, "tournaments/active_list.html", context)


@never_cache
def livestream_view(request, pk=None):
    now = timezone.now()
    live_match = None

    if pk:
        live_match = get_object_or_404(Match.objects.select_related('tournament'), pk=pk)
    else:
        live_match = Match.objects.select_related('tournament').filter(
            livestream_url__isnull=False,
            match_time__lte=now
        ).order_by('-match_time').first()

    # Xử lý logic bình luận
    comments = []
    comment_form = CommentForm()

    if live_match:
        # Xử lý khi người dùng gửi bình luận mới (POST request)
        if request.method == 'POST' and request.user.is_authenticated:
            form = CommentForm(request.POST)
            if form.is_valid():
                new_comment = form.save(commit=False)
                new_comment.match = live_match
                new_comment.user = request.user
                new_comment.save()
                # Chuyển hướng về chính trang này để tránh gửi lại form
                return redirect('livestream_match', pk=live_match.pk)
        
        # Lấy danh sách bình luận để hiển thị
        comments = live_match.comments.select_related('user').all()

    # Logic lấy các trận sắp diễn ra và ticker text không đổi
    qs = Match.objects.filter(
        team1_score__isnull=True,
        team2_score__isnull=True,
        match_time__gte=now
    )
    if live_match:
        qs = qs.filter(tournament=live_match.tournament).exclude(pk=live_match.pk)
    upcoming_matches = qs.order_by('match_time')[:12]

    ticker_text_to_display = "Chào mừng tới DBP Sports • Liên hệ quảng cáo: 09xx xxx xxx"
    if live_match and live_match.ticker_text:
        ticker_text_to_display = live_match.ticker_text

    context = {
        "live_match": live_match,
        "upcoming_matches": upcoming_matches,
        "ticker_text": ticker_text_to_display,
        "comments": comments, # Gửi comments ra template
        "comment_form": comment_form, # Gửi form ra template
    }
    return render(request, "tournaments/livestream.html", context)

def shop_view(request):
    return render(request, 'tournaments/shop.html')

@never_cache
def tournament_detail(request, pk):
    tournament = get_object_or_404(
        Tournament.objects.prefetch_related(
            Prefetch('groups', queryset=Group.objects.order_by('name').prefetch_related(
                Prefetch('teams', queryset=Team.objects.select_related('captain'))
            )),
            'photos'
        ),
        pk=pk
    )
    
    is_organizer = False
    if request.user.is_authenticated and tournament.organization:
        if tournament.organization.members.filter(pk=request.user.pk).exists():
            is_organizer = True

    all_matches = tournament.matches.select_related('team1', 'team2').order_by('match_time')
    group_matches = all_matches.filter(match_round='GROUP')
    unassigned_teams = tournament.teams.filter(payment_status='PAID', group__isnull=True)

    # === BẮT ĐẦU PHẦN CẬP NHẬT LOGIC KNOCKOUT ===
    all_knockout_matches = list(all_matches.filter(
        match_round__in=['QUARTER', 'SEMI', 'THIRD_PLACE', 'FINAL']
    ).order_by('match_time'))

    quarter_finals = [m for m in all_knockout_matches if m.match_round == 'QUARTER']
    semi_finals = [m for m in all_knockout_matches if m.match_round == 'SEMI']
    third_place_match = next((m for m in all_knockout_matches if m.match_round == 'THIRD_PLACE'), None)
    final_match = next((m for m in all_knockout_matches if m.match_round == 'FINAL'), None)

    while len(quarter_finals) < 4:
        quarter_finals.append(None)
    while len(semi_finals) < 2:
        semi_finals.append(None)

    knockout_data = {
        'quarter_final_1': quarter_finals[0],
        'quarter_final_2': quarter_finals[1],
        'quarter_final_3': quarter_finals[2],
        'quarter_final_4': quarter_finals[3],
        'semi_final_1': semi_finals[0],
        'semi_final_2': semi_finals[1],
        'third_place_match': third_place_match,
        'final_match': final_match,
    }
    # === KẾT THÚC PHẦN CẬP NHẬT LOGIC KNOCKOUT ===

    # Phần tính toán bảng xếp hạng (giữ nguyên)
    standings_data = defaultdict(list)
    groups_with_teams = list(tournament.groups.all())
    
    team_stats = {}
    for group in groups_with_teams:
        for team in group.teams.all():
            team_stats[team.id] = {
                'played': 0, 'wins': 0, 'draws': 0, 'losses': 0,
                'gf': 0, 'ga': 0, 'gd': 0, 'points': 0, 'team_obj': team
            }

    finished_group_matches = group_matches.filter(team1_score__isnull=False, team2_score__isnull=False)

    for match in finished_group_matches:
        team1_id, team2_id = match.team1_id, match.team2_id
        score1, score2 = match.team1_score, match.team2_score

        if team1_id in team_stats and team2_id in team_stats:
            team_stats[team1_id]['played'] += 1
            team_stats[team2_id]['played'] += 1
            team_stats[team1_id]['gf'] += score1; team_stats[team1_id]['ga'] += score2
            team_stats[team2_id]['gf'] += score2; team_stats[team2_id]['ga'] += score1

            if score1 > score2:
                team_stats[team1_id]['wins'] += 1; team_stats[team1_id]['points'] += 3
                team_stats[team2_id]['losses'] += 1
            elif score2 > score1:
                team_stats[team2_id]['wins'] += 1; team_stats[team2_id]['points'] += 3
                team_stats[team1_id]['losses'] += 1
            else:
                team_stats[team1_id]['draws'] += 1; team_stats[team1_id]['points'] += 1
                team_stats[team2_id]['draws'] += 1; team_stats[team2_id]['points'] += 1

    for group in groups_with_teams:
        group_standings = [team_stats[team.id] for team in group.teams.all() if team.id in team_stats]
        for stats in group_standings:
            stats['gd'] = stats['gf'] - stats['ga']
        
        group_standings.sort(key=lambda x: (x['points'], x['gd'], x['gf']), reverse=True)
        standings_data[group.id] = group_standings

    # Phần thống kê (giữ nguyên)
    total_teams = tournament.teams.count()
    total_players = Player.objects.filter(team__tournament=tournament).count()
    finished_matches = all_matches.filter(team1_score__isnull=False)
    total_goals = finished_matches.aggregate(total=Sum('team1_score') + Sum('team2_score'))['total'] or 0
    top_scorers = Player.objects.filter(
        goals__match__tournament=tournament
    ).annotate(
        goal_count=Count('goals')
    ).select_related('team').order_by('-goal_count')[:5]

    # Kiểm tra xem có ít nhất một đội đã thanh toán trong giải đấu chưa
    has_paid_teams = tournament.teams.filter(payment_status='PAID').exists()
    
    context = {
        'tournament': tournament,
        'is_organizer': is_organizer,
        'group_matches': group_matches,
        'knockout_matches': all_knockout_matches, # Sử dụng danh sách đã lấy
        'knockout_data': knockout_data, 
        'now': timezone.now(),
        'unassigned_teams': unassigned_teams,
        'total_teams': total_teams,
        'total_players': total_players,
        'total_goals': total_goals,
        'top_scorers': top_scorers,
        'finished_matches_count': finished_matches.count(),
        'standings_data': standings_data,
    }
    return render(request, 'tournaments/tournament_detail.html', context)

@login_required
@never_cache
def team_detail(request, pk):
    team = get_object_or_404(Team, pk=pk)
    
    if request.method == 'POST':
        if request.user == team.captain:
            player_form = PlayerCreationForm(request.POST, request.FILES)
            if player_form.is_valid():
                player = player_form.save(commit=False)
                player.team = team
                try:
                    player.full_clean()
                    player.save()
                    return redirect('team_detail', pk=team.pk)
                except ValidationError as e:
                    player_form.add_error('jersey_number', 'Số áo đã tồn tại trong đội.')
    
    if request.method != 'POST':
        player_form = PlayerCreationForm()
    
    context = {
        'team': team,
        'player_form': player_form,
    }
    return render(request, 'tournaments/team_detail.html', context)

@login_required
@never_cache
def create_team(request, tournament_pk):
    tournament = get_object_or_404(Tournament, pk=tournament_pk)
    if request.method == 'POST':
        form = TeamCreationForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                team = form.save(commit=False)
                team.tournament = tournament
                team.captain = request.user
                team.save()
                return redirect('team_detail', pk=team.pk)
            except IntegrityError:
                form.add_error(None, "Tên đội này đã tồn tại trong giải đấu. Vui lòng chọn một tên khác.")
    else:
        form = TeamCreationForm()
        
    context = {
        'form': form,
        'tournament': tournament
    }
    return render(request, 'tournaments/create_team.html', context)

@login_required
@never_cache
def delete_player(request, pk):
    player = get_object_or_404(Player, pk=pk)
    team = player.team

    if request.user != team.captain:
        return redirect('home')

    if request.method == 'POST':
        player.delete()
        return redirect('team_detail', pk=team.pk)

    context = {
        'player': player,
        'team': team,
    }
    return render(request, 'tournaments/player_confirm_delete.html', context)     

@login_required
@never_cache
def update_player(request, pk):
    player = get_object_or_404(Player, pk=pk)
    team = player.team

    if request.user != team.captain:
        return redirect('home')

    if request.method == 'POST':
        form = PlayerCreationForm(request.POST, request.FILES, instance=player)
        if form.is_valid():
            form.save()
            return redirect('team_detail', pk=team.pk)
    else:
        form = PlayerCreationForm(instance=player)

    context = {
        'form': form,
        'player': player
    }
    return render(request, 'tournaments/update_player.html', context)    

@login_required
@never_cache
def update_team(request, pk):
    team = get_object_or_404(Team, pk=pk)
    
    if request.user != team.captain:
        return redirect('home')

    if request.method == 'POST':
        form = TeamCreationForm(request.POST, request.FILES, instance=team)
        if form.is_valid():
            form.save()
            return redirect('team_detail', pk=team.pk)
    else:
        form = TeamCreationForm(instance=team)
        
    context = {
        'form': form,
        'team': team
    }
    return render(request, 'tournaments/update_team.html', context)    

def match_detail(request, pk):
    match = get_object_or_404(
        Match.objects.select_related('team1', 'team2'),
        pk=pk
    )

    captain_team = None
    if request.user.is_authenticated:
        if match.team1 and getattr(match.team1, "captain_id", None) == request.user.id:
            captain_team = match.team1
        elif match.team2 and getattr(match.team2, "captain_id", None) == request.user.id:
            captain_team = match.team2

    team1_lineup = (
        Lineup.objects
        .filter(match=match, team=match.team1)
        .select_related('player')
        .order_by('player__full_name')
    )
    team2_lineup = (
        Lineup.objects
        .filter(match=match, team=match.team2)
        .select_related('player')
        .order_by('player__full_name')
    )
    cards = match.cards.all().order_by('minute')

    context = {
        "match": match,
        "captain_team": captain_team,
        "team1_lineup": team1_lineup,
        "team2_lineup": team2_lineup,
        'cards': cards,
        "team1_starters": team1_lineup.filter(status="STARTER"),
        "team1_subs":     team1_lineup.filter(status="SUBSTITUTE"),
        "team2_starters": team2_lineup.filter(status="STARTER"),
        "team2_subs":     team2_lineup.filter(status="SUBSTITUTE"),
    }
    return render(request, "tournaments/match_detail.html", context)



@login_required
@never_cache
def manage_lineup(request, match_pk, team_pk):
    match = get_object_or_404(Match.objects.select_related('team1','team2','tournament'), pk=match_pk)
    team = get_object_or_404(Team, pk=team_pk)

    tab = request.GET.get('tab', 'schedule')
    back_url = f"{reverse('match_detail', kwargs={'pk': match.pk})}?tab={tab}#{tab}"

    if request.user != team.captain and not request.user.is_staff:
        return HttpResponseForbidden("Không có quyền.")

    if request.method == "POST":
        selection = {}
        starters = 0
        for player in team.players.all():
            status = request.POST.get(f"player_{player.pk}", "")
            selection[player.pk] = status
            if status == "STARTER":
                starters += 1

        error_message = None
        if starters > MAX_STARTERS:
            error_message = f"Tối đa {MAX_STARTERS} cầu thủ đá chính cho mỗi đội."

        if error_message is None:
            try:
                with transaction.atomic():
                    for player in team.players.all():
                        status = selection.get(player.pk, "")
                        if status:
                            Lineup.objects.update_or_create(
                                match=match, player=player,
                                defaults={"team": team, "status": status}
                            )
                        else:
                            Lineup.objects.filter(match=match, player=player, team=team).delete()
            except ValidationError as e:
                if hasattr(e, 'message_dict'):
                    msgs = []
                    for v in e.message_dict.values():
                        if isinstance(v, (list, tuple)):
                            msgs.extend(str(x) for x in v)
                        else:
                            msgs.append(str(v))
                    error_message = "; ".join(msgs)
                else:
                    error_message = str(e)

        if error_message:
            existing_lineup = selection 
            context = {
                "match": match,
                "team": team,
                "existing_lineup": existing_lineup,
                "back_url": back_url,
                "error_message": error_message,
            }
            return render(request, "tournaments/manage_lineup.html", context)

        tab = request.POST.get('tab') or request.GET.get('tab') or 'schedule'
        url = reverse('match_detail', kwargs={'pk': match.pk})
        return redirect(f'{url}?tab={tab}#{tab}')

    existing_lineup = dict(Lineup.objects.filter(match=match, team=team)
                           .values_list("player_id","status"))
    return render(request, "tournaments/manage_lineup.html", {
        "match": match, "team": team,
        "existing_lineup": existing_lineup,
        "back_url": back_url, "tab": tab,
    })
    

def match_print_view(request, pk):
    match = get_object_or_404(Match, pk=pk)
    team1_lineup = Lineup.objects.filter(match=match, team=match.team1)
    team2_lineup = Lineup.objects.filter(match=match, team=match.team2)

    context = {
        'match': match,
        'team1_lineup': team1_lineup,
        'team2_lineup': team2_lineup,
    }
    return render(request, 'tournaments/match_print.html', context) 

@login_required
@never_cache
def team_payment(request, pk):
    team = get_object_or_404(Team, pk=pk)

    if request.user != team.captain:
        return redirect('home')

    if request.method == 'POST':
        form = PaymentProofForm(request.POST, request.FILES, instance=team)
        if form.is_valid():
            team = form.save(commit=False)
            team.payment_status = 'PENDING'
            team.save()

            send_notification_email(
                subject=f"Xác nhận thanh toán mới từ đội {team.name}",
                template_name='tournaments/emails/new_payment_proof.html',
                context={'team': team},
                recipient_list=[settings.ADMIN_EMAIL]
            )
            
            if team.captain.email:
                send_notification_email(
                    subject=f"Đã nhận được hóa đơn thanh toán của đội {team.name}",
                    template_name='tournaments/emails/payment_pending_confirmation.html',
                    context={'team': team},
                    recipient_list=[team.captain.email]
                )
            
            messages.success(request, 'Đã tải lên hóa đơn thành công! Vui lòng chờ Ban tổ chức xác nhận.')
            
            return redirect('team_detail', pk=team.pk)
    else:
        form = PaymentProofForm(instance=team)

    context = {
        'form': form,
        'team': team
    }
    return render(request, 'tournaments/payment_proof.html', context)


def archive_view(request):
    # Lấy tham số lọc từ URL, tương tự trang giải đấu đang hoạt động
    region_filter = request.GET.get('region', '')
    org_filter = request.GET.get('org', '')

    # Bắt đầu với việc lấy tất cả các giải đã kết thúc
    tournaments_list = Tournament.objects.filter(status='FINISHED').select_related('organization').order_by('-start_date')

    # Áp dụng bộ lọc nếu có
    if region_filter:
        tournaments_list = tournaments_list.filter(region=region_filter)
    
    if org_filter:
        tournaments_list = tournaments_list.filter(organization__id=org_filter)

    # Lấy danh sách các đơn vị tổ chức có giải đấu đã kết thúc để đưa vào bộ lọc
    finished_orgs_ids = Tournament.objects.filter(status='FINISHED').values_list('organization__id', flat=True).distinct()
    all_organizations = Organization.objects.filter(id__in=finished_orgs_ids).order_by('name')

    context = {
        'tournaments': tournaments_list, # Đổi tên biến để nhất quán
        'all_organizations': all_organizations,
        'all_regions': Tournament.Region.choices,
        'current_region': region_filter,
        'current_org': org_filter,
    }
    return render(request, 'tournaments/archive.html', context)

@login_required
@never_cache
def announcement_dashboard(request):
    tournament_ids_as_captain = set(
        Team.objects.filter(captain=request.user).values_list('tournament_id', flat=True)
    )
    
    tournament_ids_as_player = set(
        Player.objects.filter(user=request.user).values_list('team__tournament_id', flat=True)
    )
    
    all_relevant_ids = tournament_ids_as_captain.union(tournament_ids_as_player)

    if not all_relevant_ids:
        announcements = Announcement.objects.none()
    else:
        public_announcements = Q(audience='PUBLIC', tournament_id__in=all_relevant_ids)

        captain_only_announcements = Q()
        if tournament_ids_as_captain:
            captain_only_announcements = Q(audience='CAPTAINS_ONLY', tournament_id__in=tournament_ids_as_captain)
        
        announcements = Announcement.objects.filter(
            public_announcements | captain_only_announcements,
            is_published=True
        ).select_related('tournament').distinct().order_by('-created_at')

    unread_announcements = announcements.exclude(read_by=request.user)
    request.user.read_announcements.add(*unread_announcements) 

    context = {
        'announcements': announcements
    }
    return render(request, 'tournaments/announcement_dashboard.html', context)

def faq_view(request):
    return render(request, 'tournaments/faq.html')        

# === THAY THẾ HÀM NÀY ===
@login_required
@never_cache
def draw_groups_view(request, tournament_pk):
    tournament = get_object_or_404(Tournament, pk=tournament_pk)

    is_organizer = tournament.organization and tournament.organization.members.filter(pk=request.user.pk).exists()
    if not request.user.is_staff and not is_organizer:
        return HttpResponseForbidden("Bạn không có quyền truy cập trang này.")

    # Kiểm tra xem giải đấu còn đang mở đăng ký không
    if tournament.status == 'REGISTRATION_OPEN':
        # Gửi một thông báo lỗi cho người dùng
        messages.error(request, "Không thể bốc thăm khi giải đấu vẫn đang trong giai đoạn đăng ký.")
        # Chuyển hướng họ về trang chi tiết giải đấu
        return redirect('tournament_detail', pk=tournament.pk)

    if request.method == 'POST':
        try:
            results_str = request.POST.get('draw_results')
            if not results_str:
                raise ValueError("Không nhận được dữ liệu bốc thăm.")

            group_assignments = json.loads(results_str) 

            with transaction.atomic():
                # --- BẮT ĐẦU SỬA LỖI ---
                # 1. Xóa tất cả các trận đấu vòng bảng cũ của giải này
                Match.objects.filter(tournament=tournament, match_round='GROUP').delete()
                
                # 2. Đưa tất cả các đội về trạng thái "chưa có bảng"
                tournament.teams.update(group=None)
                # --- KẾT THÚC SỬA LỖI ---

                # 3. Tiến hành xếp các đội vào bảng mới
                for group_id_str, team_ids in group_assignments.items():
                    group_id = int(group_id_str)
                    group = get_object_or_404(Group, pk=group_id, tournament=tournament)
                    
                    # Cập nhật lại các đội trong bảng
                    teams_to_assign = Team.objects.filter(pk__in=team_ids, tournament=tournament)
                    for team in teams_to_assign:
                        team.group = group
                        team.save()
            
            messages.success(request, "Kết quả bốc thăm mới đã được lưu thành công! Lịch thi đấu vòng bảng cũ đã được xóa.")
            return redirect('tournament_detail', pk=tournament.pk)

        except Exception as e:
            messages.error(request, f"Đã có lỗi xảy ra: {e}")
            # Sửa lại redirect khi có lỗi
            return redirect('draw_groups', tournament_pk=tournament.pk)

    unassigned_teams = tournament.teams.filter(payment_status='PAID', group__isnull=True)
    groups = tournament.groups.all().order_by('name')

    teams_data = [{
        'id': team.id, 
        'name': team.name, 
        'logo': team.logo.url if team.logo else ''
    } for team in unassigned_teams]

    groups_data = [{
        'id': group.id, 
        'name': group.name
    } for group in groups]

    context = {
        'tournament': tournament,
        'teams_json': json.dumps(teams_data),
        'groups_json': json.dumps(groups_data),
    }
    return render(request, 'tournaments/draw_groups.html', context)

@login_required # Giữ lại
@never_cache
# Bỏ decorator @staff_member_required
def generate_schedule_view(request, tournament_pk):
    tournament = get_object_or_404(Tournament, pk=tournament_pk)
    
    # --- THÊM ĐOẠN KIỂM TRA QUYỀN MỚI ---
    is_organizer = tournament.organization and tournament.organization.members.filter(pk=request.user.pk).exists()
    if not request.user.is_staff and not is_organizer:
        return HttpResponseForbidden("Bạn không có quyền truy cập trang này.")

    # === BẮT ĐẦU THÊM ĐOẠN KIỂM TRA MỚI ===
    has_groups = tournament.groups.exists()
    has_unassigned_teams = tournament.teams.filter(payment_status='PAID', group__isnull=True).exists()
    has_paid_teams = tournament.teams.filter(payment_status='PAID').exists()

    # Nếu chưa đủ điều kiện, báo lỗi và trả về trang chi tiết
    if not has_groups or not has_paid_teams or has_unassigned_teams:
        messages.error(request, "Không thể xếp lịch. Cần tạo bảng, có đội đã đăng ký và tất cả các đội phải được bốc thăm vào bảng.")
        return redirect('tournament_detail', pk=tournament.pk)

    # Nếu đã có lịch rồi thì cũng không cho tạo lại
    if tournament.matches.exists():
        messages.warning(request, "Lịch thi đấu đã được tạo cho giải này.")
        return redirect('tournament_detail', pk=tournament.pk)

    if request.method == 'POST' and 'confirm_schedule' in request.POST:
        schedule_preview_json = request.session.get('schedule_preview_json')
        if not schedule_preview_json:
            messages.error(request, "Không tìm thấy lịch thi đấu xem trước. Vui lòng tạo lại.")
            return redirect('generate_schedule', tournament_pk=tournament.pk)
        
        try:
            with transaction.atomic():
                Match.objects.filter(tournament=tournament).delete()
                schedule_to_save = json.loads(schedule_preview_json)
                for match_data in schedule_to_save:
                    Match.objects.create(
                        tournament=tournament,
                        team1=Team.objects.get(pk=match_data['team1_id']),
                        team2=Team.objects.get(pk=match_data['team2_id']),
                        match_time=datetime.fromisoformat(match_data['match_time']),
                        location=match_data['location'],
                        match_round='GROUP'
                    )
            del request.session['schedule_preview_json']
            messages.success(request, "Lịch thi đấu đã được tạo thành công!")
            return redirect('tournament_detail', pk=tournament.pk)
        except Exception as e:
            messages.error(request, f"Lỗi khi lưu lịch thi đấu: {e}")

    schedule_by_group = None
    unscheduled_matches = None
    if request.method == 'POST':
        form = ScheduleGenerationForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            
            start_date = data['start_date']
            time_slots_str = [t.strip() for t in data['time_slots'].split(',')]
            locations = [loc.strip() for loc in data['locations'].split(',')]
            rest_days = timedelta(days=data['rest_days'])
            
            all_pairings = []
            groups = tournament.groups.prefetch_related('teams').all()
            for group in groups:
                teams_in_group = list(group.teams.all())
                group_pairings = list(combinations(teams_in_group, 2))
                for pair in group_pairings:
                    all_pairings.append({'pair': pair, 'group_name': group.name})

            random.shuffle(all_pairings)
            
            scheduled_matches = []
            team_last_played = {}
            current_date = start_date
            day_offset = 0
            
            while all_pairings:
                for time_str in time_slots_str:
                    for location in locations:
                        if not all_pairings: break
                        
                        current_datetime = datetime.combine(current_date, time.fromisoformat(time_str))
                        best_match_index = -1
                        for i, pairing_info in enumerate(all_pairings):
                            team1, team2 = pairing_info['pair']
                            last_played1 = team_last_played.get(team1.id, None)
                            last_played2 = team_last_played.get(team2.id, None)
                            can_play1 = not last_played1 or (current_date - last_played1.date()) > rest_days
                            can_play2 = not last_played2 or (current_date - last_played2.date()) > rest_days
                            if can_play1 and can_play2:
                                best_match_index = i
                                break
                        
                        if best_match_index != -1:
                            pairing_info = all_pairings.pop(best_match_index)
                            team1, team2 = pairing_info['pair']
                            scheduled_matches.append({
                                'team1_name': team1.name, 'team1_id': team1.id,
                                'team2_name': team2.name, 'team2_id': team2.id,
                                'match_time': current_datetime,
                                'location': location,
                                'group_name': pairing_info['group_name']
                            })
                            team_last_played[team1.id] = current_datetime
                            team_last_played[team2.id] = current_datetime

                day_offset += 1
                current_date = start_date + timedelta(days=day_offset)
                if day_offset > 100:
                    unscheduled_matches = [p['pair'] for p in all_pairings]
                    all_pairings = []

            schedule_by_group = {}
            scheduled_matches.sort(key=lambda x: x['match_time'])
            for match in scheduled_matches:
                group_name = match['group_name']
                if group_name not in schedule_by_group:
                    schedule_by_group[group_name] = []
                schedule_by_group[group_name].append(match)

            schedule_by_group = dict(sorted(schedule_by_group.items()))

            schedule_for_session = [
                {**match, 'match_time': match['match_time'].isoformat()}
                for match in scheduled_matches
            ]
            request.session['schedule_preview_json'] = json.dumps(schedule_for_session)
    else:
        form = ScheduleGenerationForm()

    context = {
        'tournament': tournament,
        'form': form,
        'schedule_by_group': schedule_by_group,
        'unscheduled_matches': unscheduled_matches,
    }
    return render(request, 'tournaments/generate_schedule.html', context)
# === KẾT THÚC SỬA LỖI ===

def player_detail(request, pk):
    player = get_object_or_404(Player.objects.select_related('team__tournament'), pk=pk)
    tournament = player.team.tournament

    total_goals = Goal.objects.filter(player=player).count()
    cards = Card.objects.filter(player=player).aggregate(
        yellow_cards=Count('id', filter=Q(card_type='YELLOW')),
        red_cards=Count('id', filter=Q(card_type='RED'))
    )
    matches_played = Match.objects.filter(lineups__player=player).distinct()

    stats = {
        'total_goals': total_goals,
        'yellow_cards': cards.get('yellow_cards', 0),
        'red_cards': cards.get('red_cards', 0),
        'matches_played': matches_played.select_related('team1', 'team2').order_by('-match_time'),
        'matches_played_count': matches_played.count(),
    }

    badges = []
    top_scorer = Player.objects.filter(team__tournament=tournament).annotate(goal_count=Count('goals')).order_by('-goal_count').first()
    if top_scorer and top_scorer.pk == player.pk and stats['total_goals'] > 0:
        badges.append({'name': 'Vua phá lưới', 'icon': 'bi-trophy-fill', 'color': 'text-warning'})

    if stats['yellow_cards'] == 0 and stats['red_cards'] == 0 and stats['matches_played_count'] > 0:
        badges.append({'name': 'Cầu thủ Fair-play', 'icon': 'bi-shield-check', 'color': 'text-primary'})

    most_played = Player.objects.filter(team__tournament=tournament).annotate(match_count=Count('lineups')).order_by('-match_count').first()
    if most_played and most_played.pk == player.pk and stats['matches_played_count'] > 0:
        badges.append({'name': 'Cột trụ đội bóng', 'icon': 'bi-gem', 'color': 'text-info'})

    context = {
        'player': player,
        'stats': stats,
        'badges': badges,
    }
    return render(request, 'tournaments/player_detail.html', context)


@login_required
def claim_player_profile(request, pk):
    player_to_claim = get_object_or_404(Player, pk=pk)

    if hasattr(request.user, 'player_profile') and request.user.player_profile is not None:
        messages.error(request, "Tài khoản của bạn đã được liên kết với một hồ sơ cầu thủ khác.")
        return redirect('player_detail', pk=pk)

    if player_to_claim.user is not None:
        messages.error(request, "Hồ sơ này đã được một tài khoản khác liên kết.")
        return redirect('player_detail', pk=pk)

    player_to_claim.user = request.user
    player_to_claim.save()
    messages.success(request, f"Bạn đã liên kết thành công với hồ sơ cầu thủ {player_to_claim.full_name}.")
    return redirect('player_detail', pk=pk)

@login_required
def tournament_bulk_upload(request, tournament_pk):
    tournament = get_object_or_404(Tournament, pk=tournament_pk)
    
    # Kiểm tra quyền truy cập
    is_organizer = False
    if request.user.is_authenticated and tournament.organization:
        if tournament.organization.members.filter(pk=request.user.pk).exists():
            is_organizer = True
    if not request.user.is_superuser and not is_organizer:
        return HttpResponseForbidden("Bạn không có quyền thực hiện hành động này.")

    if request.method == 'POST':
        # Form xử lý URL vẫn hoạt động bình thường
        url_form = GalleryURLForm(request.POST, instance=tournament)
        if url_form.is_valid():
            url_form.save()
            messages.success(request, "Đã cập nhật thành công link album ảnh.")

        # Xử lý file ảnh trực tiếp từ request, không cần form
        if 'images' in request.FILES:
            images = request.FILES.getlist('images')
            uploaded_count = 0
            for image_file in images:
                # Kiểm tra cơ bản để chắc chắn đó là file ảnh
                if image_file.content_type.startswith('image'):
                    TournamentPhoto.objects.create(tournament=tournament, image=image_file)
                    uploaded_count += 1
                else:
                    messages.warning(request, f"File '{image_file.name}' không phải là ảnh và đã bị bỏ qua.")
            
            if uploaded_count > 0:
                 messages.success(request, f"Đã tải lên thành công {uploaded_count} ảnh.")
        
        # Nếu không có file và không có URL mới, thông báo không có gì thay đổi
        if 'images' not in request.FILES and not url_form.has_changed():
             messages.info(request, "Không có thay đổi nào được thực hiện.")

        return redirect(reverse('tournament_detail', args=[tournament_pk]) + '?tab=gallery')

    else: # GET request
        # Khi trang được tải, chỉ cần tạo form cho URL
        url_form = GalleryURLForm(instance=tournament)

    context = {
        'tournament': tournament,
        'url_form': url_form,
    }
    return render(request, 'tournaments/bulk_upload.html', context)