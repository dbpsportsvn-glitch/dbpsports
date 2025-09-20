# tournaments/views.py

from django.shortcuts import render, get_object_or_404, redirect
# --- THÊM CÁC DÒNG NÀY VÀO ---
from collections import defaultdict
from django.db.models import Prefetch
# --- KẾT THÚC ---
from .models import Tournament, Team, Player, Match, Lineup, MAX_STARTERS, Group, Announcement, Goal, Card
from django.contrib.auth.decorators import login_required # Để yêu cầu đăng nhập
from django.views.decorators.cache import never_cache # Thêm dòng này
#from .forms import TeamCreationForm, PlayerCreationForm 
from django.http import HttpResponseForbidden
from django.db import transaction
from django.core.exceptions import ValidationError
from django.urls import reverse
from django.db.models import Sum, Count
from .forms import TeamCreationForm, PlayerCreationForm, PaymentProofForm, CommentForm, ScheduleGenerationForm
from .utils import send_notification_email
from django.conf import settings
from django.utils import timezone
from django.db.models import Q
from .models import HomeBanner
from datetime import timedelta
from django.contrib import messages
import json
from django.http import JsonResponse
from django.contrib.admin.views.decorators import staff_member_required
from itertools import combinations
import random
from datetime import datetime, time, timedelta


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
    today = timezone.localdate()
    qs = Tournament.objects.filter(
        Q(start_date__lte=today, end_date__gte=today) |
        Q(status__in=["REGISTRATION_OPEN","ONGOING","IN_PROGRESS"])
    ).order_by("-start_date")
    return render(request, "tournaments/active_list.html", {"tournaments": qs})

from datetime import timedelta
from django.utils import timezone

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

# --- THAY THẾ TOÀN BỘ HÀM tournament_detail BẰNG PHIÊN BẢN MỚI NÀY ---
@never_cache # THÊM DÒNG NÀY VÀO
def tournament_detail(request, pk):
    tournament = get_object_or_404(
        Tournament.objects.prefetch_related(
            Prefetch('groups', queryset=Group.objects.order_by('name').prefetch_related(
                Prefetch('teams', queryset=Team.objects.select_related('captain'))
            ))
        ),
        pk=pk
    )

    all_matches = tournament.matches.select_related('team1', 'team2').order_by('match_time')
    group_matches = all_matches.filter(match_round='GROUP')
    knockout_matches = all_matches.filter(match_round__in=['SEMI', 'FINAL'])
    unassigned_teams = tournament.teams.filter(payment_status='PAID', group__isnull=True)

    # === TÍNH TOÁN BẢNG XẾP HẠNG ĐÃ ĐƯỢC TỐI ƯU ===
    standings_data = defaultdict(list)
    # Lấy tất cả các nhóm và đội của chúng từ tournament đã prefetch
    groups_with_teams = list(tournament.groups.all())
    
    team_stats = {}
    for group in groups_with_teams:
        for team in group.teams.all():
            team_stats[team.id] = {
                'played': 0, 'wins': 0, 'draws': 0, 'losses': 0,
                'gf': 0, 'ga': 0, 'gd': 0, 'points': 0, 'team_obj': team
            }

    # Chỉ 1 câu lệnh để lấy tất cả các trận vòng bảng đã kết thúc của giải đấu
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

    # === CÁC THỐNG KÊ KHÁC VẪN GIỮ NGUYÊN ===
    total_teams = tournament.teams.count()
    total_players = Player.objects.filter(team__tournament=tournament).count()
    finished_matches = all_matches.filter(team1_score__isnull=False)
    total_goals = finished_matches.aggregate(total=Sum('team1_score') + Sum('team2_score'))['total'] or 0
    top_scorers = Player.objects.filter(
        goals__match__tournament=tournament
    ).annotate(
        goal_count=Count('goals')
    ).select_related('team').order_by('-goal_count')[:5]

    context = {
        'tournament': tournament,
        'group_matches': group_matches,
        'knockout_matches': knockout_matches,
        'now': timezone.now(),
        'unassigned_teams': unassigned_teams,
        'total_teams': total_teams,
        'total_players': total_players,
        'total_goals': total_goals,
        'top_scorers': top_scorers,
        'finished_matches_count': finished_matches.count(),
        'standings_data': standings_data, # Gửi dữ liệu BXH đã xử lý ra template
    }
    return render(request, 'tournaments/tournament_detail.html', context)

