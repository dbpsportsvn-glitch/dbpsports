# Python Standard Library
import json
import random
from collections import defaultdict
from datetime import datetime, time, timedelta
from itertools import combinations
from django.core import serializers
from django.db import transaction
from datetime import date
from organizations.models import JobPosting, JobApplication
from organizations.forms import JobApplicationForm
from django.db.models import Q

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
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from services.weather import get_weather_for_match
from organizations.forms import GoalForm, CardForm, SubstitutionForm, MatchMediaUpdateForm 
from .utils import get_current_vote_value
from .models import TournamentStaff
from organizations.views import user_can_control_match, user_can_upload_gallery
from organizations.forms import MatchUpdateForm
# Thêm import Note BLV
from .models import MatchNote
from .forms import CommentatorNoteForm
from .forms import CaptainNoteForm

# Local Application Imports
from organizations.models import Organization

from .forms import (CommentForm, GalleryURLForm, PaymentProofForm,
                    PlayerCreationForm, ScheduleGenerationForm,
                    TeamCreationForm)
from .models import (Announcement, Card, Goal, Group, HomeBanner, Lineup, Match,
                     Player, Team, Tournament, TournamentPhoto, MAX_STARTERS, Notification, Substitution, MatchEvent, TeamAchievement, VoteRecord)
from .utils import send_notification_email, send_schedule_notification
from django.db.models import Sum, F
from django.contrib.auth.models import User

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

@never_cache
def tournaments_active(request):
    # Lấy tham số lọc từ URL (ví dụ: ?region=MIEN_BAC)
    region_filter = request.GET.get('region', '')
    org_filter = request.GET.get('org', '')

    # Bắt đầu với việc lấy tất cả các giải đang hoạt động
    tournaments_list = Tournament.objects.exclude(status='FINISHED').select_related('organization').order_by('-start_date')

    # --- BẮT ĐẦU THÊM MỚI ---
    followed_tournament_ids = []
    if request.user.is_authenticated:
        followed_tournament_ids = request.user.followed_tournaments.values_list('id', flat=True)
    # --- KẾT THÚC THÊM MỚI ---

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
        'all_organizations': all_organizations,
        'all_regions': Tournament.Region.choices,
        'current_region': region_filter,
        'current_org': org_filter,
        'followed_tournament_ids': followed_tournament_ids, # Gửi danh sách ID ra template
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

    # === BẮT ĐẦU THÊM MỚI TẠI ĐÂY ===
    # Lấy danh sách các trận đấu có thư viện ảnh riêng
    matches_with_galleries = all_matches.filter(
        Q(cover_photo__isnull=False) | Q(gallery_url__isnull=False)
    ).distinct()
        
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

    # Các truy vấn cơ bản
    all_teams_in_tournament = tournament.teams.all()
    total_teams = all_teams_in_tournament.count()
    total_players = Player.objects.filter(team__tournament=tournament).count()
    finished_matches = all_matches.filter(team1_score__isnull=False)
    finished_matches_count = finished_matches.count()
    
    # Thống kê bàn thắng & thẻ phạt tổng quát
    total_goals_obj = Goal.objects.filter(match__in=finished_matches)
    total_own_goals = total_goals_obj.filter(is_own_goal=True).count()
    total_normal_goals = total_goals_obj.filter(is_own_goal=False).count()
    
    total_cards_obj = Card.objects.filter(match__in=finished_matches)
    total_yellow_cards = total_cards_obj.filter(card_type='YELLOW').count()
    total_red_cards = total_cards_obj.filter(card_type='RED').count()
    
    avg_goals_per_match = round(total_normal_goals / finished_matches_count, 2) if finished_matches_count > 0 else 0

    # Thống kê cầu thủ
    top_scorers = Player.objects.filter(
        goals__match__tournament=tournament,
        goals__is_own_goal=False  # Chỉ tính bàn thắng, không tính phản lưới
    ).annotate(
        goal_count=Count('goals')
    ).select_related('team').order_by('-goal_count')[:5]

    hattricks = Player.objects.filter(
        goals__match__tournament=tournament,
        goals__is_own_goal=False
    ).values('full_name', 'team__name', 'goals__match_id').annotate(
        goals_in_match=Count('id')
    ).filter(goals_in_match__gte=3).count()

    # Thống kê theo từng đội
    team_goal_stats = []
    team_card_stats = []
    for team in all_teams_in_tournament:
        goals_for = Goal.objects.filter(team=team, is_own_goal=False).count()
        goals_against_matches_as_team1 = Goal.objects.filter(match__team1=team, is_own_goal=False).exclude(team=team)
        goals_against_matches_as_team2 = Goal.objects.filter(match__team2=team, is_own_goal=False).exclude(team=team)
        goals_against = goals_against_matches_as_team1.count() + goals_against_matches_as_team2.count()
        team_goal_stats.append({
            'team_obj': team,
            'gf': goals_for,
            'ga': goals_against,
            'gd': goals_for - goals_against
        })

        yellow_cards = Card.objects.filter(team=team, card_type='YELLOW').count()
        red_cards = Card.objects.filter(team=team, card_type='RED').count()
        team_card_stats.append({
            'team_obj': team,
            'yellow_cards': yellow_cards,
            'red_cards': red_cards
        })

    # Sắp xếp danh sách thống kê đội
    team_goal_stats.sort(key=lambda x: (x['gd'], x['gf']), reverse=True)
    team_card_stats.sort(key=lambda x: (x['red_cards'], x['yellow_cards']), reverse=True)


    # === KẾT THÚC KHỐI THỐNG KÊ MỚI ===

    # Kiểm tra xem có ít nhất một đội đã thanh toán trong giải đấu chưa
    has_paid_teams = tournament.teams.filter(payment_status='PAID').exists()
    
    context = {
        'tournament': tournament,
        'is_organizer': is_organizer,
        'group_matches': group_matches,
        'knockout_matches': all_knockout_matches,
        'knockout_data': knockout_data, 
        'now': timezone.now(),
        'unassigned_teams': unassigned_teams,
        'standings_data': standings_data,
        'has_paid_teams': has_paid_teams, # Giữ lại biến này

        # --- Gửi các biến thống kê mới ra template ---
        'total_teams': total_teams,
        'total_players': total_players,
        'finished_matches_count': finished_matches_count,
        'total_normal_goals': total_normal_goals,
        'total_own_goals': total_own_goals,
        'avg_goals_per_match': avg_goals_per_match,
        'total_yellow_cards': total_yellow_cards,
        'total_red_cards': total_red_cards,
        'hattricks': hattricks,
        'top_scorers': top_scorers,
        'team_goal_stats': team_goal_stats,
        'team_card_stats': team_card_stats,
        'matches_with_galleries': matches_with_galleries,
    }
    return render(request, 'tournaments/tournament_detail.html', context)


@login_required
def add_free_agent(request, team_pk, player_pk):
    team = get_object_or_404(Team, pk=team_pk)
    # Đảm bảo chỉ đội trưởng của đội mới có quyền thêm cầu thủ
    if request.user != team.captain:
        messages.error(request, "Bạn không có quyền thực hiện hành động này.")
        return redirect('team_detail', pk=team_pk)

    player = get_object_or_404(Player, pk=player_pk, team__isnull=True) # Chỉ tìm cầu thủ tự do

    if request.method == 'POST':
        # Kiểm tra xem số áo đã tồn tại trong đội chưa
        if team.players.filter(jersey_number=player.jersey_number).exists():
            messages.error(request, f"Số áo {player.jersey_number} đã có người sử dụng trong đội của bạn.")
            return redirect('team_detail', pk=team_pk)
        
        # Gán cầu thủ vào đội và lưu lại
        player.team = team
        player.save()
        messages.success(request, f"Đã chiêu mộ thành công cầu thủ {player.full_name} vào đội!")
        return redirect('team_detail', pk=team_pk)

    # Nếu không phải POST, chỉ hiển thị trang xác nhận (tùy chọn) hoặc redirect
    return redirect('team_detail', pk=team_pk)

