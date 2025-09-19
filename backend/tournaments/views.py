# tournaments/views.py

from django.shortcuts import render, get_object_or_404, redirect
# --- THÊM CÁC DÒNG NÀY VÀO ---
from collections import defaultdict
from django.db.models import Prefetch
# --- KẾT THÚC ---
from .models import Tournament, Team, Player, Match, Lineup, MAX_STARTERS
from django.contrib.auth.decorators import login_required # Để yêu cầu đăng nhập
from .forms import TeamCreationForm, PlayerCreationForm 
from django.http import HttpResponseForbidden
from django.db import transaction
from django.core.exceptions import ValidationError
from django.urls import reverse
from django.db.models import Sum, Count
from .forms import TeamCreationForm, PlayerCreationForm, PaymentProofForm, CommentForm
from .utils import send_notification_email
from django.conf import settings
from django.utils import timezone
from django.db.models import Q
from .models import HomeBanner
from datetime import timedelta


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
def create_team(request, tournament_pk):
    tournament = get_object_or_404(Tournament, pk=tournament_pk)
    if request.method == 'POST':
        # Thêm request.FILES vào đây để xử lý file tải lên
        form = TeamCreationForm(request.POST, request.FILES)
        if form.is_valid():
            team = form.save(commit=False)
            team.tournament = tournament
            team.captain = request.user
            team.save()
            return redirect('team_detail', pk=team.pk)
    else:
        form = TeamCreationForm()
        
    context = {
        'form': form,
        'tournament': tournament
    }
    return render(request, 'tournaments/create_team.html', context)

@login_required
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