@login_required
@never_cache
def team_detail(request, pk):
    team = get_object_or_404(Team, pk=pk)
    
    # Xử lý form thêm cầu thủ
    if request.method == 'POST':
        # Chỉ đội trưởng mới có quyền thêm cầu thủ
        if request.user == team.captain:
            player_form = PlayerCreationForm(request.POST, request.FILES) # Sửa lại đây
            if player_form.is_valid():
                player = player_form.save(commit=False)
                player.team = team  # Gán cầu thủ vào đội này
                try:
                    player.full_clean()
                    player.save()
                    return redirect('team_detail', pk=team.pk)  # Tải lại trang để xem cầu thủ mới
                except ValidationError as e:
                    player_form.add_error('jersey_number', 'Số áo đã tồn tại trong đội.')
    
    # Tạo form trống cho GET. Nếu POST lỗi, giữ nguyên form có lỗi.
    if request.method != 'POST':
        player_form = PlayerCreationForm()
    
    context = {
        'team': team,
        'player_form': player_form, # Gửi form vào template
    }
    return render(request, 'tournaments/team_detail.html', context)

@login_required
@never_cache
def create_team(request, tournament_pk):
    tournament = get_object_or_404(Tournament, pk=tournament_pk)
    if request.method == 'POST':
        form = TeamCreationForm(request.POST, request.FILES)
        if form.is_valid():
            try: # --- BẮT ĐẦU SỬA LỖI ---
                team = form.save(commit=False)
                team.tournament = tournament
                team.captain = request.user
                team.save()
                return redirect('team_detail', pk=team.pk)
            except IntegrityError:
                form.add_error(None, "Tên đội này đã tồn tại trong giải đấu. Vui lòng chọn một tên khác.")
            # --- KẾT THÚC SỬA LỖI ---
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

    # Chỉ đội trưởng của đội mới có quyền xóa cầu thủ
    if request.user != team.captain:
        # (Trong tương lai, chúng ta sẽ hiển thị trang báo lỗi thay vì redirect)
        return redirect('home')

    if request.method == 'POST':
        player.delete()
        return redirect('team_detail', pk=team.pk) # Chuyển về trang chi tiết đội

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

    # Chỉ đội trưởng của đội mới có quyền sửa
    if request.user != team.captain:
        return redirect('home')

    if request.method == 'POST':
        form = PlayerCreationForm(request.POST, request.FILES, instance=player) # Thêm request.FILES
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
    
    # Chỉ đội-trưởng mới có quyền sửa
    if request.user != team.captain:
        return redirect('home')

    if request.method == 'POST':
        # Thêm request.FILES vào đây
        form = TeamCreationForm(request.POST, request.FILES, instance=team)
        if form.is_valid():
            form.save()
            return redirect('team_detail', pk=team.pk)
    else:
        # Hiển-thị form với thông-tin có sẵn của đội
        form = TeamCreationForm(instance=team)
        
    context = {
        'form': form,
        'team': team
    }
    return render(request, 'tournaments/update_team.html', context)    


# tournaments/views.py
from django.shortcuts import get_object_or_404, render
from .models import Match, Lineup

def match_detail(request, pk):
    match = get_object_or_404(
        Match.objects.select_related('team1', 'team2'),
        pk=pk
    )

    # đội mà user là đội trưởng (để hiện nút)
    captain_team = None
    if request.user.is_authenticated:
        if match.team1 and getattr(match.team1, "captain_id", None) == request.user.id:
            captain_team = match.team1
        elif match.team2 and getattr(match.team2, "captain_id", None) == request.user.id:
            captain_team = match.team2

    # lineup theo đội
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
    # Lấy thông tin thẻ phạt
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

    # Chỉ đội trưởng của team này hoặc staff được sửa
    if request.user != team.captain and not request.user.is_staff:
        return HttpResponseForbidden("Không có quyền.")

    if request.method == "POST":
        # Build selection from POST
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
            existing_lineup = selection  # keep user's choices
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

    # Chỉ đội trưởng mới có quyền
    if request.user != team.captain:
        return redirect('home')

    if request.method == 'POST':
        form = PaymentProofForm(request.POST, request.FILES, instance=team)
        if form.is_valid():
            team = form.save(commit=False)
            team.payment_status = 'PENDING' # Chuyển trạng thái sang "Chờ xác nhận"
            team.save()

            # === GỌI HÀM GỬI EMAIL TẠI ĐÂY ===
            send_notification_email(
                subject=f"Xác nhận thanh toán mới từ đội {team.name}",
                template_name='tournaments/emails/new_payment_proof.html',
                context={'team': team},
                recipient_list=[settings.ADMIN_EMAIL] # <-- Gửi trong một danh sách
            )
            
            return redirect('team_detail', pk=team.pk)
    else:
        form = PaymentProofForm(instance=team)

    context = {
        'form': form,
        'team': team
    }
    return render(request, 'tournaments/payment_proof.html', context)


    # tournaments/views.py