@login_required
@never_cache
def team_detail(request, pk):
    team = get_object_or_404(Team, pk=pk)
    achievements = team.achievements.select_related('tournament').all()
    
    player_form = PlayerCreationForm()
    search_query = request.GET.get('q', '')
    search_results = []
    active_tab = ''

    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'create_new_player':
            active_tab = 'new'
            
            if request.user != team.captain:
                messages.error(request, "Bạn không có quyền thực hiện hành động này.")
            else:
                player_form = PlayerCreationForm(request.POST, request.FILES)
                if player_form.is_valid():
                    player = player_form.save(commit=False)
                    player.team = team
                    try:
                        player.full_clean()
                        player.save()
                        messages.success(request, f"Đã thêm cầu thủ {player.full_name} thành công!")
                        return redirect('team_detail', pk=team.pk)
                    
                    except ValidationError as e:
                        # --- BẮT ĐẦU NÂNG CẤP XỬ LÝ LỖI ---
                        # Vòng lặp qua các lỗi mà model trả về
                        for field, errors in e.message_dict.items():
                            user_friendly_message = ""
                            # Dịch các lỗi phổ biến sang tiếng Việt
                            if field == 'jersey_number' and 'unique' in errors[0]:
                                user_friendly_message = "Số áo này đã có người sử dụng trong đội."
                            else:
                                user_friendly_message = errors[0] # Giữ lại lỗi gốc nếu chưa dịch

                            # Gắn lỗi vào đúng trường của form
                            # Nếu lỗi không thuộc trường nào, nó sẽ được hiển thị ở đầu form
                            player_form.add_error(field if field != '__all__' else None, user_friendly_message)
                        
                        messages.error(request, 'Thêm cầu thủ thất bại, vui lòng kiểm tra lại.')
                        # --- KẾT THÚC NÂNG CẤP ---

                else:
                    messages.error(request, 'Thêm cầu thủ thất bại. Vui lòng kiểm tra các lỗi được đánh dấu màu đỏ.')

    elif search_query:
        active_tab = 'search'
        search_results = Player.objects.filter(
            Q(full_name__icontains=search_query) & Q(team__isnull=True)
        ).exclude(user__isnull=False)

    context = {
        'team': team,
        'player_form': player_form,
        'achievements': achievements,
        'search_results': search_results,
        'search_query': search_query,
        'active_tab': active_tab,
    }
    return render(request, 'tournaments/team_detail.html', context)


