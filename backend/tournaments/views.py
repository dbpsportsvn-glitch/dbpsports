# Python Standard Library
import json
import random
from collections import defaultdict
from datetime import datetime, time, timedelta
from itertools import combinations
from django.core import serializers
from django.db import transaction

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

# Local Application Imports
from organizations.models import Organization

from .forms import (CommentForm, GalleryURLForm, PaymentProofForm,
                    PlayerCreationForm, ScheduleGenerationForm,
                    TeamCreationForm)
from .models import (Announcement, Card, Goal, Group, HomeBanner, Lineup, Match,
                     Player, Team, Tournament, TournamentPhoto, MAX_STARTERS, Notification)
from .utils import send_notification_email, send_schedule_notification


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
@never_cache
def team_detail(request, pk):
    team = get_object_or_404(Team, pk=pk)
    achievements = team.achievements.select_related('tournament').all()

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
        'achievements': achievements,
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
    # Lấy thông tin trận đấu và các đội liên quan để tối ưu
    match = get_object_or_404(
        Match.objects.select_related('tournament', 'team1', 'team2'),
        pk=pk
    )

    # --- PHẦN LẤY DỮ LIỆU ĐỘI HÌNH VÀ THỐNG KÊ (ĐÃ NÂNG CẤP) ---

    # Lấy danh sách cầu thủ của cả 2 đội trong trận này
    players_in_match = Player.objects.filter(team__in=[match.team1, match.team2])

    # Lấy tất cả các sự kiện (bàn thắng, thẻ phạt) của trận đấu này
    all_goals_in_match = Goal.objects.filter(match=match).select_related('player', 'team')
    all_cards_in_match = Card.objects.filter(match=match).select_related('player', 'team')

    # Hàm trợ giúp để xử lý thông tin cho từng đội
    def get_team_lineup_with_stats(team):
        lineup_entries = Lineup.objects.filter(match=match, team=team).select_related('player')
        
        lineup_with_stats = []
        for entry in lineup_entries:
            player = entry.player
            
            # Đếm số bàn thắng của cầu thủ trong trận này
            goals_in_this_match = all_goals_in_match.filter(player=player, is_own_goal=False).count()
            
            # Đếm số thẻ của cầu thủ trong trận này
            yellow_cards_in_this_match = all_cards_in_match.filter(player=player, card_type='YELLOW').count()
            red_cards_in_this_match = all_cards_in_match.filter(player=player, card_type='RED').count()
            
            lineup_with_stats.append({
                'player': player,
                'status': entry.get_status_display(), # Lấy tên trạng thái (Đá chính/Dự bị)
                'goals': goals_in_this_match,
                'yellow_cards': yellow_cards_in_this_match,
                'red_cards': red_cards_in_this_match,
            })
        return lineup_with_stats

    team1_lineup = get_team_lineup_with_stats(match.team1)
    team2_lineup = get_team_lineup_with_stats(match.team2)
    
    # Lấy danh sách các sự kiện đã sắp xếp theo thời gian để hiển thị
    events = sorted(
        list(all_goals_in_match) + list(all_cards_in_match),
        key=lambda x: x.minute or 0
    )

    # Kiểm tra xem người dùng hiện tại có phải đội trưởng của 1 trong 2 đội không
    captain_team = None
    if request.user.is_authenticated:
        if match.team1.captain == request.user:
            captain_team = match.team1
        elif match.team2.captain == request.user:
            captain_team = match.team2

    context = {
        'match': match,
        'team1_lineup': team1_lineup,
        'team2_lineup': team2_lineup,
        'events': events, # Gửi danh sách sự kiện ra template
        'captain_team': captain_team,
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