def archive_view(request):
    # Lấy tất cả các giải đấu đã kết thúc
    finished_tournaments = Tournament.objects.filter(status='FINISHED').order_by('-start_date')

    context = {
        'tournaments_list': finished_tournaments
    }
    return render(request, 'tournaments/archive.html', context)

# >> THÊM HÀM MỚI NÀY VÀO CUỐI FILE views.py <<
@login_required
@never_cache # Không cache trang này để đội trưởng luôn thấy thông báo mới nhất
def announcement_dashboard(request):
    # Lấy danh sách ID các giải đấu mà người dùng đang làm đội trưởng
    managed_tournaments_ids = Team.objects.filter(captain=request.user).values_list('tournament_id', flat=True).distinct()
    
    # Lấy tất cả thông báo thuộc các giải đấu đó và đã được công khai
    announcements = Announcement.objects.filter(
        tournament_id__in=managed_tournaments_ids,
        is_published=True
    ).select_related('tournament') # Dùng select_related để tối ưu truy vấn
    
    context = {
        'announcements': announcements
    }
    return render(request, 'tournaments/announcement_dashboard.html', context)

# >> FAG <<
def faq_view(request):
    return render(request, 'tournaments/faq.html')        


@staff_member_required # Chỉ admin hoặc staff mới được truy cập
@login_required
@never_cache
def draw_groups_view(request, tournament_pk):
    tournament = get_object_or_404(Tournament, pk=tournament_pk)

    # Xử lý khi admin nhấn nút "Lưu kết quả"
    if request.method == 'POST':
        try:
            results_str = request.POST.get('draw_results')
            if not results_str:
                raise ValueError("Không nhận được dữ liệu bốc thăm.")

            # Chuyển đổi chuỗi JSON từ frontend thành dictionary của Python
            group_assignments = json.loads(results_str) 

            with transaction.atomic(): # Đảm bảo tất cả các cập nhật đều thành công
                for group_id_str, team_ids in group_assignments.items():
                    group_id = int(group_id_str)
                    group = get_object_or_404(Group, pk=group_id, tournament=tournament)
                    
                    for team_id in team_ids:
                        team = get_object_or_404(Team, pk=team_id, tournament=tournament)
                        team.group = group # Gán đội vào bảng đấu
                        team.save()
            
            messages.success(request, "Kết quả bốc thăm đã được lưu thành công!")
            return redirect('tournament_detail', pk=tournament.pk)

        except Exception as e:
            messages.error(request, f"Đã có lỗi xảy ra: {e}")
            # Quay lại trang bốc thăm nếu có lỗi
            return redirect('draw_groups', tournament_pk=tournament.pk)


    # Lấy dữ liệu cho lần đầu tải trang (GET request)
    unassigned_teams = tournament.teams.filter(payment_status='PAID', group__isnull=True)
    groups = tournament.groups.all().order_by('name')

    # Chuyển đổi dữ liệu sang định dạng mà JavaScript có thể đọc được
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
        'teams_json': json.dumps(teams_data), # Chuyển thành chuỗi JSON
        'groups_json': json.dumps(groups_data), # Chuyển thành chuỗi JSON
    }
    return render(request, 'tournaments/draw_groups.html', context)