@login_required
@never_cache
def create_team(request, tournament_pk):
    tournament = get_object_or_404(Tournament, pk=tournament_pk)
    if request.method == 'POST':
        # === THAY ĐỔI DÒNG NÀY ===
        form = TeamCreationForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            # Bỏ try-except vì form đã xử lý lỗi trùng tên của captain
            team = form.save(commit=False)
            team.tournament = tournament
            team.captain = request.user
            
            # Chỉ cần bắt lỗi trùng tên trong cùng giải đấu
            try:
                team.save()
                return redirect('team_detail', pk=team.pk)
            except IntegrityError:
                 form.add_error('name', "Tên đội này đã tồn tại trong giải đấu. Vui lòng chọn một tên khác.")

    else:
        # === VÀ THAY ĐỔI DÒNG NÀY ===
        form = TeamCreationForm(user=request.user)
        
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

    # === LOGIC KIỂM TRA MỚI ===
    can_edit = player.votes < 3 and player.edit_count < 3
    if not can_edit:
        if player.votes >= 3:
            messages.error(request, f"Không thể chỉnh sửa. Cầu thủ {player.full_name} đã có 3 phiếu bầu trở lên.")
        else: # edit_count >= 3
            messages.error(request, f"Không thể chỉnh sửa. Đã hết số lần cho phép (3 lần) cho cầu thủ {player.full_name}.")
        return redirect('team_detail', pk=team.pk)

    if request.method == 'POST':
        form = PlayerCreationForm(request.POST, request.FILES, instance=player)
        if form.is_valid():
            # Tăng số lần chỉnh sửa trước khi lưu
            player.edit_count += 1
            form.save()
            remaining = 3 - player.edit_count
            messages.success(request, f"Đã cập nhật thông tin cho cầu thủ {player.full_name}. Số lần sửa còn lại: {remaining}.")
            return redirect('team_detail', pk=team.pk)
    else:
        form = PlayerCreationForm(instance=player)

    context = {
        'form': form,
        'player': player,
        'remaining_edits': 3 - player.edit_count, # Gửi số lần sửa còn lại ra template
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

# === THAY THẾ TOÀN BỘ HÀM NÀY BẰNG PHIÊN BẢN MỚI ===
@never_cache
def match_detail(request, pk):
    # Lấy thông tin trận đấu và các đội liên quan để tối ưu
    match = get_object_or_404(
        Match.objects.select_related('tournament', 'team1', 'team2'),
        pk=pk
    )

    weather_data = None
    if match.match_time and timezone.now() < match.match_time < timezone.now() + timedelta(days=14):
        weather_data = get_weather_for_match(match.location, match.match_time, match.tournament.region)

    # --- PHẦN LẤY DỮ LIỆU ĐỘI HÌNH VÀ THỐNG KÊ ---
    all_goals_in_match = Goal.objects.filter(match=match).select_related('player', 'team')
    all_cards_in_match = Card.objects.filter(match=match).select_related('player', 'team')
    all_substitutions_in_match = Substitution.objects.filter(match=match).select_related('player_in', 'player_out', 'team')
    match_events = list(match.events.all())

    events = sorted(
        list(all_goals_in_match) + list(all_cards_in_match) + list(all_substitutions_in_match) + match_events,
        key=lambda x: x.created_at
    )

    def get_team_lineup_with_stats(team):
        lineup_entries = Lineup.objects.filter(match=match, team=team).select_related('player')
        lineup_with_stats = []
        for entry in lineup_entries:
            player = entry.player
            goals_in_this_match = all_goals_in_match.filter(player=player, is_own_goal=False).count()
            yellow_cards_in_this_match = all_cards_in_match.filter(player=player, card_type='YELLOW').count()
            red_cards_in_this_match = all_cards_in_match.filter(player=player, card_type='RED').count()
            lineup_with_stats.append({
                'player': player,
                'status': entry.get_status_display(),
                'goals': goals_in_this_match,
                'yellow_cards': yellow_cards_in_this_match,
                'red_cards': red_cards_in_this_match,
            })
        return lineup_with_stats

    team1_lineup_full = get_team_lineup_with_stats(match.team1)
    team2_lineup_full = get_team_lineup_with_stats(match.team2)

    team1_starters = [p for p in team1_lineup_full if p['status'] == 'Đá chính']
    team1_substitutes = [p for p in team1_lineup_full if p['status'] == 'Dự bị']
    team2_starters = [p for p in team2_lineup_full if p['status'] == 'Đá chính']
    team2_substitutes = [p for p in team2_lineup_full if p['status'] == 'Dự bị']
    
    captain_team = None
    if request.user.is_authenticated:
        if match.team1.captain == request.user:
            captain_team = match.team1
        elif match.team2.captain == request.user:
            captain_team = match.team2

    # === DÒNG QUAN TRỌNG ĐƯỢC THÊM VÀO ===
    can_control_match = user_can_control_match(request.user, match)
    
    context = {
        'match': match,
        'team1_starters': team1_starters,
        'team1_substitutes': team1_substitutes,
        'team2_starters': team2_starters,
        'team2_substitutes': team2_substitutes,
        'events': events,
        'captain_team': captain_team,
        'weather_data': weather_data,
        'can_control_match': can_control_match, # Gửi biến quyền ra template
    }
    return render(request, 'tournaments/match_detail.html', context)


# backend Kéo Thả đội hình thi đấu
@login_required
@never_cache
def manage_lineup(request, match_pk, team_pk):
    match = get_object_or_404(Match.objects.select_related('team1', 'team2', 'tournament'), pk=match_pk)
    team = get_object_or_404(Team, pk=team_pk)

    if request.user != team.captain and not request.user.is_staff:
        messages.error(request, "Bạn không có quyền truy cập trang này.")
        return redirect('match_detail', pk=match.pk)

    if request.method == "POST":
        starters_ids_str = request.POST.get('starters', '')
        substitutes_ids_str = request.POST.get('substitutes', '')

        starter_ids = [int(pid) for pid in starters_ids_str.split(',') if pid]
        substitute_ids = [int(pid) for pid in substitutes_ids_str.split(',') if pid]

        try:
            with transaction.atomic():
                Lineup.objects.filter(match=match, team=team).delete()

                for player_id in starter_ids:
                    player = get_object_or_404(Player, pk=player_id, team=team)
                    Lineup.objects.create(match=match, player=player, team=team, status='STARTER')

                for player_id in substitute_ids:
                    player = get_object_or_404(Player, pk=player_id, team=team)
                    Lineup.objects.create(match=match, player=player, team=team, status='SUBSTITUTE')

            messages.success(request, "Đã lưu đội hình thành công!")
            return redirect('match_detail', pk=match.pk)
        except Exception as e:
            messages.error(request, f"Đã có lỗi xảy ra khi lưu đội hình: {e}")
            return redirect('manage_lineup', match_pk=match.pk, team_pk=team.pk)

    existing_lineup = {
        'starters': list(Lineup.objects.filter(match=match, team=team, status='STARTER').values_list('player_id', flat=True)),
        'substitutes': list(Lineup.objects.filter(match=match, team=team, status='SUBSTITUTE').values_list('player_id', flat=True)),
    }
    context = {
        "match": match,
        "team": team,
        "existing_lineup_json": json.dumps(existing_lineup),  # an toàn + dễ parse
    }
    return render(request, "tournaments/manage_lineup.html", context)
    

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
    
    # === BẮT ĐẦU THAY ĐỔI ===
    # Lấy thêm danh sách ID các giải đấu mà người dùng theo dõi
    tournament_ids_as_follower = set(
        request.user.followed_tournaments.values_list('id', flat=True)
    )

    # Gộp tất cả các ID lại với nhau
    all_relevant_ids = tournament_ids_as_captain.union(tournament_ids_as_player, tournament_ids_as_follower)
    # === KẾT THÚC THAY ĐỔI ===

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

    # Đánh dấu các thông báo là đã đọc
    unread_announcements = announcements.exclude(read_by=request.user)
    if unread_announcements.exists():
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
            # Gửi thông báo
            send_schedule_notification(
                tournament,
                Notification.NotificationType.DRAW_COMPLETE,
                f"Giải đấu '{tournament.name}' đã có kết quả bốc thăm",
                "Kết quả bốc thăm chia bảng đã có. Hãy vào xem chi tiết.",
                'tournament_detail'
            )            
            # CHỈNH SỬA TẠI ĐÂY
            return redirect(reverse('tournament_detail', kwargs={'pk': tournament.pk}) + '?tab=teams#teams')

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


@login_required
@never_cache
def generate_schedule_view(request, tournament_pk):
    tournament = get_object_or_404(Tournament, pk=tournament_pk)

    is_organizer = tournament.organization and tournament.organization.members.filter(pk=request.user.pk).exists()
    if not request.user.is_staff and not is_organizer:
        return HttpResponseForbidden("Bạn không có quyền truy cập trang này.")

    if not tournament.groups.exists() or tournament.teams.filter(payment_status='PAID', group__isnull=True).exists() or not tournament.teams.filter(payment_status='PAID').exists():
        messages.error(request, "Không thể xếp lịch. Cần tạo bảng, có đội đã đăng ký và tất cả các đội phải được bốc thăm vào bảng.")
        return redirect('tournament_detail', pk=tournament.pk)

    if tournament.matches.filter(match_round='GROUP').exists():
        messages.warning(request, "Lịch thi đấu vòng bảng đã được tạo cho giải này.")
        return redirect('tournament_detail', pk=tournament.pk)

    if request.method == 'POST':
        if 'confirm_schedule' in request.POST:
            schedule_preview_json = request.session.get('schedule_preview_json')
            if not schedule_preview_json:
                messages.error(request, "Không tìm thấy lịch thi đấu xem trước. Vui lòng tạo lại.")
                return redirect('generate_schedule', tournament_pk=tournament.pk)

            try:
                with transaction.atomic():
                    Match.objects.filter(tournament=tournament, match_round='GROUP').delete()
                    schedule_to_save = json.loads(schedule_preview_json)
                    for match_data in schedule_to_save:
                        Match.objects.create(
                            tournament=tournament,
                            team1_id=match_data['team1_id'],
                            team2_id=match_data['team2_id'],
                            match_time=datetime.fromisoformat(match_data['match_time']),
                            location=match_data['location'],
                            match_round='GROUP'
                        )
                del request.session['schedule_preview_json']
                messages.success(request, "Lịch thi đấu đã được tạo thành công!")
                send_schedule_notification(
                    tournament, Notification.NotificationType.SCHEDULE_CREATED,
                    f"Giải đấu '{tournament.name}' đã có lịch thi đấu",
                    "Lịch thi đấu vòng bảng đã được tạo. Hãy vào xem chi tiết.",
                    'tournament_detail'
                )
                return redirect(reverse('tournament_detail', kwargs={'pk': tournament.pk}) + '?tab=schedule#schedule')
            except Exception as e:
                messages.error(request, f"Lỗi khi lưu lịch thi đấu: {e}")
                return redirect('generate_schedule', tournament_pk=tournament.pk)

        else:
            form = ScheduleGenerationForm(request.POST)
            if form.is_valid():
                data = form.cleaned_data
                strategy = data['scheduling_strategy']
                matches_per_group_str = data.get('matches_per_group_per_week', '')

                group_limits = {}
                if matches_per_group_str:
                    try:
                        pairs = [p.strip() for p in matches_per_group_str.split(',') if p.strip()]
                        for pair in pairs:
                            name, limit = pair.split(':')
                            group_limits[name.strip()] = int(limit.strip())
                    except Exception:
                        messages.error(request, "Định dạng 'Giới hạn trận đấu MỖI BẢNG' không hợp lệ. Ví dụ đúng: Bảng A:2, Bảng B:1")
                        return redirect('generate_schedule', tournament_pk=tournament.pk)

                start_date = data['start_date']
                time_slots_str = [t.strip() for t in data['time_slots'].split(',')]
                locations = [loc.strip() for loc in data['locations'].split(',')]
                rest_days = timedelta(days=data['rest_days'])
                selected_weekdays = {int(d) for d in data['weekdays']}
                matches_per_week = data.get('matches_per_week')
                max_matches_per_team_per_week = data.get('max_matches_per_team_per_week')

                all_pairings_by_group = {}
                groups = sorted(list(tournament.groups.prefetch_related('teams').all()), key=lambda g: g.name)
                for group in groups:
                    teams_in_group = list(group.teams.all())
                    group_pairings = list(combinations(teams_in_group, 2))
                    random.shuffle(group_pairings)
                    all_pairings_by_group[group] = [{'pair': pair, 'group_name': group.name} for pair in group_pairings]

                scheduled_matches = []
                team_last_played = {}
                current_date = start_date
                day_offset = 0
                team_matches_this_week = defaultdict(int)
                group_matches_this_week = defaultdict(int)
                last_week_checked = start_date.isocalendar()[1]

                while any(all_pairings_by_group.values()) and day_offset <= 365:
                    current_week = current_date.isocalendar()[1]
                    if current_week != last_week_checked:
                        team_matches_this_week.clear()
                        group_matches_this_week.clear()
                        last_week_checked = current_week

                    if current_date.weekday() in selected_weekdays:
                        for time_str in time_slots_str:
                            for location in locations:
                                matches_this_week_count = sum(1 for m in scheduled_matches if datetime.fromisoformat(m['match_time']).isocalendar()[1] == current_week)
                                if matches_per_week and matches_this_week_count >= matches_per_week: break

                                try:
                                    time_parts = time_str.split(':')
                                    current_datetime = datetime.combine(current_date, time.fromisoformat(f"{time_parts[0].zfill(2)}:{time_parts[1]}"))
                                except ValueError: continue

                                group_pool = groups if strategy == 'PRIORITIZED' else random.sample(groups, len(groups))

                                match_scheduled_in_slot = False
                                for group in group_pool:
                                    if match_scheduled_in_slot: break
                                    if not all_pairings_by_group.get(group): continue

                                    group_limit = group_limits.get(group.name)
                                    if group_limit is not None and group_matches_this_week[group.id] >= group_limit: continue

                                    for i, pairing_info in enumerate(all_pairings_by_group[group]):
                                        team1, team2 = pairing_info['pair']

                                        can_play1 = not team_last_played.get(team1.id) or (current_date - team_last_played[team1.id].date()) >= rest_days
                                        can_play2 = not team_last_played.get(team2.id) or (current_date - team_last_played[team2.id].date()) >= rest_days
                                        team1_weekly_ok = not max_matches_per_team_per_week or team_matches_this_week[team1.id] < max_matches_per_team_per_week
                                        team2_weekly_ok = not max_matches_per_team_per_week or team_matches_this_week[team2.id] < max_matches_per_team_per_week

                                        if can_play1 and can_play2 and team1_weekly_ok and team2_weekly_ok:
                                            scheduled_matches.append({ 'team1_name': team1.name, 'team1_id': team1.id, 'team2_name': team2.name, 'team2_id': team2.id, 'match_time': current_datetime.isoformat(), 'location': location, 'group_name': group.name })
                                            team_last_played[team1.id] = team_last_played[team2.id] = current_datetime
                                            team_matches_this_week[team1.id] += 1
                                            team_matches_this_week[team2.id] += 1
                                            group_matches_this_week[group.id] += 1
                                            all_pairings_by_group[group].pop(i)
                                            match_scheduled_in_slot = True
                                            break

                            if matches_per_week and matches_this_week_count >= matches_per_week: break

                    day_offset += 1
                    current_date = start_date + timedelta(days=day_offset)

                unscheduled_matches = [p['pair'] for pairings in all_pairings_by_group.values() for p in pairings]

                schedule_by_group = defaultdict(list)
                scheduled_matches.sort(key=lambda x: x['match_time'])
                for match in scheduled_matches:
                    match['match_time'] = datetime.fromisoformat(match['match_time'])
                    schedule_by_group[match['group_name']].append(match)

                request.session['schedule_preview_json'] = json.dumps([{**m, 'match_time': m['match_time'].isoformat()} for m in scheduled_matches])

                context = { 'tournament': tournament, 'form': form, 'schedule_by_group': dict(sorted(schedule_by_group.items())), 'unscheduled_matches': unscheduled_matches, }
                return render(request, 'tournaments/generate_schedule.html', context)

    form = ScheduleGenerationForm(initial={'start_date': timezone.now().date() + timedelta(days=1)})
    context = { 'tournament': tournament, 'form': form, 'schedule_by_group': None, 'unscheduled_matches': None, }
    return render(request, 'tournaments/generate_schedule.html', context)


def player_detail(request, pk):
    player = get_object_or_404(Player.objects.select_related('team__tournament'), pk=pk)

    # === BẮT ĐẦU SỬA LỖI: Lấy tournament một cách an toàn ===
    tournament = player.team.tournament if player.team else None
    # === KẾT THÚC SỬA LỖI ===

    age = None
    if player.date_of_birth:
        today = date.today()
        age = today.year - player.date_of_birth.year - ((today.month, today.day) < (player.date_of_birth.month, player.date_of_birth.day))

    teams_played_for_ids = Player.objects.filter(full_name__iexact=player.full_name).values_list('team_id', flat=True)
    player_achievements = TeamAchievement.objects.filter(team_id__in=teams_played_for_ids).select_related('tournament').order_by('-achieved_at')

    current_vote_value = get_current_vote_value()
    value_from_votes = player.votes * current_vote_value
    total_value = player.transfer_value + value_from_votes

    total_goals = Goal.objects.filter(player=player, is_own_goal=False).count()
    cards = Card.objects.filter(player=player).aggregate(yellow_cards=Count('id', filter=Q(card_type='YELLOW')), red_cards=Count('id', filter=Q(card_type='RED')))
    matches_played = Match.objects.filter(lineups__player=player).distinct().select_related('tournament', 'team1', 'team2').order_by('-match_time')

    stats = {
        'total_goals': total_goals,
        'yellow_cards': cards.get('yellow_cards', 0),
        'red_cards': cards.get('red_cards', 0),
        'matches_played': matches_played,
        'matches_played_count': matches_played.count(),
    }
    
    badges = []
    # === BẮT ĐẦU SỬA LỖI: Chỉ tính huy hiệu nếu có giải đấu ===
    if tournament:
        top_scorer = Player.objects.filter(team__tournament=tournament).annotate(goal_count=Count('goals', filter=Q(goals__is_own_goal=False))).order_by('-goal_count').first()
        if top_scorer and top_scorer.pk == player.pk and stats['total_goals'] > 0:
            badges.append({'name': 'Vua phá lưới', 'icon': 'bi-trophy-fill', 'color': 'text-warning'})
        
        most_played = Player.objects.filter(team__tournament=tournament).annotate(match_count=Count('lineups')).order_by('-match_count').first()
        if most_played and most_played.pk == player.pk and stats['matches_played_count'] > 0:
            badges.append({'name': 'Cột trụ đội bóng', 'icon': 'bi-gem', 'color': 'text-info'})
    # === KẾT THÚC SỬA LỖI ===
            
    if stats['yellow_cards'] == 0 and stats['red_cards'] == 0 and stats['matches_played_count'] > 0:
        badges.append({'name': 'Cầu thủ Fair-play', 'icon': 'bi-shield-check', 'color': 'text-primary'})

    context = {
        'player': player,
        'stats': stats,
        'badges': badges,
        'player_achievements': player_achievements,
        'age': age,
        'value_from_votes': value_from_votes,
        'total_value': total_value,
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
    
    # === DÒNG KIỂM TRA QUYỀN ĐÃ ĐƯỢC CẬP NHẬT ===
    if not user_can_upload_gallery(request.user, tournament):
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

# TẠO LỊCH THI ĐẤU ĐẸP
def tournament_schedule_print_view(request, pk):
    tournament = get_object_or_404(Tournament, pk=pk)

    # --- BẮT ĐẦU THÊM KHỐI CODE KIỂM TRA QUYỀN ---
    if not request.user.is_authenticated:
        return HttpResponseForbidden("Bạn cần đăng nhập để xem trang này.")

    is_organizer = False
    if tournament.organization:
        is_organizer = tournament.organization.members.filter(pk=request.user.pk).exists()

    if not request.user.is_staff and not is_organizer:
        return HttpResponseForbidden("Bạn không có quyền truy cập trang này.")
    # --- KẾT THÚC KHỐI CODE KIỂM TRA QUYỀN ---

    # Lấy tất cả các bảng đấu và các trận đấu tương ứng
    groups_with_matches = []
    groups = tournament.groups.all().order_by('name')
    for group in groups:
        matches = Match.objects.filter(
            tournament=tournament, 
            team1__group=group
        ).select_related('team1', 'team2').order_by('match_time')
        groups_with_matches.append({'group_name': group.name, 'matches': matches})

    # Chia các bảng đấu thành các trang, mỗi trang 4 bảng
    page_size = 4
    group_pages = [
        groups_with_matches[i:i + page_size] 
        for i in range(0, len(groups_with_matches), page_size)
    ]

    context = {
        'tournament': tournament,
        'group_pages': group_pages,
    }
    return render(request, 'tournaments/schedule_print.html', context)    

def privacy_policy_view(request):
    """Hiển thị trang chính sách quyền riêng tư."""
    return render(request, 'tournaments/legal/privacy_policy.html')

def terms_of_service_view(request):
    """Hiển thị trang điều khoản dịch vụ."""
    return render(request, 'tournaments/legal/terms_of_service.html')

def data_deletion_view(request):
    """Hiển thị trang hướng dẫn xóa dữ liệu."""
    return render(request, 'tournaments/legal/data_deletion.html') 

@login_required
@require_POST # Chỉ cho phép truy cập bằng phương thức POST
def toggle_follow_view(request, pk):
    tournament = get_object_or_404(Tournament, pk=pk)
    user = request.user

    if user in tournament.followers.all():
        # Nếu đã theo dõi -> Bỏ theo dõi
        tournament.followers.remove(user)
        is_following = False
    else:
        # Nếu chưa theo dõi -> Theo dõi
        tournament.followers.add(user)
        is_following = True

    return JsonResponse({'status': 'ok', 'is_following': is_following})      

# === Thong bao tu dong ===
@login_required
@never_cache
def notification_list(request):
    """
    Hiển thị danh sách tất cả thông báo cho người dùng đã đăng nhập.
    Đánh dấu tất cả là đã đọc khi người dùng truy cập trang này.
    """
    notifications = Notification.objects.filter(user=request.user)

    # Lấy danh sách ID các thông báo chưa đọc và sau đó cập nhật chúng
    unread_notification_ids = list(notifications.filter(is_read=False).values_list('id', flat=True))
    if unread_notification_ids:
        Notification.objects.filter(id__in=unread_notification_ids).update(is_read=True)

    context = {
        'notifications': notifications
    }
    return render(request, 'tournaments/notification_list.html', context)

# === Đọc Tất Cả Thông Báo ===
@login_required
@require_POST
def mark_all_notifications_as_read(request):
    """
    Đánh dấu tất cả các thông báo của người dùng hiện tại là đã đọc.
    """
    Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    messages.success(request, "Tất cả thông báo đã được đánh dấu là đã đọc.")
    return redirect('home') # Chuyển hướng về trang chủ

# === THÊM MỚI: Hàm xóa một thông báo ===
@login_required
@require_POST
def delete_notification(request, pk):
    """
    Xóa một thông báo cụ thể.
    """
    # Lấy thông báo, đảm bảo chỉ user sở hữu mới có thể xóa
    notification = get_object_or_404(Notification, pk=pk, user=request.user)
    notification.delete()
    messages.success(request, "Đã xóa thông báo.")
    return redirect('notification_list')

# === THÊM MỚI: Hàm xóa tất cả thông báo ===
@login_required
@require_POST
def delete_all_notifications(request):
    """
    Xóa tất cả thông báo của người dùng hiện tại.
    """
    Notification.objects.filter(user=request.user).delete()
    messages.success(request, "Đã xóa tất cả thông báo.")
    return redirect('notification_list')

# === Xử lý thành tích đội bóng ===
@login_required
@never_cache
def team_hall_of_fame(request, pk):
    team = get_object_or_404(Team, pk=pk)
    achievements = team.achievements.select_related('tournament').order_by('-tournament__start_date')

    # Chỉ đội trưởng mới có thể upload ảnh
    form = None
    if request.user == team.captain:
        form = TeamCreationForm(instance=team, user=request.user) # Tạm thời dùng form cũ để upload ảnh
        if request.method == 'POST':
            form = TeamCreationForm(request.POST, request.FILES, instance=team, user=request.user)
            if 'main_photo' in request.FILES:
                team.main_photo = request.FILES['main_photo']
                team.save()
                messages.success(request, "Đã cập nhật ảnh đại diện cho đội!")
                return redirect('team_hall_of_fame', pk=team.pk)

    context = {
        'team': team,
        'achievements': achievements,
        'form': form,
    }
    return render(request, 'tournaments/team_hall_of_fame.html', context)

# === live Room ===
@login_required
@never_cache
def match_control_view(request, pk):
    match = get_object_or_404(
        Match.objects.select_related('tournament__organization', 'team1', 'team2'),
        pk=pk
    )

    if not user_can_control_match(request.user, match):
        return HttpResponseForbidden("Bạn không có quyền truy cập phòng điều khiển trực tiếp này.")

    if request.method == 'POST':
        # ... (toàn bộ logic xử lý POST giữ nguyên, không cần thay đổi) ...
        action = request.POST.get('action')

        if action in ['add_goal', 'add_card', 'add_substitution', 'add_match_event']:
            players_in_match_qs = Player.objects.filter(team__in=[match.team1_id, match.team2_id])
            
            form = None
            if action == 'add_goal':
                form = GoalForm(request.POST)
                form.fields['player'].queryset = players_in_match_qs
                if form.is_valid():
                    instance = form.save(commit=False)
                    instance.match = match
                    instance.save() 

                    match.refresh_from_db()
                    is_own_goal = form.cleaned_data.get('is_own_goal', False)
                    goal_scoring_team = instance.player.team

                    match.team1_score = match.team1_score or 0
                    match.team2_score = match.team2_score or 0

                    if is_own_goal:
                        if goal_scoring_team == match.team1:
                            match.team2_score += 1
                        else:
                            match.team1_score += 1
                    else:
                        if goal_scoring_team == match.team1:
                            match.team1_score += 1
                        else:
                            match.team2_score += 1
                    
                    match.save() 

                    response_data = {
                        'status': 'success',
                        'event': {
                            'type': 'goal',
                            'id': instance.pk,
                            'minute': instance.minute or '-',
                            'team_name': instance.team.name,
                            'team_class': 'team1' if instance.team == match.team1 else 'team2',
                            'player_name': instance.player.full_name,
                            'is_own_goal': instance.is_own_goal
                        },
                        'new_scores': {
                            'team1_score': match.team1_score,
                            'team2_score': match.team2_score
                        }
                    }
                    return JsonResponse(response_data)

            elif action == 'add_card':
                form = CardForm(request.POST)
                form.fields['player'].queryset = players_in_match_qs
            elif action == 'add_substitution':
                starters_qs = Player.objects.filter(lineups__match=match, lineups__status='STARTER')
                subs_qs = Player.objects.filter(lineups__match=match, lineups__status='SUBSTITUTE')
                form = SubstitutionForm(request.POST)
                form.fields['player_in'].queryset = subs_qs
                form.fields['player_out'].queryset = starters_qs

            if action == 'add_match_event':
                event_type = request.POST.get('event_type')
                current_score = request.POST.get('current_score', '')
                text = ""
                if event_type == MatchEvent.EventType.MATCH_START: text = "Trận đấu bắt đầu!"
                elif event_type == MatchEvent.EventType.HALF_TIME: text = f"Hết hiệp 1. Tỉ số tạm thời là {current_score}."
                elif event_type == MatchEvent.EventType.MATCH_END: text = f"Trận đấu kết thúc. Tỉ số chung cuộc là {current_score}."
                if text:
                    event = MatchEvent.objects.create(match=match, event_type=event_type, text=text)
                    return JsonResponse({'status': 'success', 'event': {'type': 'match_event', 'id': event.pk, 'text': event.text, 'event_type': event.event_type, 'created_at': event.created_at.strftime('%H:%M')}})
                return JsonResponse({'status': 'error', 'message': 'Loại sự kiện không hợp lệ.'}, status=400)

            if form and form.is_valid():
                instance = form.save(commit=False)
                instance.match = match
                instance.save()
                
                response_data = {'status': 'success', 'event': {'id': instance.pk, 'minute': instance.minute or '-', 'team_name': instance.team.name, 'team_class': 'team1' if instance.team == match.team1 else 'team2'}}
                if action == 'add_card':
                    response_data['event'].update({'type': 'card', 'player_name': instance.player.full_name, 'card_type': instance.card_type})
                elif action == 'add_substitution':
                     response_data['event'].update({'type': 'substitution', 'player_in_name': instance.player_in.full_name, 'player_out_name': instance.player_out.full_name})

                return JsonResponse(response_data)
            else:
                error_str = ". ".join([f"{field}: {err[0]}" for field, err in form.errors.items()]) if form and form.errors else "Form không hợp lệ."
                return JsonResponse({'status': 'error', 'message': error_str}, status=400)
        
        if action == 'update_score':
            try:
                score1_str = request.POST.get('team1_score')
                score2_str = request.POST.get('team2_score')
                
                match.team1_score = int(score1_str) if score1_str.isdigit() else None
                match.team2_score = int(score2_str) if score2_str.isdigit() else None
                
                match.save()
                return JsonResponse({'status': 'success', 'message': 'Đã lưu tỉ số.'})
            except (ValueError, TypeError):
                return JsonResponse({'status': 'error', 'message': 'Giá trị tỉ số không hợp lệ.'}, status=400)
        
        return redirect('match_control', pk=match.pk)


    # --- Logic cho GET request ---
    substituted_out_player_ids = set(Substitution.objects.filter(match=match).values_list('player_out_id', flat=True))
    lineup_entries = Lineup.objects.filter(match=match).select_related('player')
    starters_ids = {entry.player.id for entry in lineup_entries if entry.status == 'STARTER'}
    substitutes_ids = {entry.player.id for entry in lineup_entries if entry.status == 'SUBSTITUTE'}
    lineup_is_set = bool(starters_ids or substitutes_ids)
    players_team1 = Player.objects.filter(team=match.team1).order_by('jersey_number')
    starters_team1 = [p for p in players_team1 if p.id in starters_ids]
    substitutes_team1 = [p for p in players_team1 if p.id in substitutes_ids]
    players_team2 = Player.objects.filter(team=match.team2).order_by('jersey_number')
    starters_team2 = [p for p in players_team2 if p.id in starters_ids]
    substitutes_team2 = [p for p in players_team2 if p.id in substitutes_ids]
    goals = list(match.goals.select_related('player', 'team').all())
    cards = list(match.cards.select_related('player', 'team').all())
    substitutions = list(match.substitutions.select_related('player_in', 'player_out', 'team').all())
    match_events = list(match.events.all())
    all_events = sorted(goals + cards + substitutions + match_events, key=lambda x: x.created_at, reverse=True)

    # === BẮT ĐẦU NÂNG CẤP: TẠO THÔNG BÁO ẢO CHO BLV ===
    # Chỉ kiểm tra khi chưa có sự kiện nào diễn ra
    if not all_events:
        captain_notes = MatchNote.objects.filter(
            match=match, 
            note_type=MatchNote.NoteType.CAPTAIN
        ).select_related('team')
        
        if captain_notes.exists():
            # Tạo một "sự kiện ảo" để chèn vào đầu danh sách
            note_alert_event = {
                'is_captain_note_alert': True, # Dùng cờ này để nhận biết trong template
                'notes': list(captain_notes) # Gửi danh sách ghi chú
            }
            all_events.insert(0, note_alert_event)
    # === KẾT THÚC NÂNG CẤP ===

    context = {
        'match': match,
        'events': all_events,
        'lineup_is_set': lineup_is_set,
        'players_team1': players_team1,
        'starters_team1': starters_team1,
        'substitutes_team1': substitutes_team1,
        'players_team2': players_team2,
        'starters_team2': starters_team2,
        'substitutes_team2': substitutes_team2,
        'substituted_out_player_ids': substituted_out_player_ids,
    }
    return render(request, 'tournaments/match_control.html', context)
    
# === Xoá dự liệu trận đấu nhập sai ===
@login_required
@require_POST
def delete_match_event(request, event_type, pk):
    """
    Xử lý việc xóa một sự kiện (bàn thắng, thẻ phạt, thay người, etc.)
    và hoàn tác các thay đổi liên quan (ví dụ: tỉ số).
    """
    try:
        with transaction.atomic():
            response_data = {'status': 'success'}
            
            # Xác định model dựa trên event_type
            if event_type == 'goal':
                event = get_object_or_404(Goal, pk=pk)
                match = event.match
                
                # Hoàn tác tỉ số
                is_own_goal = event.is_own_goal
                scoring_team = event.player.team
                
                if (not is_own_goal and scoring_team == match.team1) or \
                   (is_own_goal and scoring_team == match.team2):
                    if match.team1_score > 0: match.team1_score -= 1
                else:
                    if match.team2_score > 0: match.team2_score -= 1
                
                match.save()
                response_data['new_scores'] = {
                    'team1_score': match.team1_score,
                    'team2_score': match.team2_score,
                }

            elif event_type == 'card':
                event = get_object_or_404(Card, pk=pk)
            elif event_type == 'substitution':
                event = get_object_or_404(Substitution, pk=pk)
            elif event_type == 'match_event':
                event = get_object_or_404(MatchEvent, pk=pk)
            else:
                return JsonResponse({'status': 'error', 'message': 'Loại sự kiện không hợp lệ'}, status=400)
            
            # Kiểm tra quyền (chỉ người của BTC mới được xóa)
            is_organizer = event.match.tournament.organization and request.user in event.match.tournament.organization.members.all()
            if not request.user.is_staff and not is_organizer:
                return HttpResponseForbidden("Bạn không có quyền thực hiện hành động này.")

            event.delete()
            return JsonResponse(response_data)

    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)     

@login_required
@never_cache
def player_voting_view(request, tournament_pk):
    tournament = get_object_or_404(Tournament, pk=tournament_pk)
    user = request.user
    
    # 1. Xác định vai trò và quyền vote của người dùng trong giải đấu này
    user_role = "Khách"
    max_votes = 0
    
    is_organizer = tournament.organization and tournament.organization.members.filter(pk=user.pk).exists()
    is_captain = Team.objects.filter(tournament=tournament, captain=user).exists()
    is_player = Player.objects.filter(team__tournament=tournament, user=user).exists()
    
    is_specialist_staff = TournamentStaff.objects.filter(
        tournament=tournament, 
        user=user, 
        role__id__in=['COMMENTATOR', 'MEDIA', 'PHOTOGRAPHER', 'COLLABORATOR', 'TOURNAMENT_MANAGER']
    ).exists()

    if is_organizer:
        user_role = "Ban tổ chức"
        max_votes = 3
    elif is_captain:
        user_role = "Đội trưởng"
        max_votes = 2
    elif is_specialist_staff:
        staff_entry = TournamentStaff.objects.get(tournament=tournament, user=user)
        user_role = staff_entry.role.name
        max_votes = 2
    elif is_player:
        user_role = "Cầu thủ"
        max_votes = 1

    # 2. Tính toán số phiếu còn lại (bao gồm cả phiếu quà tặng)
    votes_cast_in_tournament = VoteRecord.objects.filter(voter=user, tournament=tournament).aggregate(total=Sum('weight'))['total'] or 0
    gift_votes_qs = VoteRecord.objects.filter(voter=user, tournament__isnull=True, voted_for__isnull=True)
    gift_votes_count = gift_votes_qs.count()

    total_available_votes = max_votes + gift_votes_count
    remaining_votes = total_available_votes - votes_cast_in_tournament

    progress_percentage = 0
    if total_available_votes > 0:
        progress_percentage = (votes_cast_in_tournament / total_available_votes) * 100
        
    # 3. Xử lý khi người dùng gửi phiếu bầu (giữ nguyên logic)
    if request.method == 'POST':
        player_id = request.POST.get('player_id')
        player_to_vote = get_object_or_404(Player, pk=player_id, team__tournament=tournament)

        already_voted_for_player = VoteRecord.objects.filter(
            voter=user, 
            voted_for=player_to_vote, 
            tournament=tournament
        ).exists()

        if remaining_votes <= 0:
            messages.error(request, "Bạn đã hết phiếu bầu cho giải đấu này.")
        elif player_to_vote.user == user:
            messages.error(request, "Bạn không thể tự bỏ phiếu cho chính mình.")
        elif already_voted_for_player:
            messages.warning(request, f"Bạn đã bỏ phiếu cho cầu thủ {player_to_vote.full_name} trước đó rồi.")
        else:
            try:
                with transaction.atomic():
                    gift_vote_to_use = gift_votes_qs.first()
                    if gift_vote_to_use:
                        gift_vote_to_use.tournament = tournament
                        gift_vote_to_use.voted_for = player_to_vote
                        gift_vote_to_use.save()
                    else:
                        VoteRecord.objects.create(
                            voter=user,
                            voted_for=player_to_vote,
                            tournament=tournament,
                            weight=1
                        )
                    
                    player_to_vote.votes = F('votes') + 1
                    player_to_vote.save()
                
                messages.success(request, f"Bạn đã bỏ phiếu thành công cho {player_to_vote.full_name}!")
                return redirect('player_voting', tournament_pk=tournament.pk)

            except Exception as e:
                messages.error(request, f"Đã có lỗi xảy ra: {e}")

    # === BẮT ĐẦU THAY ĐỔI LOGIC SẮP XẾP TẠI ĐÂY ===
    
    # Lấy danh sách cầu thủ ban đầu (chưa sắp xếp)
    players_list = list(Player.objects.filter(team__tournament=tournament).exclude(user=user).select_related('team'))
    
    # Lấy giá trị hiện tại của một phiếu bầu
    current_vote_value = get_current_vote_value()

    # Thêm thuộc tính 'market_value' vào mỗi đối tượng cầu thủ
    for player in players_list:
        value_from_votes = player.votes * current_vote_value
        player.market_value = player.transfer_value + value_from_votes
        
    # Sắp xếp danh sách cầu thủ bằng Python dựa trên 'market_value' từ cao đến thấp
    players_to_vote = sorted(players_list, key=lambda p: p.market_value, reverse=True)
    
    # === KẾT THÚC THAY ĐỔI LOGIC SẮP XẾP ===

    context = {
        'tournament': tournament,
        'players_to_vote': players_to_vote,
        'user_role': user_role,
        'max_votes': total_available_votes,
        'votes_cast_count': votes_cast_in_tournament,
        'remaining_votes': remaining_votes,
        'progress_percentage': progress_percentage,
        'current_vote_value': current_vote_value,
    }
    return render(request, 'tournaments/player_voting.html', context)    

@login_required
@require_POST # Chỉ cho phép truy cập bằng phương thức POST
def cast_vote_view(request, player_pk):
    player_to_vote = get_object_or_404(Player, pk=player_pk)
    tournament = player_to_vote.team.tournament
    user = request.user

    # 1. Xác định vai trò và quyền vote
    max_votes = 0
    is_organizer = tournament.organization and user in tournament.organization.members.all()
    is_captain = Team.objects.filter(tournament=tournament, captain=user).exists()
    is_player = Player.objects.filter(team__tournament=tournament, user=user).exists()

    if is_organizer: max_votes = 3
    elif is_captain: max_votes = 2
    elif is_player: max_votes = 1
    
    # 2. Kiểm tra các quy tắc
    votes_cast_count = VoteRecord.objects.filter(voter=user, tournament=tournament).aggregate(total=Sum('weight'))['total'] or 0
    if votes_cast_count >= max_votes:
        return JsonResponse({'status': 'error', 'message': 'Bạn đã hết phiếu bầu cho giải đấu này.'}, status=403)
    if player_to_vote.user == user:
        return JsonResponse({'status': 'error', 'message': 'Bạn không thể tự bỏ phiếu cho chính mình.'}, status=403)
    if VoteRecord.objects.filter(voter=user, voted_for=player_to_vote, tournament=tournament).exists():
        return JsonResponse({'status': 'error', 'message': f"Bạn đã bỏ phiếu cho cầu thủ {player_to_vote.full_name} trước đó rồi."}, status=403)

    # 3. Xử lý vote hợp lệ
    try:
        with transaction.atomic():
            VoteRecord.objects.create(voter=user, voted_for=player_to_vote, tournament=tournament, weight=1)
            # Dùng F() để cập nhật và lấy lại giá trị mới ngay lập tức
            player_to_vote.refresh_from_db(fields=['votes'])
            player_to_vote.votes = F('votes') + 1
            player_to_vote.save()
            player_to_vote.refresh_from_db(fields=['votes']) # Lấy giá trị vote mới nhất

        # Tạo thông báo (giữ nguyên)
        voter_name = user.get_full_name() or user.username
        # (Phần gửi thông báo có thể được tối ưu sau, tạm thời giữ nguyên)

        return JsonResponse({
            'status': 'success',
            'message': f'Bạn đã bỏ phiếu thành công cho {player_to_vote.full_name}!',
            'new_vote_count': player_to_vote.votes,
            'remaining_votes': max_votes - (votes_cast_count + 1)
        })
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': f'Đã có lỗi xảy ra ở server: {e}'}, status=500)         


#Đội tự do
@login_required
@never_cache
def create_standalone_team(request):
    if request.method == 'POST':
        form = TeamCreationForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            team = form.save(commit=False)
            team.captain = request.user
            team.payment_status = 'PAID' # Đội tự do được coi là đã "thanh toán" để có thể thêm cầu thủ
            team.save()
            messages.success(request, f"Đã tạo thành công đội '{team.name}'!")
            return redirect('team_detail', pk=team.pk)
    else:
        form = TeamCreationForm(user=request.user)

    context = {
        'form': form,
        'is_standalone': True
    }
    return render(request, 'tournaments/create_team.html', context)

@login_required
@never_cache
def media_dashboard(request, tournament_pk):
    tournament = get_object_or_404(Tournament, pk=tournament_pk)
    
    # Kiểm tra quyền: Phải là Media hoặc Nhiếp ảnh gia của giải này
    is_media_staff = TournamentStaff.objects.filter(
        tournament=tournament, user=request.user, role__id__in=['MEDIA', 'PHOTOGRAPHER', 'TOURNAMENT_MANAGER']
    ).exists()
    is_btc_member = tournament.organization and tournament.organization.members.filter(pk=request.user.pk).exists()

    if not request.user.is_staff and not is_btc_member and not is_media_staff:
        return HttpResponseForbidden("Bạn không có quyền truy cập khu vực này.")

    matches = tournament.matches.all().order_by('match_time')
    
    context = {
        'tournament': tournament,
        'matches': matches
    }
    return render(request, 'tournaments/media_dashboard.html', context)


# khu vực cho tk Media Và nhiếp ảnh
@login_required
@never_cache
def media_edit_match(request, pk):
    match = get_object_or_404(Match, pk=pk)
    tournament = match.tournament

    # Logic kiểm tra quyền (giữ nguyên)
    is_media_staff = TournamentStaff.objects.filter(
        tournament=tournament, user=request.user, role__id__in=['MEDIA', 'PHOTOGRAPHER', 'TOURNAMENT_MANAGER']
    ).exists()
    is_btc_member = tournament.organization and tournament.organization.members.filter(pk=request.user.pk).exists()

    if not request.user.is_staff and not is_btc_member and not is_media_staff:
        return HttpResponseForbidden("Bạn không có quyền truy cập trang này.")

    # === SỬA LỖI TẠI ĐÂY: SỬ DỤNG FORM MỚI ===
    if request.method == 'POST':
        form = MatchMediaUpdateForm(request.POST, request.FILES, instance=match)
        if form.is_valid():
            form.save()
            messages.success(request, f"Đã cập nhật thông tin media cho trận đấu: {match}.")
            return redirect('media_edit_match', pk=match.pk)
    else:
        form = MatchMediaUpdateForm(instance=match)
    # === KẾT THÚC SỬA LỖI ===

    context = {
        'form': form,
        'match': match,
        'tournament': tournament
    }
    return render(request, 'tournaments/media_edit_match.html', context)

# === Thị trường công việc ===
def job_market_view(request):
    # Lấy tham số lọc khu vực từ URL
    region_filter = request.GET.get('region', '')

    # Bắt đầu với việc lấy tất cả các tin đang mở
    jobs = JobPosting.objects.filter(status=JobPosting.Status.OPEN).select_related('tournament', 'role_required')

    # Áp dụng bộ lọc nếu có
    if region_filter:
        jobs = jobs.filter(tournament__region=region_filter)

    context = {
        'jobs': jobs,
        'all_regions': Tournament.Region.choices, # Gửi danh sách khu vực ra template
        'current_region': region_filter,           # Gửi khu vực đang được chọn
    }
    return render(request, 'tournaments/job_market.html', context)

def job_detail_view(request, pk):
    job = get_object_or_404(JobPosting, pk=pk)
    user_has_applied = False
    is_organizer = False

    if request.user.is_authenticated:
        user_has_applied = JobApplication.objects.filter(job=job, applicant=request.user).exists()
        is_organizer = job.tournament.organization and job.tournament.organization.members.filter(pk=request.user.pk).exists()

    if request.method == 'POST' and request.user.is_authenticated and not user_has_applied and not is_organizer:
        form = JobApplicationForm(request.POST)
        if form.is_valid():
            application = form.save(commit=False)
            application.job = job
            application.applicant = request.user
            application.save()
            messages.success(request, "Bạn đã ứng tuyển thành công!")
            
            # Gửi thông báo trên web và email cho BTC
            organization = job.tournament.organization
            if organization:
                btc_members = organization.members.all()
                applicant_name = request.user.get_full_name() or request.user.username
                notification_title = f"Có đơn ứng tuyển mới cho '{job.title}'"
                notification_message = f"{applicant_name} vừa ứng tuyển vào vị trí của bạn trong giải đấu '{job.tournament.name}'."
                notification_url = request.build_absolute_uri(
                    reverse('organizations:manage_jobs', kwargs={'tournament_pk': job.tournament.pk})
                )
                
                # Gửi thông báo trên web (đã có)
                notifications_to_create = [
                    Notification(user=member, title=notification_title, message=notification_message, related_url=notification_url)
                    for member in btc_members
                ]
                if notifications_to_create:
                    Notification.objects.bulk_create(notifications_to_create)

                # === BẮT ĐẦU NÂNG CẤP: GỬI EMAIL ===
                btc_emails = [member.email for member in btc_members if member.email]
                if btc_emails:
                    send_notification_email(
                        subject=f"[DBP Sports] {notification_title}",
                        template_name='organizations/emails/new_job_application.html',
                        context={
                            'job': job,
                            'applicant': request.user,
                            'application': application
                        },
                        recipient_list=btc_emails,
                        request=request
                    )
                # === KẾT THÚC NÂNG CẤP ===

            return redirect('job_detail', pk=pk)
    else:
        form = JobApplicationForm()

    context = {
        'job': job,
        'form': form,
        'user_has_applied': user_has_applied,
        'is_organizer': is_organizer,
    }
    return render(request, 'tournaments/job_detail.html', context)    

# === backend Note BLV ===
@login_required
@never_cache
def commentator_notes_view(request, match_pk):
    match = get_object_or_404(Match.objects.select_related('team1', 'team2'), pk=match_pk)
    
    # Kiểm tra quyền: Chỉ BLV hoặc người có quyền control trận đấu mới được vào
    if not user_can_control_match(request.user, match):
        return HttpResponseForbidden("Bạn không có quyền truy cập trang này.")

    # Tìm hoặc tạo ghi chú của BLV cho trận này
    note_instance, created = MatchNote.objects.get_or_create(
        match=match,
        author=request.user,
        note_type=MatchNote.NoteType.COMMENTATOR,
        defaults={}
    )

    if request.method == 'POST':
        form = CommentatorNoteForm(request.POST, instance=note_instance)
        if form.is_valid():
            form.save()
            messages.success(request, "Đã lưu ghi chú thành công!")
            return redirect('commentator_notes', match_pk=match.pk)
    else:
        form = CommentatorNoteForm(instance=note_instance)
    
    # Lấy ghi chú từ đội trưởng của 2 đội (nếu có)
    captain_note_team1 = MatchNote.objects.filter(match=match, team=match.team1, note_type=MatchNote.NoteType.CAPTAIN).first()
    captain_note_team2 = MatchNote.objects.filter(match=match, team=match.team2, note_type=MatchNote.NoteType.CAPTAIN).first()

    context = {
        'match': match,
        'form': form,
        'captain_note_team1': captain_note_team1,
        'captain_note_team2': captain_note_team2,
    }
    return render(request, 'tournaments/commentator_notes.html', context)    

# === Note cho đội trưởng ===
@login_required
@never_cache
def captain_note_view(request, match_pk, team_pk):
    match = get_object_or_404(Match, pk=match_pk)
    team = get_object_or_404(Team, pk=team_pk)

    # Kiểm tra quyền: Chỉ đội trưởng của đội đó mới được truy cập
    if request.user != team.captain:
        return HttpResponseForbidden("Bạn không phải đội trưởng của đội này.")

    # Tìm hoặc tạo ghi chú của đội trưởng cho trận này
    note_instance, created = MatchNote.objects.get_or_create(
        match=match,
        author=request.user,
        team=team,
        note_type=MatchNote.NoteType.CAPTAIN,
        defaults={}
    )

    if request.method == 'POST':
        form = CaptainNoteForm(request.POST, instance=note_instance)
        if form.is_valid():
            form.save()
            messages.success(request, "Đã gửi ghi chú cho Bình luận viên thành công!")
            return redirect('manage_lineup', match_pk=match.pk, team_pk=team.pk)
    else:
        form = CaptainNoteForm(instance=note_instance)

    context = {
        'match': match,
        'team': team,
        'form': form,
    }
    return render(request, 'tournaments/captain_note.html', context)    


@login_required
def claim_player_profile(request, pk):
    player_to_claim = get_object_or_404(Player, pk=pk)

    # Kiểm tra xem tài khoản này đã có hồ sơ cầu thủ chưa
    if hasattr(request.user, 'player_profile') and request.user.player_profile is not None:
        messages.error(request, "Tài khoản của bạn đã được liên kết với một hồ sơ cầu thủ khác.")
        return redirect('player_detail', pk=pk)

    # Kiểm tra xem hồ sơ này đã bị ai nhận chưa
    if player_to_claim.user is not None:
        messages.error(request, "Hồ sơ này đã được một tài khoản khác liên kết.")
        return redirect('player_detail', pk=pk)

    # Nếu mọi thứ hợp lệ, tiến hành liên kết
    player_to_claim.user = request.user
    player_to_claim.save()
    messages.success(request, f"Bạn đã liên kết thành công với hồ sơ cầu thủ {player_to_claim.full_name}.")
    return redirect('player_detail', pk=pk)    