# >> THÊM VÀO CUỐI FILE views.py <<
from django.db.models import Count, Q
def player_detail(request, pk):
    player = get_object_or_404(Player.objects.select_related('team__tournament'), pk=pk)
    tournament = player.team.tournament

    # --- Tính toán thống kê ---
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

    # --- BẮT ĐẦU: Xác định các huy hiệu đạt được ---
    badges = []

    # 1. Huy hiệu "Vua phá lưới"
    top_scorer = Player.objects.filter(team__tournament=tournament).annotate(goal_count=Count('goals')).order_by('-goal_count').first()
    if top_scorer and top_scorer.pk == player.pk and stats['total_goals'] > 0:
        badges.append({'name': 'Vua phá lưới', 'icon': 'bi-trophy-fill', 'color': 'text-warning'})

    # 2. Huy hiệu "Fair-play"
    if stats['yellow_cards'] == 0 and stats['red_cards'] == 0 and stats['matches_played_count'] > 0:
        badges.append({'name': 'Cầu thủ Fair-play', 'icon': 'bi-shield-check', 'color': 'text-primary'})

    # 3. Huy hiệu "Cột trụ đội bóng"
    most_played = Player.objects.filter(team__tournament=tournament).annotate(match_count=Count('lineups')).order_by('-match_count').first()
    if most_played and most_played.pk == player.pk and stats['matches_played_count'] > 0:
        badges.append({'name': 'Cột trụ đội bóng', 'icon': 'bi-gem', 'color': 'text-info'})

    # --- KẾT THÚC: Xác định huy hiệu ---

    context = {
        'player': player,
        'stats': stats,
        'badges': badges, # Gửi danh sách huy hiệu ra template
    }
    return render(request, 'tournaments/player_detail.html', context)


# Tính năng xếp lịch thi đấu
@staff_member_required
@login_required
@never_cache
def generate_schedule_view(request, tournament_pk):
    tournament = get_object_or_404(Tournament, pk=tournament_pk)
    
    # Logic lưu lịch (POST confirm_schedule) giữ nguyên
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

    # Xử lý khi nhấn nút "Tạo lịch (Xem trước)"
    schedule_by_group = None # Sẽ có dạng: {'Bảng A': [trận...], 'Bảng B': [trận...]}
    unscheduled_matches = None
    if request.method == 'POST':
        form = ScheduleGenerationForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            
            start_date = data['start_date']
            time_slots_str = [t.strip() for t in data['time_slots'].split(',')]
            locations = [loc.strip() for loc in data['locations'].split(',')]
            rest_days = timedelta(days=data['rest_days'])
            
            # Sửa đổi ở đây: Tạo cặp đấu theo từng bảng
            all_pairings = []
            groups = tournament.groups.prefetch_related('teams').all()
            for group in groups:
                teams_in_group = list(group.teams.all())
                # Thêm thông tin group vào mỗi cặp đấu
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
                                'group_name': pairing_info['group_name'] # Lưu lại tên bảng
                            })
                            team_last_played[team1.id] = current_datetime
                            team_last_played[team2.id] = current_datetime

                day_offset += 1
                current_date = start_date + timedelta(days=day_offset)
                if day_offset > 100:
                    unscheduled_matches = [p['pair'] for p in all_pairings]
                    all_pairings = []

            # Sắp xếp và nhóm kết quả theo bảng đấu
            schedule_by_group = {}
            # Sắp xếp các trận theo ngày giờ trước
            scheduled_matches.sort(key=lambda x: x['match_time'])
            for match in scheduled_matches:
                group_name = match['group_name']
                if group_name not in schedule_by_group:
                    schedule_by_group[group_name] = []
                schedule_by_group[group_name].append(match)

            # Lưu bản danh sách phẳng vào session để dễ xử lý khi lưu
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
        'schedule_by_group': schedule_by_group, # Gửi dữ liệu đã nhóm ra template
        'unscheduled_matches': unscheduled_matches,
    }
    return render(request, 'tournaments/generate_schedule.html', context)

@login_required
def claim_player_profile(request, pk):
    player_to_claim = get_object_or_404(Player, pk=pk)

    # Kiểm tra xem người dùng đã có hồ sơ nào chưa
    if hasattr(request.user, 'player_profile') and request.user.player_profile is not None:
        messages.error(request, "Tài khoản của bạn đã được liên kết với một hồ sơ cầu thủ khác.")
        return redirect('player_detail', pk=pk)

    # Kiểm tra xem hồ sơ này đã có ai nhận chưa
    if player_to_claim.user is not None:
        messages.error(request, "Hồ sơ này đã được một tài khoản khác liên kết.")
        return redirect('player_detail', pk=pk)

    # Nếu mọi thứ hợp lệ, tiến hành liên kết
    player_to_claim.user = request.user
    player_to_claim.save()
    messages.success(request, f"Bạn đã liên kết thành công với hồ sơ cầu thủ {player_to_claim.full_name}.")
    return redirect('player_detail', pk=pk)    