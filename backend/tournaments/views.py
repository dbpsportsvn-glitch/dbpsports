# backend/tournaments/views.py

# Standard library
import json
import random
import os
from collections import defaultdict
from datetime import date, datetime, time, timedelta
from itertools import combinations
from PIL import Image
from io import BytesIO
from django.core.files.base import ContentFile

def compress_banner_image(image_field):
    """
    Nén ảnh banner để giảm kích thước file
    Target: giảm xuống dưới 2MB với chất lượng 85%
    """
    if not image_field or not hasattr(image_field, 'read'):
        return image_field
    
    try:
        # Reset file pointer to beginning
        image_field.seek(0)
        
        # Mở ảnh với PIL
        img = Image.open(image_field)
        
        # Chuyển đổi sang RGB nếu cần (cho PNG có alpha channel)
        if img.mode in ('RGBA', 'P'):
            img = img.convert('RGB')
        
        # Tính toán kích thước mới để đảm bảo file < 2MB
        # Giả sử 1 pixel RGB = 3 bytes, với quality 85% và compression
        # Target: 2MB = 2,097,152 bytes
        target_size = 2 * 1024 * 1024  # 2MB
        current_pixels = img.width * img.height
        
        # Nếu ảnh quá lớn, resize để giảm kích thước
        if current_pixels > 1920 * 1080:  # Nếu lớn hơn Full HD
            # Tính tỷ lệ để giảm xuống khoảng 1920x1080
            ratio = min(1920 / img.width, 1080 / img.height)
            new_width = int(img.width * ratio)
            new_height = int(img.height * ratio)
            img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        # Nén ảnh với quality 85%
        buffer = BytesIO()
        img.save(buffer, format='JPEG', quality=85, optimize=True)
        
        # Kiểm tra kích thước sau khi nén
        compressed_size = buffer.tell()
        
        # Nếu vẫn quá lớn, giảm quality xuống 75%
        if compressed_size > target_size:
            buffer = BytesIO()
            img.save(buffer, format='JPEG', quality=75, optimize=True)
            compressed_size = buffer.tell()
        
        # Nếu vẫn quá lớn, giảm quality xuống 65%
        if compressed_size > target_size:
            buffer = BytesIO()
            img.save(buffer, format='JPEG', quality=65, optimize=True)
        
        # Tạo file mới với tên gốc
        file_name = os.path.basename(image_field.name)
        if not file_name.lower().endswith('.jpg'):
            file_name = os.path.splitext(file_name)[0] + '.jpg'
        
        new_image = ContentFile(buffer.getvalue(), name=file_name)
        return new_image
        
    except Exception as e:
        # Nếu có lỗi trong quá trình nén, trả về file gốc
        print(f"Error compressing image: {e}")
        return image_field

# Django
from django.conf import settings
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core import serializers
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.db.models import Avg, Count, F, Prefetch, Q, Sum, Value
from django.db import models
from django.http import HttpResponseForbidden, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_POST

# Project apps
from organizations.forms import (
    CardForm,
    GoalForm,
    JobApplicationForm,
    MatchMediaUpdateForm,
    MatchUpdateForm,
    SubstitutionForm,
)
from organizations.models import JobApplication, JobPosting, Organization
from organizations.views import user_can_control_match, user_can_upload_gallery
from services.weather import get_weather_for_match
from sponsors.models import Testimonial

# Current app
from .forms import (
    BudgetQuickAddForm,
    CaptainNoteForm,
    CommentatorNoteForm,
    CommentForm,
    ExpenseItemForm,
    GalleryURLForm,
    PaymentProofForm,
    PlayerCreationForm,
    PlayerTransferForm,
    RevenueItemForm,
    TournamentBudgetForm,
    ScheduleGenerationForm,
    TeamCreationForm,
)
from .models import (
    Announcement,
    BudgetHistory,
    Card,
    CoachRecruitment,
    ExpenseItem,
    Goal,
    Group,
    HomeBanner,
    Lineup,
    Match,
    MatchEvent,
    MatchNote,
    MAX_STARTERS,
    Notification,
    Player,
    PlayerTransfer,
    RevenueItem,
    ScoutingList,
    SponsorClick,
    Sponsorship,
    Substitution,
    Team,
    TeamAchievement,
    TeamRegistration,
    TeamVoteRecord,
    Tournament,
    TournamentBudget,
    TournamentPhoto,
    TournamentStaff,
    VoteRecord,
    SponsorshipPackage,
)
from shop.models import Cart
from .utils import (
    get_current_vote_value,
    send_notification_email,
    send_schedule_notification,
)

#==================================

def home(request):
    from django.db.models import Count
    
    # Lấy banner
    banners = HomeBanner.objects.filter(is_active=True).order_by('order', 'id')
    
    # Giải đấu nổi bật - Kết hợp giải Super Admin + giải nhiều followers
    # 1. Lấy giải của Super Admin trước (không có organization)
    super_admin_tournaments = list(Tournament.objects.filter(
        organization__isnull=True
    ).exclude(status='FINISHED').annotate(
        followers_count=Count('followers')
    ).order_by('-followers_count', '-start_date'))
    
    # 2. Tính số giải còn thiếu để đủ 4 giải
    remaining_count = 4 - len(super_admin_tournaments)
    
    # 3. Nếu còn thiếu, lấy thêm giải có nhiều followers nhất từ BTC khác
    featured_tournaments = super_admin_tournaments
    if remaining_count > 0:
        # Lấy ID các giải đã có để loại trừ
        existing_ids = [t.id for t in super_admin_tournaments]
        
        # Lấy thêm giải có nhiều followers từ BTC khác
        additional_tournaments = list(Tournament.objects.exclude(
            status='FINISHED'
        ).exclude(
            id__in=existing_ids
        ).annotate(
            followers_count=Count('followers')
        ).filter(followers_count__gt=0).order_by('-followers_count')[:remaining_count])
        
        featured_tournaments.extend(additional_tournaments)
    
    # Giải nhiều người theo dõi nhất (loại trừ các giải đã ở featured)
    featured_ids = [t.id for t in featured_tournaments]
    most_followed_tournaments = Tournament.objects.exclude(
        status='FINISHED'
    ).exclude(
        id__in=featured_ids
    ).annotate(
        followers_count=Count('followers')
    ).filter(followers_count__gt=0).order_by('-followers_count')[:6]
    
    # Tất cả các giải đang hoạt động
    all_active_tournaments = Tournament.objects.exclude(
        status='FINISHED'
    ).order_by('-start_date')

    return render(
        request,
        'tournaments/home.html',
        {
            'banners': banners,
            'featured_tournaments': featured_tournaments,
            'most_followed_tournaments': most_followed_tournaments,
            'all_active_tournaments': all_active_tournaments,
        }
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


@never_cache
def tournament_detail(request, pk):
    tournament = get_object_or_404(
        Tournament.objects.prefetch_related(
            Prefetch('groups', queryset=Group.objects.order_by('name').prefetch_related(
                Prefetch('registrations__team', queryset=Team.objects.select_related('captain'))
            )),
            'photos',
            # Sửa dòng này để tối ưu hơn
            Prefetch('sponsorships', queryset=Sponsorship.objects.filter(is_active=True).select_related('package', 'sponsor__sponsor_profile'))
        ),
        pk=pk
    )

    is_organizer = False
    if request.user.is_authenticated and tournament.organization:
        if tournament.organization.members.filter(pk=request.user.pk).exists():
            is_organizer = True

    all_matches = tournament.matches.select_related('team1', 'team2').order_by('match_time')

    # Lấy danh sách các trận đấu có thư viện ảnh riêng
    matches_with_galleries = all_matches.filter(
        Q(cover_photo__isnull=False) | Q(gallery_url__isnull=False)
    ).distinct()

    # Lọc trận theo thể thức
    group_matches = all_matches.filter(match_round=('LEAGUE' if tournament.format == Tournament.Format.LEAGUE else 'GROUP'))
    # SỬA LỖI: Truy vấn các đội chưa được xếp bảng thông qua TeamRegistration
    unassigned_teams = Team.objects.filter(registrations__tournament=tournament, registrations__payment_status='PAID', registrations__group__isnull=True)


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

    # Phần tính toán bảng xếp hạng
    standings_data = defaultdict(list)
    groups_with_teams = list(tournament.groups.all())

    team_stats = {}
    # SỬA LỖI: Lấy các đội đã đăng ký và được duyệt
    registered_teams = Team.objects.filter(registrations__tournament=tournament, registrations__payment_status='PAID').prefetch_related('registrations')
    for team in registered_teams:
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

    if tournament.format == Tournament.Format.LEAGUE:
        # League: một bảng duy nhất 'LEAGUE'
        league_team_ids = tournament.registrations.filter(payment_status='PAID').values_list('team_id', flat=True)
        league_standings = [team_stats[tid] for tid in league_team_ids if tid in team_stats]
        for stats in league_standings:
            stats['gd'] = stats['gf'] - stats['ga']
        league_standings.sort(key=lambda x: (x['points'], x['gd'], x['gf']), reverse=True)
        standings_data['LEAGUE'] = league_standings
    else:
        for group in groups_with_teams:
            # SỬA LỖI: Lấy teams trong group thông qua registrations
            teams_in_group_ids = TeamRegistration.objects.filter(group=group).values_list('team_id', flat=True)
            group_standings = [team_stats[team_id] for team_id in teams_in_group_ids if team_id in team_stats]

            for stats in group_standings:
                stats['gd'] = stats['gf'] - stats['ga']

            group_standings.sort(key=lambda x: (x['points'], x['gd'], x['gf']), reverse=True)
            standings_data[group.id] = group_standings


    # SỬA LỖI: Thay thế tournament.teams.all()
    all_teams_in_tournament = Team.objects.filter(registrations__tournament=tournament)
    total_teams = all_teams_in_tournament.count()
    total_players = Player.objects.filter(team__in=all_teams_in_tournament).count()
    finished_matches = all_matches.filter(team1_score__isnull=False)
    finished_matches_count = finished_matches.count()

    total_goals_obj = Goal.objects.filter(match__in=finished_matches)
    total_own_goals = total_goals_obj.filter(is_own_goal=True).count()
    total_normal_goals = total_goals_obj.filter(is_own_goal=False).count()

    total_cards_obj = Card.objects.filter(match__in=finished_matches)
    total_yellow_cards = total_cards_obj.filter(card_type='YELLOW').count()
    total_red_cards = total_cards_obj.filter(card_type='RED').count()

    avg_goals_per_match = round(total_normal_goals / finished_matches_count, 2) if finished_matches_count > 0 else 0

    top_scorers = Player.objects.filter(
        goals__match__tournament=tournament,
        goals__is_own_goal=False
    ).annotate(
        goal_count=Count('goals')
    ).select_related('team').order_by('-goal_count')[:5]

    hattricks = Player.objects.filter(
        goals__match__tournament=tournament,
        goals__is_own_goal=False
    ).values('full_name', 'team__name', 'goals__match_id').annotate(
        goals_in_match=Count('id')
    ).filter(goals_in_match__gte=3).count()

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

    team_goal_stats.sort(key=lambda x: (x['gd'], x['gf']), reverse=True)
    team_card_stats.sort(key=lambda x: (x['red_cards'], x['yellow_cards']), reverse=True)

    # SỬA LỖI: Kiểm tra đội đã thanh toán qua TeamRegistration
    has_paid_teams = tournament.registrations.filter(payment_status='PAID').exists()

    registerable_teams = []
    if request.user.is_authenticated:
        # Lấy các đội mà user làm đội trưởng và chưa đăng ký giải này
        registered_team_ids = tournament.registrations.values_list('team_id', flat=True)
        registerable_teams = Team.objects.filter(captain=request.user).exclude(id__in=registered_team_ids)

    # === LOGIC CHO NHÀ TÀI TRỢ  ===
    # Lấy danh sách nhà tài trợ đã được prefetch ở trên
    sponsorships_list = list(tournament.sponsorships.all())

    # Tính toán rating trung bình cho từng nhà tài trợ
    for sponsorship in sponsorships_list:
        if sponsorship.sponsor and hasattr(sponsorship.sponsor, 'sponsor_profile'):
            # Tính rating trung bình và gán trực tiếp vào đối tượng sponsorship
            avg_rating = Testimonial.objects.filter(
                sponsor_profile=sponsorship.sponsor.sponsor_profile
            ).aggregate(avg_rating=Avg('rating'))['avg_rating']
            sponsorship.avg_rating = avg_rating if avg_rating is not None else 0
        else:
            sponsorship.avg_rating = 0 # Mặc định là 0 nếu không có profile

    # Sắp xếp danh sách nhà tài trợ bằng Python
    # Ưu tiên 1: Thứ tự của gói (order nhỏ hơn lên trước)
    # Ưu tiên 2: Điểm đánh giá trung bình (avg_rating cao hơn lên trước)
    sorted_sponsorships = sorted(
        sponsorships_list,
        key=lambda s: (s.package.order, -s.avg_rating),
    )
    # === KẾT THÚC PHẦN LOGIC MỚI ===
    context = {
        'tournament': tournament,
        'is_organizer': is_organizer,
        'registerable_teams': registerable_teams,
        'group_matches': group_matches,
        'knockout_matches': all_knockout_matches,
        'knockout_data': knockout_data,
        'now': timezone.now(),
        'unassigned_teams': unassigned_teams,
        'standings_data': standings_data,
        'has_paid_teams': has_paid_teams,

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
        'sorted_sponsorships': sorted_sponsorships,
    }
    return render(request, 'tournaments/tournament_detail.html', context)



@login_required
@never_cache
def team_detail(request, pk):
    team = get_object_or_404(Team, pk=pk)
    registrations = TeamRegistration.objects.filter(team=team).select_related('tournament').order_by('-tournament__start_date')
    
    player_form = PlayerCreationForm()
    active_tab = ''
    can_manage_players = not registrations.exists() or registrations.filter(payment_status='PAID').exists()

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'create_new_player':
            active_tab = 'new'
            if not can_manage_players:
                messages.error(request, "Bạn cần hoàn tất lệ phí cho ít nhất một giải đấu để thêm cầu thủ.")
            elif request.user != team.captain:
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
                        for field, errors in e.message_dict.items():
                            player_form.add_error(field if field != '__all__' else None, errors[0])
                        messages.error(request, 'Thêm cầu thủ thất bại, vui lòng kiểm tra lại.')

    context = {
        'team': team,
        'registrations': registrations,
        'can_manage_players': can_manage_players,
        'player_form': player_form,
        'achievements': team.achievements.select_related('tournament').all(),
        'active_tab': active_tab,
    }
    return render(request, 'tournaments/team_detail.html', context)


@login_required
@never_cache
def create_team(request, tournament_pk):
    tournament = get_object_or_404(Tournament, pk=tournament_pk)
    existing_teams = Team.objects.filter(captain=request.user).exclude(registrations__tournament=tournament)
    
    # Kiểm tra giới hạn chỉ khi tạo đội mới (POST request)
    TEAM_LIMIT = 3
    if request.method == 'POST' and Team.objects.filter(captain=request.user).count() >= TEAM_LIMIT:
        messages.error(request, f"Bạn đã đạt đến giới hạn tối đa ({TEAM_LIMIT}) đội bóng được phép tạo.")
        return redirect('tournament_detail', pk=tournament_pk)

    if request.method == 'POST':
        form = TeamCreationForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            try:
                with transaction.atomic():
                    team = form.save(commit=False)
                    team.captain = request.user
                    team.save()
                    registration = TeamRegistration.objects.create(team=team, tournament=tournament)
                    
                    # Gửi email thông báo cho admin và BTC
                    admin_emails = getattr(settings, 'ADMIN_EMAILS', [settings.ADMIN_EMAIL])
                    btc_emails = []
                    
                    # Lấy email của BTC members
                    if tournament.organization:
                        btc_emails = [member.email for member in tournament.organization.members.all() if member.email]
                    
                    # Gộp danh sách email và loại bỏ trùng lặp
                    recipient_list = list(set(admin_emails + btc_emails))
                    recipient_list = [email for email in recipient_list if email and email != 'admin@example.com']
                    
                    if recipient_list:
                        email_sent = send_notification_email(
                            subject=f"Đội mới đăng ký: {team.name} - {tournament.name}",
                            template_name='tournaments/emails/new_team_registration.html',
                            context={'team': team, 'tournament': tournament, 'registration': registration},
                            recipient_list=recipient_list
                        )
                
                messages.success(request, f"Đã tạo và đăng ký thành công đội '{team.name}'!")
                return redirect('team_detail', pk=team.pk)
            except IntegrityError:
                 form.add_error('name', "Bạn đã có một đội với tên này. Vui lòng chọn một tên khác.")
    else:
        form = TeamCreationForm(user=request.user)

    context = { 'form': form, 'tournament': tournament, 'existing_teams': existing_teams }
    return render(request, 'tournaments/register_options.html', context)

@login_required
@never_cache
def delete_player(request, pk):
    player = get_object_or_404(Player, pk=pk)
    team = player.team

    if request.user != team.captain:
        return HttpResponseForbidden("Bạn không có quyền thực hiện hành động này.")

    if request.method == 'POST':
        player.delete()
        messages.success(request, f"Đã xóa cầu thủ {player.full_name} khỏi đội.")
        return redirect('team_detail', pk=team.pk)

    context = {'player': player, 'team': team}
    return render(request, 'tournaments/player_confirm_delete.html', context)

@login_required
def delete_team(request, pk):
    team = get_object_or_404(Team, pk=pk)

    # Kiểm tra quyền sở hữu
    if request.user != team.captain:
        return HttpResponseForbidden("Bạn không có quyền xóa đội bóng này.")

    # Ngăn xóa đội nếu đang tham gia giải
    if team.registrations.exists():
        messages.error(request, f"Không thể xóa đội '{team.name}' vì đội đang được đăng ký tham gia ít nhất một giải đấu. Vui lòng liên hệ BTC để gỡ đội khỏi các giải trước khi xóa.")
        return redirect('team_detail', pk=team.pk)

    if request.method == 'POST':
        team_name = team.name
        team.delete()
        messages.success(request, f"Đã xóa thành công đội bóng '{team_name}'.")
        return redirect('dashboard') # Chuyển về trang cá nhân sau khi xóa

    context = {'team': team}
    return render(request, 'tournaments/team_confirm_delete.html', context)

@login_required
@never_cache
def update_player(request, pk):
    player = get_object_or_404(Player, pk=pk)
    team = player.team

    if request.user != team.captain:
        return redirect('home')

    can_edit = player.votes < 3 and player.edit_count < 3
    if not can_edit:
        if player.votes >= 3:
            messages.error(request, f"Không thể chỉnh sửa. Cầu thủ {player.full_name} đã có 3 phiếu bầu trở lên.")
        else:
            messages.error(request, f"Không thể chỉnh sửa. Đã hết số lần cho phép (3 lần) cho cầu thủ {player.full_name}.")
        return redirect('team_detail', pk=team.pk)

    if request.method == 'POST':
        form = PlayerCreationForm(request.POST, request.FILES, instance=player)
        if form.is_valid():
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
        'remaining_edits': 3 - player.edit_count,
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

@never_cache
def match_detail(request, pk):
    match = get_object_or_404(
        Match.objects.select_related('tournament', 'team1', 'team2'),
        pk=pk
    )

    weather_data = None
    if match.match_time and timezone.now() < match.match_time < timezone.now() + timedelta(days=14):
        weather_data = get_weather_for_match(match.location, match.match_time, match.tournament.region)

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
        'can_control_match': can_control_match,
    }
    return render(request, 'tournaments/match_detail.html', context)


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
        "existing_lineup_json": json.dumps(existing_lineup),
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
    registration = get_object_or_404(TeamRegistration, pk=pk)
    team = registration.team
    tournament = registration.tournament

    if request.user != team.captain:
        return redirect('home')

    # Lấy cart của user
    cart, created = Cart.objects.get_or_create(user=request.user)
    
    # Tính toán giảm giá
    cart_total = cart.total_price
    discount_amount = tournament.calculate_shop_discount(cart.items.all())
    final_fee = tournament.get_final_registration_fee(cart.items.all())

    if request.method == 'POST':
        form = PaymentProofForm(request.POST, request.FILES, instance=registration)
        if form.is_valid():
            reg = form.save(commit=False)
            reg.payment_status = 'PENDING'
            
            # Xử lý tích hợp shop
            use_shop_discount = form.cleaned_data.get('use_shop_discount', False)
            if use_shop_discount and tournament.shop_discount_percentage > 0:
                if cart_total > 0:
                    messages.info(request, f'Bạn đã sử dụng giảm giá từ shop ({tournament.shop_discount_percentage}%). Đơn hàng shop sẽ được xử lý riêng.')
                else:
                    messages.warning(request, 'Giỏ hàng của bạn đang trống. Vui lòng thêm sản phẩm vào giỏ hàng để được giảm giá.')
            
            reg.save()

            send_notification_email(
                subject=f"Xác nhận thanh toán mới từ đội {team.name}",
                template_name='tournaments/emails/new_payment_proof.html',
                context={'team': team, 'tournament': tournament, 'use_shop_discount': use_shop_discount, 'cart_total': cart_total},
                recipient_list=[settings.ADMIN_EMAIL]
            )

            if team.captain.email:
                send_notification_email(
                    subject=f"Đã nhận được hóa đơn thanh toán của đội {team.name}",
                    template_name='tournaments/emails/payment_pending_confirmation.html',
                    context={'team': team, 'tournament': tournament, 'use_shop_discount': use_shop_discount, 'cart_total': cart_total},
                    recipient_list=[team.captain.email]
                )

            messages.success(request, 'Đã tải lên hóa đơn thành công! Vui lòng chờ Ban tổ chức xác nhận.')

            return redirect('team_detail', pk=team.pk)
    else:
        form = PaymentProofForm(instance=registration)

    context = {
        'form': form,
        'team': team,
        'registration': registration,
        'cart': cart,
        'cart_total': cart_total,
        'discount_amount': discount_amount,
        'final_fee': final_fee,
    }
    return render(request, 'tournaments/payment_proof.html', context)


def archive_view(request):
    region_filter = request.GET.get('region', '')
    org_filter = request.GET.get('org', '')
    tournaments_list = Tournament.objects.filter(status='FINISHED').select_related('organization').order_by('-start_date')
    if region_filter:
        tournaments_list = tournaments_list.filter(region=region_filter)
    if org_filter:
        tournaments_list = tournaments_list.filter(organization__id=org_filter)
    finished_orgs_ids = Tournament.objects.filter(status='FINISHED').values_list('organization__id', flat=True).distinct()
    all_organizations = Organization.objects.filter(id__in=finished_orgs_ids).order_by('name')

    context = {
        'tournaments': tournaments_list,
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
        TeamRegistration.objects.filter(team__captain=request.user).values_list('tournament_id', flat=True)
    )
    tournament_ids_as_player = set(
        Player.objects.filter(user=request.user).values_list('team__registrations__tournament_id', flat=True)
    )
    tournament_ids_as_follower = set(
        request.user.followed_tournaments.values_list('id', flat=True)
    )

    all_relevant_ids = tournament_ids_as_captain.union(tournament_ids_as_player, tournament_ids_as_follower)

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
    if unread_announcements.exists():
        request.user.read_announcements.add(*unread_announcements)

    context = {
        'announcements': announcements
    }
    return render(request, 'tournaments/announcement_dashboard.html', context)

def faq_view(request):
    return render(request, 'tournaments/faq.html')

@login_required
@never_cache
def draw_groups_view(request, tournament_pk):
    tournament = get_object_or_404(Tournament, pk=tournament_pk)

    is_organizer = tournament.organization and tournament.organization.members.filter(pk=request.user.pk).exists()
    if not request.user.is_staff and not is_organizer:
        return HttpResponseForbidden("Bạn không có quyền truy cập trang này.")

    if tournament.status == 'REGISTRATION_OPEN':
        messages.error(request, "Không thể bốc thăm khi giải đấu vẫn đang trong giai đoạn đăng ký.")
        return redirect('tournament_detail', pk=tournament.pk)

    if request.method == 'POST':
        try:
            results_str = request.POST.get('draw_results')
            if not results_str:
                raise ValueError("Không nhận được dữ liệu bốc thăm.")

            group_assignments = json.loads(results_str)

            with transaction.atomic():
                Match.objects.filter(tournament=tournament, match_round='GROUP').delete()
                # SỬA LỖI: Cập nhật group trên TeamRegistration
                TeamRegistration.objects.filter(tournament=tournament).update(group=None)

                for group_id_str, team_ids in group_assignments.items():
                    group_id = int(group_id_str)
                    group = get_object_or_404(Group, pk=group_id, tournament=tournament)
                    # SỬA LỖI: Cập nhật group trên TeamRegistration
                    TeamRegistration.objects.filter(tournament=tournament, team_id__in=team_ids).update(group=group)

            messages.success(request, "Kết quả bốc thăm mới đã được lưu thành công! Lịch thi đấu vòng bảng cũ đã được xóa.")
            send_schedule_notification(
                tournament,
                Notification.NotificationType.DRAW_COMPLETE,
                f"Giải đấu '{tournament.name}' đã có kết quả bốc thăm",
                "Kết quả bốc thăm chia bảng đã có. Hãy vào xem chi tiết.",
                'tournament_detail'
            )
            return redirect(reverse('tournament_detail', kwargs={'pk': tournament.pk}) + '?tab=teams#teams')

        except Exception as e:
            messages.error(request, f"An error occurred: {e}")
            return redirect('draw_groups', tournament_pk=tournament.pk)

    # SỬA LỖI: Truy vấn các đội chưa được xếp bảng
    unassigned_teams = Team.objects.filter(registrations__tournament=tournament, registrations__payment_status='PAID', registrations__group__isnull=True)
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

    # Điều kiện tùy theo thể thức
    if tournament.format == Tournament.Format.CUP:
        if not tournament.groups.exists() or tournament.registrations.filter(payment_status='PAID', group__isnull=True).exists() or not tournament.registrations.filter(payment_status='PAID').exists():
            messages.error(request, "Không thể xếp lịch. Cần tạo bảng, có đội đã đăng ký và tất cả các đội phải được bốc thăm vào bảng.")
            return redirect('tournament_detail', pk=tournament.pk)
        if tournament.matches.filter(match_round='GROUP').exists():
            messages.warning(request, "Lịch thi đấu vòng bảng đã được tạo cho giải này.")
            return redirect('tournament_detail', pk=tournament.pk)
    else:
        # LEAGUE: chỉ cần có đội đã đăng ký và đã thanh toán
        if not tournament.registrations.filter(payment_status='PAID').exists():
            messages.error(request, "Không thể xếp lịch. Chưa có đội nào đã đăng ký và thanh toán.")
            return redirect('tournament_detail', pk=tournament.pk)
        if tournament.matches.filter(match_round='LEAGUE').exists():
            messages.warning(request, "Lịch thi đấu League đã được tạo cho giải này.")
            return redirect('tournament_detail', pk=tournament.pk)

    if request.method == 'POST':
        if 'confirm_schedule' in request.POST:
            schedule_preview_json = request.session.get('schedule_preview_json')
            if not schedule_preview_json:
                messages.error(request, "Không tìm thấy lịch thi đấu xem trước. Vui lòng tạo lại.")
                return redirect('generate_schedule', tournament_pk=tournament.pk)

            try:
                with transaction.atomic():
                    # Xóa lịch cũ theo thể thức
                    round_code = 'GROUP' if tournament.format == Tournament.Format.CUP else 'LEAGUE'
                    Match.objects.filter(tournament=tournament, match_round=round_code).delete()
                    schedule_to_save = json.loads(schedule_preview_json)
                    for match_data in schedule_to_save:
                        Match.objects.create(
                            tournament=tournament,
                            team1_id=match_data['team1_id'],
                            team2_id=match_data['team2_id'],
                            match_time=datetime.fromisoformat(match_data['match_time']),
                            location=match_data['location'],
                            match_round=('GROUP' if tournament.format == Tournament.Format.CUP else 'LEAGUE'),
                            round_number=match_data.get('round_number'),
                            leg=match_data.get('leg')
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
                # Nguồn đội theo thể thức
                if tournament.format == Tournament.Format.CUP:
                    groups = sorted(list(tournament.groups.prefetch_related('registrations__team').all()), key=lambda g: g.name)
                    group_to_teams = {g: [reg.team for reg in g.registrations.all()] for g in groups}
                else:
                    # LEAGUE: tất cả đội đã thanh toán, một bảng giả 'League'
                    league_teams = [reg.team for reg in tournament.registrations.select_related('team').filter(payment_status='PAID')]
                    groups = ['LEAGUE']
                    group_to_teams = {'LEAGUE': league_teams}

                for group in groups:
                    teams_in_group = group_to_teams[group]
                    base_pairings = list(combinations(teams_in_group, 2))
                    random.shuffle(base_pairings)

                    # === THÊM HỖ TRỢ VÒNG TRÒN 2 LƯỢT: nhân đôi cặp và đảo chủ/khách ===
                    legs = int(data.get('round_robin_legs') or 1)
                    group_pairings = []
                    for pair in base_pairings:
                        team1, team2 = pair
                        # Lượt đi
                        group_pairings.append((team1, team2, 1))
                        if legs == 2:
                            # Lượt về (đảo chủ/khách)
                            group_pairings.append((team2, team1, 2))

                    # Trộn thứ tự để phân tán các lượt
                    random.shuffle(group_pairings)
                    display_name = group.name if hasattr(group, 'name') else str(group)
                    all_pairings_by_group[group] = [{'pair': (p[0], p[1]), 'leg': p[2], 'group_name': display_name} for p in group_pairings]

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

                                    group_name = group.name if hasattr(group, 'name') else str(group)
                                    group_limit = group_limits.get(group_name)
                                    group_id = group.id if hasattr(group, 'id') else str(group)
                                    if group_limit is not None and group_matches_this_week[group_id] >= group_limit: continue

                                    for i, pairing_info in enumerate(all_pairings_by_group[group]):
                                        team1, team2 = pairing_info['pair']

                                        can_play1 = not team_last_played.get(team1.id) or (current_date - team_last_played[team1.id].date()) >= rest_days
                                        can_play2 = not team_last_played.get(team2.id) or (current_date - team_last_played[team2.id].date()) >= rest_days
                                        team1_weekly_ok = not max_matches_per_team_per_week or team_matches_this_week[team1.id] < max_matches_per_team_per_week
                                        team2_weekly_ok = not max_matches_per_team_per_week or team_matches_this_week[team2.id] < max_matches_per_team_per_week

                                        if can_play1 and can_play2 and team1_weekly_ok and team2_weekly_ok:
                                            scheduled_matches.append({ 'team1_name': team1.name, 'team1_id': team1.id, 'team2_name': team2.name, 'team2_id': team2.id, 'match_time': current_datetime.isoformat(), 'location': location, 'group_name': group.name if hasattr(group, 'name') else str(group), 'leg': pairing_info.get('leg') })
                                            team_last_played[team1.id] = team_last_played[team2.id] = current_datetime
                                            team_matches_this_week[team1.id] += 1
                                            team_matches_this_week[team2.id] += 1
                                            group_matches_this_week[group_id] += 1
                                            all_pairings_by_group[group].pop(i)
                                            match_scheduled_in_slot = True
                                            break

                            if matches_per_week and matches_this_week_count >= matches_per_week: break

                    day_offset += 1
                    current_date = start_date + timedelta(days=day_offset)

                unscheduled_matches = [p['pair'] for pairings in all_pairings_by_group.values() for p in pairings]

                schedule_by_group = defaultdict(list)
                scheduled_matches.sort(key=lambda x: x['match_time'])
                # Tính vòng: gom theo tuần-thứ tự để gán round_number tuần tự
                for match in scheduled_matches:
                    match['match_time'] = datetime.fromisoformat(match['match_time'])
                schedule_by_group_intermediate = defaultdict(list)
                for m in scheduled_matches:
                    schedule_by_group_intermediate[m['group_name']].append(m)
                for gname, mlist in schedule_by_group_intermediate.items():
                    mlist.sort(key=lambda x: x['match_time'])
                    round_counter = 1
                    last_day = None
                    for m in mlist:
                        cur_day = m['match_time'].date()
                        if last_day is None:
                            last_day = cur_day
                        elif cur_day != last_day:
                            round_counter += 1
                            last_day = cur_day
                        m['round_number'] = round_counter
                        schedule_by_group[gname].append(m)

                request.session['schedule_preview_json'] = json.dumps([{**m, 'match_time': m['match_time'].isoformat()} for m in scheduled_matches])

                context = { 'tournament': tournament, 'form': form, 'schedule_by_group': dict(sorted(schedule_by_group.items())), 'unscheduled_matches': unscheduled_matches, }
                return render(request, 'tournaments/generate_schedule.html', context)

    form = ScheduleGenerationForm(initial={'start_date': timezone.now().date() + timedelta(days=1)})
    context = { 'tournament': tournament, 'form': form, 'schedule_by_group': None, 'unscheduled_matches': None, }
    return render(request, 'tournaments/generate_schedule.html', context)


def player_detail(request, pk):
    player = get_object_or_404(Player.objects.select_related('team'), pk=pk)

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

    # === BẮT ĐẦU KHỐI CODE MỚI ĐỂ KIỂM TRA QUYỀN VOTE ===
    can_vote = False
    if request.user.is_authenticated and player.team:
        # Kiểm tra xem cầu thủ có đang tham gia một giải đấu nào đang diễn ra không
        is_in_active_tournament = TeamRegistration.objects.filter(
            team=player.team, 
            tournament__status='IN_PROGRESS'
        ).exists()
        
        # Người dùng có thể vote nếu: đang ở giải đấu active VÀ không phải là chính mình
        if is_in_active_tournament and request.user != player.user:
            can_vote = True

    stats = {
        'total_goals': total_goals,
        'yellow_cards': cards.get('yellow_cards', 0),
        'red_cards': cards.get('red_cards', 0),
        'matches_played': matches_played,
        'matches_played_count': matches_played.count(),
    }

    badges = []
    # SỬA LỖI: Lấy tournament từ registration
    registration = TeamRegistration.objects.filter(team=player.team).first()
    if registration:
        tournament = registration.tournament
        top_scorer_in_tourn = Player.objects.filter(team__registrations__tournament=tournament).annotate(goal_count=Count('goals', filter=Q(goals__is_own_goal=False, goals__match__tournament=tournament))).order_by('-goal_count').first()

        if top_scorer_in_tourn and top_scorer_in_tourn.pk == player.pk and stats['total_goals'] > 0:
            badges.append({'name': 'Vua phá lưới', 'icon': 'bi-trophy-fill', 'color': 'text-warning'})

        most_played_in_tourn = Player.objects.filter(team__registrations__tournament=tournament).annotate(match_count=Count('lineups', filter=Q(lineups__match__tournament=tournament))).order_by('-match_count').first()
        if most_played_in_tourn and most_played_in_tourn.pk == player.pk and stats['matches_played_count'] > 0:
            badges.append({'name': 'Cột trụ đội bóng', 'icon': 'bi-gem', 'color': 'text-info'})

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
        'can_vote': can_vote,
    }
    return render(request, 'tournaments/player_detail.html', context)


@login_required
def claim_player_profile(request, pk):
    player_to_claim = get_object_or_404(Player, pk=pk)

    if player_to_claim.user is not None:
        messages.error(request, "Hồ sơ này đã được một tài khoản khác liên kết.")
        return redirect('player_detail', pk=pk)

    # Kiểm tra xem có cần xác nhận từ đội trưởng không
    if player_to_claim.team and player_to_claim.team.captain != request.user:
        # Tạo thông báo cho đội trưởng
        notification = Notification.objects.create(
            user=player_to_claim.team.captain,
            title="Yêu cầu liên kết cầu thủ",
            message=f"{request.user.get_full_name()} muốn liên kết với cầu thủ '{player_to_claim.full_name}' trong đội '{player_to_claim.team.name}'. Vui lòng xác nhận.",
            notification_type='player_claim_request',
            related_player=player_to_claim,
            related_user=request.user
        )
        # Cập nhật related_url sau khi có pk
        notification.related_url = f"/confirm-player-claim/{notification.pk}/"
        notification.save()
        
        messages.info(request, f"Đã gửi yêu cầu liên kết đến đội trưởng {player_to_claim.team.captain.get_full_name()}. Vui lòng chờ xác nhận.")
        return redirect('player_detail', pk=pk)
    
    # Nếu là cầu thủ tự do hoặc đội trưởng tự claim, liên kết trực tiếp
    if hasattr(request.user, 'player_profile') and request.user.player_profile is not None:
        old_player = request.user.player_profile
        old_player.user = None
        old_player.save()
        messages.info(request, f"Đã hủy liên kết với hồ sơ cầu thủ '{old_player.full_name}'.")

    player_to_claim.user = request.user
    player_to_claim.save()
    messages.success(request, f"Bạn đã liên kết thành công với hồ sơ cầu thủ '{player_to_claim.full_name}'.")
    return redirect('player_detail', pk=pk)

@login_required
def confirm_player_claim_view(request, notification_id):
    """Xác nhận liên kết cầu thủ từ đội trưởng"""
    try:
        notification = Notification.objects.get(pk=notification_id)
    except Notification.DoesNotExist:
        messages.error(request, "Thông báo không tồn tại.")
        return redirect('transfer_market')
    
    # Kiểm tra quyền truy cập
    if notification.user != request.user:
        messages.error(request, "Bạn không có quyền truy cập thông báo này.")
        return redirect('transfer_market')
    
    if notification.notification_type != 'player_claim_request':
        messages.error(request, "Thông báo không hợp lệ.")
        return redirect('transfer_market')
    
    player = notification.related_player
    claiming_user = notification.related_user
    
    if not player or not claiming_user:
        messages.error(request, "Thông tin yêu cầu không đầy đủ.")
        return redirect('transfer_market')
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'confirm':
            # Đội trưởng xác nhận
            if player.team and player.team.captain == request.user:
                # Nếu user đã có player_profile, xóa liên kết cũ
                if hasattr(claiming_user, 'player_profile') and claiming_user.player_profile is not None:
                    old_player = claiming_user.player_profile
                    old_player.user = None
                    old_player.save()
                
                # Liên kết với hồ sơ mới
                player.user = claiming_user
                player.save()
                
                # Tạo thông báo cho người được liên kết
                Notification.objects.create(
                    user=claiming_user,
                    title="Liên kết cầu thủ thành công",
                    message=f"Đội trưởng {request.user.get_full_name()} đã xác nhận liên kết bạn với hồ sơ cầu thủ '{player.full_name}' trong đội '{player.team.name}'.",
                    notification_type='player_claim_confirmed'
                )
                
                # Xóa thông báo yêu cầu
                notification.delete()
                
                messages.success(request, f"Đã xác nhận liên kết {claiming_user.get_full_name()} với cầu thủ '{player.full_name}'.")
                return redirect('team_detail', pk=player.team.pk)
            else:
                messages.error(request, "Bạn không có quyền xác nhận liên kết này.")
                
        elif action == 'reject':
            # Đội trưởng từ chối
            # Tạo thông báo cho người bị từ chối
            Notification.objects.create(
                user=claiming_user,
                title="Yêu cầu liên kết bị từ chối",
                message=f"Đội trưởng {request.user.get_full_name()} đã từ chối yêu cầu liên kết bạn với hồ sơ cầu thủ '{player.full_name}' trong đội '{player.team.name}'.",
                notification_type='player_claim_rejected'
            )
            
            # Xóa thông báo yêu cầu
            notification.delete()
            
            messages.info(request, f"Đã từ chối yêu cầu liên kết của {claiming_user.get_full_name()}.")
            return redirect('team_detail', pk=player.team.pk)
    
    # Kiểm tra quyền truy cập
    if not player.team or player.team.captain != request.user:
        messages.error(request, "Bạn không có quyền xác nhận liên kết này.")
        return redirect('transfer_market')
    
    context = {
        'player': player,
        'team_name': player.team.name,
        'claiming_user': claiming_user
    }
    return render(request, 'tournaments/confirm_player_claim.html', context)

@login_required
def tournament_bulk_upload(request, tournament_pk):
    tournament = get_object_or_404(Tournament, pk=tournament_pk)
    if not user_can_upload_gallery(request.user, tournament):
        return HttpResponseForbidden("Bạn không có quyền thực hiện hành động này.")

    if request.method == 'POST':
        url_form = GalleryURLForm(request.POST, instance=tournament)
        if url_form.is_valid():
            url_form.save()
            messages.success(request, "Đã cập nhật thành công link album ảnh.")

        if 'images' in request.FILES:
            images = request.FILES.getlist('images')
            uploaded_count = 0
            for image_file in images:
                if image_file.content_type.startswith('image'):
                    TournamentPhoto.objects.create(tournament=tournament, image=image_file)
                    uploaded_count += 1
                else:
                    messages.warning(request, f"File '{image_file.name}' không phải là ảnh và đã bị bỏ qua.")

            if uploaded_count > 0:
                 messages.success(request, f"Đã tải lên thành công {uploaded_count} ảnh.")

        if 'images' not in request.FILES and not url_form.has_changed():
             messages.info(request, "Không có thay đổi nào được thực hiện.")

        return redirect(reverse('tournament_detail', args=[tournament_pk]) + '?tab=gallery')

    else:
        url_form = GalleryURLForm(instance=tournament)

    context = {
        'tournament': tournament,
        'url_form': url_form,
    }
    return render(request, 'tournaments/bulk_upload.html', context)

@login_required
def tournament_schedule_print_view(request, pk):
    tournament = get_object_or_404(Tournament, pk=pk)
    if not request.user.is_authenticated:
        return HttpResponseForbidden("Bạn cần đăng nhập để xem trang này.")

    is_organizer = False
    if tournament.organization:
        is_organizer = tournament.organization.members.filter(pk=request.user.pk).exists()

    if not request.user.is_staff and not is_organizer:
        return HttpResponseForbidden("Bạn không có quyền truy cập trang này.")

    groups_with_matches = []
    groups = tournament.groups.all().order_by('name')
    for group in groups:
        # SỬA LỖI: Lấy team_ids từ registrations
        team_ids_in_group = TeamRegistration.objects.filter(group=group).values_list('team_id', flat=True)
        matches = Match.objects.filter(
            tournament=tournament,
            team1_id__in=team_ids_in_group
        ).select_related('team1', 'team2').order_by('match_time')
        groups_with_matches.append({'group_name': group.name, 'matches': matches})

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
    return render(request, 'tournaments/legal/privacy_policy.html')

def terms_of_service_view(request):
    return render(request, 'tournaments/legal/terms_of_service.html')

def data_deletion_view(request):
    return render(request, 'tournaments/legal/data_deletion.html')

@login_required
@require_POST
def toggle_follow_view(request, pk):
    tournament = get_object_or_404(Tournament, pk=pk)
    user = request.user

    if user in tournament.followers.all():
        tournament.followers.remove(user)
        is_following = False
    else:
        tournament.followers.add(user)
        is_following = True

    return JsonResponse({'status': 'ok', 'is_following': is_following})

@login_required
@never_cache
def notification_list(request):
    notifications = Notification.objects.filter(user=request.user)
    unread_notification_ids = list(notifications.filter(is_read=False).values_list('id', flat=True))
    if unread_notification_ids:
        Notification.objects.filter(id__in=unread_notification_ids).update(is_read=True)

    context = {
        'notifications': notifications
    }
    return render(request, 'tournaments/notification_list.html', context)

@login_required
@require_POST
def mark_all_notifications_as_read(request):
    Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    messages.success(request, "Tất cả thông báo đã được đánh dấu là đã đọc.")
    return redirect('home')

@login_required
@require_POST # Yêu cầu phương thức POST để xóa
def delete_notification(request, pk):
    # Tìm thông báo theo id (pk) VÀ đảm bảo nó thuộc về người dùng đang đăng nhập
    notification = get_object_or_404(Notification, pk=pk, user=request.user)
    notification.delete()
    messages.success(request, "Đã xóa thông báo.")
    # Sau khi xóa, quay trở lại trang danh sách thông báo
    return redirect('notification_list')

@login_required
@require_POST
def delete_all_notifications(request):
    Notification.objects.filter(user=request.user).delete()
    messages.success(request, "Đã xóa tất cả thông báo.")
    return redirect('notification_list')

@login_required
@never_cache
def team_hall_of_fame(request, pk):
    team = get_object_or_404(Team, pk=pk)
    achievements = team.achievements.select_related('tournament').order_by('-tournament__start_date')

    form = None
    if request.user == team.captain:
        form = TeamCreationForm(instance=team, user=request.user)
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

    if not all_events:
        captain_notes = MatchNote.objects.filter(
            match=match,
            note_type=MatchNote.NoteType.CAPTAIN
        ).select_related('team')

        if captain_notes.exists():
            note_alert_event = {
                'is_captain_note_alert': True,
                'notes': list(captain_notes)
            }
            all_events.insert(0, note_alert_event)

    # Kiểm tra quyền bình luận viên
    is_commentator = TournamentStaff.objects.filter(
        tournament=match.tournament,
        user=request.user,
        role__id='COMMENTATOR'
    ).exists()
    
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
        'is_commentator': is_commentator,
    }
    return render(request, 'tournaments/match_control.html', context)

@login_required
@require_POST
def delete_match_event(request, event_type, pk):
    try:
        with transaction.atomic():
            response_data = {'status': 'success'}

            if event_type == 'goal':
                event = get_object_or_404(Goal, pk=pk)
                match = event.match

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

    user_role = "Khách"
    max_votes = 0

    is_organizer = tournament.organization and tournament.organization.members.filter(pk=user.pk).exists()
    is_captain = TeamRegistration.objects.filter(tournament=tournament, team__captain=user).exists()
    is_player = Player.objects.filter(team__registrations__tournament=tournament, user=user).exists()

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

    votes_cast_in_tournament = VoteRecord.objects.filter(voter=user, tournament=tournament).aggregate(total=Sum('weight'))['total'] or 0
    gift_votes_qs = VoteRecord.objects.filter(voter=user, tournament__isnull=True, voted_for__isnull=True)
    gift_votes_count = gift_votes_qs.count()

    total_available_votes = max_votes + gift_votes_count
    remaining_votes = total_available_votes - votes_cast_in_tournament

    progress_percentage = 0
    if total_available_votes > 0:
        progress_percentage = (votes_cast_in_tournament / total_available_votes) * 100

    if request.method == 'POST':
        player_id = request.POST.get('player_id')
        player_to_vote = get_object_or_404(Player, pk=player_id, team__registrations__tournament=tournament)

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
                messages.error(request, f"An error occurred: {e}")

    players_list = list(Player.objects.filter(team__registrations__tournament=tournament).exclude(user=user).select_related('team'))
    current_vote_value = get_current_vote_value()

    for player in players_list:
        value_from_votes = player.votes * current_vote_value
        player.market_value = player.transfer_value + value_from_votes

    players_to_vote = sorted(players_list, key=lambda p: p.market_value, reverse=True)

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
@require_POST
def cast_vote_view(request, player_pk):
    player_to_vote = get_object_or_404(Player, pk=player_pk)
    # SỬA LỖI: Lấy tournament từ registration
    registration = TeamRegistration.objects.filter(team=player_to_vote.team).first()
    if not registration:
         return JsonResponse({'status': 'error', 'message': 'Cầu thủ không thuộc giải đấu nào.'}, status=404)
    tournament = registration.tournament
    user = request.user

    max_votes = 0
    is_organizer = tournament.organization and user in tournament.organization.members.all()
    is_captain = TeamRegistration.objects.filter(tournament=tournament, team__captain=user).exists()
    is_player = Player.objects.filter(team__registrations__tournament=tournament, user=user).exists()

    if is_organizer: max_votes = 3
    elif is_captain: max_votes = 2
    elif is_player: max_votes = 1

    votes_cast_count = VoteRecord.objects.filter(voter=user, tournament=tournament).aggregate(total=Sum('weight'))['total'] or 0
    if votes_cast_count >= max_votes:
        return JsonResponse({'status': 'error', 'message': 'Bạn đã hết phiếu bầu cho giải đấu này.'}, status=403)
    if player_to_vote.user == user:
        return JsonResponse({'status': 'error', 'message': 'Bạn không thể tự bỏ phiếu cho chính mình.'}, status=403)
    if VoteRecord.objects.filter(voter=user, voted_for=player_to_vote, tournament=tournament).exists():
        return JsonResponse({'status': 'error', 'message': f"Bạn đã bỏ phiếu cho cầu thủ {player_to_vote.full_name} trước đó rồi."}, status=403)

    try:
        with transaction.atomic():
            VoteRecord.objects.create(voter=user, voted_for=player_to_vote, tournament=tournament, weight=1)
            player_to_vote.refresh_from_db(fields=['votes'])
            player_to_vote.votes = F('votes') + 1
            player_to_vote.save()
            player_to_vote.refresh_from_db(fields=['votes'])

        return JsonResponse({
            'status': 'success',
            'message': f'Bạn đã bỏ phiếu thành công cho {player_to_vote.full_name}!',
            'new_vote_count': player_to_vote.votes,
            'remaining_votes': max_votes - (votes_cast_count + 1)
        })
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': f'Đã có lỗi xảy ra ở server: {e}'}, status=500)

@login_required
@never_cache
def create_standalone_team(request):
    # --- THÊM LOGIC GIỚI HẠN ---
    TEAM_LIMIT = 3
    if Team.objects.filter(captain=request.user).count() >= TEAM_LIMIT:
        messages.error(request, f"Bạn đã đạt đến giới hạn tối đa ({TEAM_LIMIT}) đội bóng được phép tạo.")
        return redirect('dashboard')
    # --- KẾT THÚC LOGIC GIỚI HẠN ---

    if request.method == 'POST':
        form = TeamCreationForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            team = form.save(commit=False)
            team.captain = request.user
            team.save()
            messages.success(request, f"Đã tạo thành công đội '{team.name}'!")
            return redirect('team_detail', pk=team.pk)
    else:
        form = TeamCreationForm(user=request.user)

    context = {
        'form': form,
        'is_standalone': True,
        'tournament': None,
    }
    return render(request, 'tournaments/register_options.html', context)

@login_required
@never_cache
def media_dashboard(request, tournament_pk):
    tournament = get_object_or_404(Tournament, pk=tournament_pk)

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


@login_required
@never_cache
def media_edit_match(request, pk):
    match = get_object_or_404(Match, pk=pk)
    tournament = match.tournament

    is_media_staff = TournamentStaff.objects.filter(
        tournament=tournament, user=request.user, role__id__in=['MEDIA', 'PHOTOGRAPHER', 'TOURNAMENT_MANAGER']
    ).exists()
    is_btc_member = tournament.organization and tournament.organization.members.filter(pk=request.user.pk).exists()

    if not request.user.is_staff and not is_btc_member and not is_media_staff:
        return HttpResponseForbidden("Bạn không có quyền truy cập trang này.")

    if request.method == 'POST':
        form = MatchMediaUpdateForm(request.POST, request.FILES, instance=match)
        if form.is_valid():
            form.save()
            messages.success(request, f"Đã cập nhật thông tin media cho trận đấu: {match}.")
            return redirect('media_edit_match', pk=match.pk)
    else:
        form = MatchMediaUpdateForm(instance=match)

    context = {
        'form': form,
        'match': match,
        'tournament': tournament
    }
    return render(request, 'tournaments/media_edit_match.html', context)

def job_market_view(request):
    # Lấy các filter parameters
    region_filter = request.GET.get('region', '')
    role_filter = request.GET.get('role', '')
    search_query = request.GET.get('search', '')
    job_type_filter = request.GET.get('job_type', '')  # tournament hoặc stadium
    
    # Base queryset cho jobs
    jobs = JobPosting.objects.filter(status=JobPosting.Status.OPEN).select_related(
        'tournament', 'role_required', 'stadium'
    )
    
    # Apply filters
    if region_filter:
        # Filter theo region của tournament hoặc stadium
        jobs = jobs.filter(
            models.Q(tournament__region=region_filter) | 
            models.Q(stadium__region=region_filter)
        )
    
    if role_filter:
        jobs = jobs.filter(role_required__id=role_filter)
    
    if job_type_filter:
        if job_type_filter == 'tournament':
            jobs = jobs.filter(tournament__isnull=False)
        elif job_type_filter == 'stadium':
            jobs = jobs.filter(stadium__isnull=False)
    
    if search_query:
        jobs = jobs.filter(
            models.Q(title__icontains=search_query) |
            models.Q(description__icontains=search_query) |
            models.Q(tournament__name__icontains=search_query) |
            models.Q(stadium__stadium_name__icontains=search_query)
        )
    
    # Lấy professional rankings (top rated professionals)
    from users.models import CoachProfile, StadiumProfile
    from organizations.models import ProfessionalReview
    
    # Top coaches với ratings
    top_coaches = CoachProfile.objects.annotate(
        avg_rating=models.Avg('reviews__rating'),
        review_count=models.Count('reviews', filter=models.Q(reviews__is_approved=True))
    ).filter(
        review_count__gt=0,
        is_available=True
    ).order_by('-avg_rating')[:5]
    
    # Top stadiums với ratings
    top_stadiums = StadiumProfile.objects.annotate(
        avg_rating=models.Avg('reviews__rating'),
        review_count=models.Count('reviews', filter=models.Q(reviews__is_approved=True))
    ).filter(
        review_count__gt=0
    ).order_by('-avg_rating')[:5]
    
    # Top professionals từ job applications (referee, media, etc.)
    top_professionals = User.objects.annotate(
        avg_rating=models.Avg('received_reviews__rating'),
        review_count=models.Count('received_reviews')
    ).filter(
        review_count__gt=0,
        profile__roles__id__in=['REFEREE', 'MEDIA', 'PHOTOGRAPHER', 'COMMENTATOR']
    ).order_by('-avg_rating')[:5]
    
    # Lấy tất cả roles để filter
    from users.models import Role
    all_roles = Role.objects.all().order_by('name')
    
    # Tìm kiếm user profiles nếu có search query
    search_users = None
    if search_query:
        # Tìm users theo username, first_name, last_name, email
        search_users = User.objects.filter(
            models.Q(username__icontains=search_query) |
            models.Q(first_name__icontains=search_query) |
            models.Q(last_name__icontains=search_query) |
            models.Q(email__icontains=search_query)
        ).select_related('profile').distinct()[:10]  # Limit 10 results
    
    context = {
        'jobs': jobs,
        'search_users': search_users,
        'all_regions': Tournament.Region.choices,
        'all_roles': all_roles,
        'current_region': region_filter,
        'current_role': role_filter,
        'current_search': search_query,
        'current_job_type': job_type_filter,
        'top_coaches': top_coaches,
        'top_stadiums': top_stadiums,
        'top_professionals': top_professionals,
    }
    return render(request, 'tournaments/job_market_new.html', context)

def job_detail_view(request, pk):
    job = get_object_or_404(JobPosting, pk=pk)
    user_has_applied = False
    is_organizer = False

    if request.user.is_authenticated:
        user_has_applied = JobApplication.objects.filter(job=job, applicant=request.user).exists()
        
        # Kiểm tra user có phải organizer không
        if job.tournament and job.tournament.organization:
            is_organizer = job.tournament.organization.members.filter(pk=request.user.pk).exists()
        elif job.stadium and job.stadium.user == request.user:
            is_organizer = True  # Stadium owner
        elif job.professional_user == request.user:
            is_organizer = True  # Professional user who posted the job
        else:
            is_organizer = False

    if request.method == 'POST' and request.user.is_authenticated:
        # Kiểm tra các điều kiện cấm ứng tuyển
        if user_has_applied:
            messages.warning(request, "Bạn đã ứng tuyển vào vị trí này rồi.")
        elif is_organizer:
            if job.professional_user == request.user:
                messages.warning(request, "Bạn không thể ứng tuyển vào chính tin đăng tìm việc của mình.")
            elif job.stadium and job.stadium.user == request.user:
                messages.warning(request, "Bạn không thể ứng tuyển vào chính tin đăng tuyển dụng của sân bóng mình.")
            else:
                messages.warning(request, "Bạn không thể ứng tuyển vào tin đăng này.")
        else:
            # Cho phép ứng tuyển
            form = JobApplicationForm(request.POST)
            if form.is_valid():
                application = form.save(commit=False)
                application.job = job
                application.applicant = request.user
                application.save()
                messages.success(request, "Bạn đã ứng tuyển thành công!")

                # Gửi thông báo cho organizer
                if job.tournament and job.tournament.organization:
                    organization = job.tournament.organization
                    btc_members = organization.members.all()
                    applicant_name = request.user.get_full_name() or request.user.username
                    notification_title = f"Có đơn ứng tuyển mới cho '{job.title}'"
                    # Xác định tên tổ chức và URL
                    if job.tournament:
                        org_name = job.tournament.name
                        notification_url = request.build_absolute_uri(
                            reverse('organizations:manage_jobs', kwargs={'tournament_pk': job.tournament.pk})
                        )
                    elif job.stadium:
                        org_name = job.stadium.stadium_name
                        notification_url = request.build_absolute_uri(reverse('stadium_dashboard'))
                    else:
                        org_name = "Tổ chức khác"
                        notification_url = request.build_absolute_uri(reverse('job_market'))
                    
                    notification_message = f"{applicant_name} vừa ứng tuyển vào vị trí của bạn tại '{org_name}'."

                    notifications_to_create = [
                        Notification(user=member, title=notification_title, message=notification_message, related_url=notification_url)
                        for member in btc_members
                    ]
                    if notifications_to_create:
                        Notification.objects.bulk_create(notifications_to_create)

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
                    
                elif job.stadium:
                    # Stadium job - gửi thông báo cho stadium owner
                    applicant_name = request.user.get_full_name() or request.user.username
                    notification_title = f"Có đơn ứng tuyển mới cho '{job.title}'"
                    org_name = job.stadium.stadium_name
                    notification_url = request.build_absolute_uri(reverse('stadium_dashboard'))
                    
                    Notification.objects.create(
                        user=job.stadium.user,
                        title=notification_title,
                        message=f"{applicant_name} vừa ứng tuyển vào vị trí của bạn tại '{org_name}'.",
                        notification_type=Notification.NotificationType.GENERIC,
                        related_url=notification_url
                    )
                    
                    # Gửi email cho stadium owner nếu có email
                    if job.stadium.user.email:
                        send_notification_email(
                            subject=f"[DBP Sports] {notification_title}",
                            template_name='organizations/emails/new_job_application.html',
                            context={
                                'job': job,
                                'applicant': request.user,
                                'application': application
                            },
                            recipient_list=[job.stadium.user.email],
                            request=request
                        )

                elif job.professional_user:
                    # Professional job - gửi thông báo cho professional user
                    applicant_name = request.user.get_full_name() or request.user.username
                    notification_title = f"Có đơn ứng tuyển mới cho '{job.title}'"
                    org_name = f"{job.professional_user.get_full_name() or job.professional_user.username} (Chuyên gia)"
                    notification_url = request.build_absolute_uri(reverse('professional_job_applications'))
                    
                    Notification.objects.create(
                        user=job.professional_user,
                        title=notification_title,
                        message=f"{applicant_name} vừa ứng tuyển vào vị trí của bạn tại '{org_name}'.",
                        notification_type=Notification.NotificationType.GENERIC,
                        related_url=notification_url
                    )
                    
                    # Gửi email cho professional user nếu có email
                    if job.professional_user.email:
                        send_notification_email(
                            subject=f"[DBP Sports] {notification_title}",
                            template_name='organizations/emails/new_job_application.html',
                            context={
                                'job': job,
                                'applicant': request.user,
                                'application': application
                            },
                            recipient_list=[job.professional_user.email],
                            request=request
                        )

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


@never_cache
@login_required
def commentator_notes_view(request, match_pk):
    match = get_object_or_404(Match.objects.select_related('tournament', 'team1', 'team2'), pk=match_pk)
    tournament = match.tournament

    is_commentator_for_tournament = TournamentStaff.objects.filter(
        tournament=tournament,
        user=request.user,
        role__id='COMMENTATOR'
    ).exists()

    if not is_commentator_for_tournament and not request.user.is_staff:
        messages.error(request, "Bạn không có quyền truy cập trang này.")
        return redirect('tournament_detail', pk=tournament.pk)

    note, created = MatchNote.objects.get_or_create(
        match=match,
        author=request.user,
        note_type=MatchNote.NoteType.COMMENTATOR
    )

    if request.method == 'POST':
        note.commentator_notes_team1 = request.POST.get('commentator_notes_team1', '')
        note.commentator_notes_team2 = request.POST.get('commentator_notes_team2', '')
        note.save()
        messages.success(request, "Đã lưu ghi chú của bạn.")
        return redirect('commentator_notes', match_pk=match.pk)

    captain_notes = MatchNote.objects.filter(
        match=match,
        note_type=MatchNote.NoteType.CAPTAIN
    ).select_related('author', 'team')

    # --- BẮT ĐẦU LOGIC MỚI ĐỂ LẤY DỮ LIỆU BỔ SUNG ---
    # 1. Thống kê toàn giải
    tournament_stats = {
        'total_goals': Goal.objects.filter(match__tournament=tournament, is_own_goal=False).count(),
        'yellow_cards': Card.objects.filter(match__tournament=tournament, card_type='YELLOW').count(),
        'red_cards': Card.objects.filter(match__tournament=tournament, card_type='RED').count(),
    }
    
    # 2. Top 5 Vua phá lưới
    top_scorers = Player.objects.filter(
        goals__match__tournament=tournament,
        goals__is_own_goal=False
    ).annotate(
        num_goals=Count('goals')
    ).order_by('-num_goals')[:5]

    # 3. Cầu thủ đáng chú ý của 2 đội
    team1_top_scorer = Player.objects.filter(
        team=match.team1, 
        goals__match__tournament=tournament,
        goals__is_own_goal=False
    ).annotate(num_goals=Count('goals')).order_by('-num_goals').first()

    team2_top_scorer = Player.objects.filter(
        team=match.team2, 
        goals__match__tournament=tournament,
        goals__is_own_goal=False
    ).annotate(num_goals=Count('goals')).order_by('-num_goals').first()
    
    # 4. Nhà tài trợ
    sponsors = Sponsorship.objects.filter(
        tournament=tournament, 
        is_active=True
    ).select_related('package', 'sponsor__sponsor_profile').order_by('package__order', 'order')

    # 5. Bảng xếp hạng (logic tương tự tournament_detail)
    standings_data = defaultdict(list)
    groups = tournament.groups.prefetch_related('registrations__team').all()
    if groups:
        # Lấy tất cả các đội đã được duyệt trong giải đấu
        paid_teams_in_tournament_ids = TeamRegistration.objects.filter(
            tournament=tournament, payment_status='PAID'
        ).values_list('team_id', flat=True)

        # Lấy tất cả các trận đã kết thúc của giải đấu
        finished_matches_in_tournament = Match.objects.filter(
            tournament=tournament,
            team1_score__isnull=False,
            team2_score__isnull=False
        )

        team_stats = {team_id: {
            'played': 0, 'wins': 0, 'draws': 0, 'losses': 0,
            'gf': 0, 'ga': 0, 'gd': 0, 'points': 0,
            'team_obj': None # Sẽ được điền sau
        } for team_id in paid_teams_in_tournament_ids}
        
        teams_map = {team.id: team for team in Team.objects.filter(id__in=paid_teams_in_tournament_ids)}
        for team_id in team_stats:
            team_stats[team_id]['team_obj'] = teams_map.get(team_id)

        for match in finished_matches_in_tournament:
            t1_id, t2_id, s1, s2 = match.team1_id, match.team2_id, match.team1_score, match.team2_score
            if t1_id in team_stats and t2_id in team_stats:
                # Cập nhật các chỉ số... (giống hệt trong tournament_detail)
                team_stats[t1_id]['played'] += 1; team_stats[t2_id]['played'] += 1
                team_stats[t1_id]['gf'] += s1; team_stats[t1_id]['ga'] += s2
                team_stats[t2_id]['gf'] += s2; team_stats[t2_id]['ga'] += s1
                if s1 > s2:
                    team_stats[t1_id]['wins'] += 1; team_stats[t1_id]['points'] += 3
                    team_stats[t2_id]['losses'] += 1
                elif s2 > s1:
                    team_stats[t2_id]['wins'] += 1; team_stats[t2_id]['points'] += 3
                    team_stats[t1_id]['losses'] += 1
                else:
                    team_stats[t1_id]['draws'] += 1; team_stats[t1_id]['points'] += 1
                    team_stats[t2_id]['draws'] += 1; team_stats[t2_id]['points'] += 1

        for group in groups:
            group_team_ids = group.registrations.filter(payment_status='PAID').values_list('team_id', flat=True)
            group_standings = [team_stats[team_id] for team_id in group_team_ids if team_id in team_stats]
            for stats in group_standings:
                stats['gd'] = stats['gf'] - stats['ga']
            group_standings.sort(key=lambda x: (x['points'], x['gd'], x['gf']), reverse=True)
            standings_data[group.id] = group_standings
    # --- KẾT THÚC LOGIC MỚI ---

    context = {
        'match': match,
        'note': note,
        'captain_notes': captain_notes,
        'tournament_stats': tournament_stats,
        'top_scorers': top_scorers,
        'team1_top_scorer': team1_top_scorer,
        'team2_top_scorer': team2_top_scorer,
        'sponsors': sponsors,
        'standings_data': standings_data, # Gửi dữ liệu BXH
        'tournament': tournament, # Gửi cả object tournament
    }
    return render(request, 'tournaments/commentator_notes.html', context)
    

@login_required
@never_cache
def captain_note_view(request, match_pk, team_pk):
    match = get_object_or_404(Match, pk=match_pk)
    team = get_object_or_404(Team, pk=team_pk)

    if request.user != team.captain:
        return HttpResponseForbidden("Bạn không phải đội trưởng của đội này.")

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
@require_POST
def register_existing_team(request, tournament_pk, team_pk):
    tournament = get_object_or_404(Tournament, pk=tournament_pk)
    team = get_object_or_404(Team, pk=team_pk, captain=request.user)

    if TeamRegistration.objects.filter(tournament=tournament, team=team).exists():
        messages.warning(request, f"Đội '{team.name}' đã được đăng ký vào giải này rồi.")
        return redirect('tournament_detail', pk=tournament_pk)

    registration = TeamRegistration.objects.create(team=team, tournament=tournament)
    
    # Gửi email thông báo cho admin và BTC
    admin_emails = getattr(settings, 'ADMIN_EMAILS', [settings.ADMIN_EMAIL])
    btc_emails = []
    
    # Lấy email của BTC members
    if tournament.organization:
        btc_emails = [member.email for member in tournament.organization.members.all() if member.email]
    
    # Gộp danh sách email và loại bỏ trùng lặp
    recipient_list = list(set(admin_emails + btc_emails))
    recipient_list = [email for email in recipient_list if email and email != 'admin@example.com']
    
    if recipient_list:
        email_sent = send_notification_email(
            subject=f"Đội đăng ký giải đấu: {team.name} - {tournament.name}",
            template_name='tournaments/emails/new_team_registration.html',
            context={'team': team, 'tournament': tournament, 'registration': registration},
            recipient_list=recipient_list
        )

    messages.success(request, f"Đã đăng ký thành công đội '{team.name}' vào giải đấu. Vui lòng hoàn tất lệ phí.")
    return redirect('team_detail', pk=team.pk)


# Chi tiết đội bóng
@never_cache
def public_team_detail(request, pk):
    team = get_object_or_404(Team.objects.select_related('captain'), pk=pk)

    # Lịch sử tham gia giải đấu
    registrations = TeamRegistration.objects.filter(team=team).select_related('tournament').order_by('-tournament__start_date')

    # Lấy danh sách cầu thủ trong đội
    players = team.players.all().order_by('jersey_number')

    # Thành tích
    achievements = team.achievements.select_related('tournament').order_by('-achieved_at')

    # Lịch sử thi đấu
    matches_played = Match.objects.filter(
        Q(team1=team) | Q(team2=team),
        team1_score__isnull=False
    ).select_related('tournament', 'team1', 'team2').order_by('-match_time')

    # Tính toán thống kê
    stats = {'played': matches_played.count(), 'wins': 0, 'draws': 0, 'losses': 0, 'goals_for': 0, 'goals_against': 0}
    for match in matches_played:
        if match.winner == team: stats['wins'] += 1
        elif match.loser == team: stats['losses'] += 1
        else: stats['draws'] += 1
        
        if match.team1 == team:
            stats['goals_for'] += match.team1_score if match.team1_score is not None else 0
            stats['goals_against'] += match.team2_score if match.team2_score is not None else 0
        else:
            stats['goals_for'] += match.team2_score if match.team2_score is not None else 0
            stats['goals_against'] += match.team1_score if match.team1_score is not None else 0
            
    # --- BẮT ĐẦU LOGIC TÍNH GIÁ TRỊ NÂNG CẤP ---
    
    # Lấy hệ số nhân động từ hàm tiện ích
    dynamic_multiplier = get_current_vote_value() / 5000 # Lấy hệ số gốc (ví dụ: 5000) làm mốc để có tỉ lệ nhân hợp lý

    # 1. Giá trị Nền (không đổi)
    base_value = team.transfer_value

    # 2. Giá trị Đội hình (không đổi)
    squad_value = 0
    players_in_team = Player.objects.filter(team=team)
    for player in players_in_team:
        squad_value += player.transfer_value + (player.votes * get_current_vote_value())

    # 3. Thưởng Thành tích (nhân với hệ số)
    achievement_bonus_base = 0
    for achievement in achievements:
        if achievement.achievement_type == 'CHAMPION': achievement_bonus_base += 2000000
        elif achievement.achievement_type == 'RUNNER_UP': achievement_bonus_base += 1000000
        elif achievement.achievement_type == 'THIRD_PLACE': achievement_bonus_base += 500000
        else: achievement_bonus_base += 200000
    achievement_bonus = achievement_bonus_base * dynamic_multiplier

    # 4. Thưởng Phong độ (nhân với hệ số)
    performance_bonus_base = (stats['wins'] - stats['losses']) * 50000
    performance_bonus = performance_bonus_base * dynamic_multiplier

    # 5. Giá trị Phiếu bầu của Đội (nhân với hệ số)
    team_vote_value_base = team.votes * 20000
    team_vote_value = team_vote_value_base * dynamic_multiplier

    # Tổng giá trị
    total_value = base_value + squad_value + achievement_bonus + performance_bonus + team_vote_value
    
    can_vote = False
    if request.user.is_authenticated:
        is_in_active_tournament = registrations.filter(tournament__status='IN_PROGRESS').exists()
        if request.user != team.captain and is_in_active_tournament:
            can_vote = True

    context = {
        'team': team,
        'registrations': registrations,
        'achievements': achievements,
        'matches_played': matches_played,
        'stats': stats,
        'total_value': total_value,
        'can_vote': can_vote,
        'players': players,
        'value_breakdown': {
            'base_value': base_value,
            'squad_value': squad_value,
            'achievement_bonus': achievement_bonus,
            'performance_bonus': performance_bonus,
            'team_vote_value': team_vote_value,
        }
    }
    return render(request, 'tournaments/public_team_detail.html', context)


@login_required
def upload_team_banner(request, team_pk):
    """Upload team banner image"""
    try:
        team = Team.objects.get(pk=team_pk)
        # Kiểm tra quyền: đội trưởng hoặc cầu thủ trong đội
        is_captain = team.captain == request.user
        is_player_in_team = Player.objects.filter(team=team, user=request.user).exists()
        
        if not (is_captain or is_player_in_team):
            messages.error(request, "Không tìm thấy đội bóng hoặc bạn không có quyền chỉnh sửa.")
            return redirect('dashboard')
    except Team.DoesNotExist:
        messages.error(request, "Không tìm thấy đội bóng hoặc bạn không có quyền chỉnh sửa.")
        return redirect('dashboard')
    
    if request.method == 'POST':
        banner_image = request.FILES.get('banner_image')
        if banner_image:
            # Validate file type
            allowed_types = ['image/jpeg', 'image/jpg', 'image/png', 'image/webp']
            if banner_image.content_type not in allowed_types:
                messages.error(request, "Chỉ chấp nhận file ảnh (JPG, PNG, WebP).")
                return redirect('public_team_detail', pk=team_pk)
            
            # Tự động nén ảnh để giảm kích thước
            try:
                compressed_image = compress_banner_image(banner_image)
                team.banner_image = compressed_image
                team.save()
                
                if is_captain:
                    messages.success(request, "Đã cập nhật ảnh bìa hồ sơ đội bóng thành công! Ảnh đã được tự động nén để tối ưu.")
                else:
                    messages.success(request, "Đã cập nhật ảnh bìa hồ sơ cầu thủ thành công! Ảnh đã được tự động nén để tối ưu.")
            except Exception as e:
                messages.error(request, f"Có lỗi xảy ra khi xử lý ảnh: {str(e)}")
                # Redirect về trang phù hợp
                if is_captain:
                    return redirect('public_team_detail', pk=team_pk)
                else:
                    # Tìm player của user này trong team
                    try:
                        player = Player.objects.get(team=team, user=request.user)
                        return redirect('player_detail', pk=player.pk)
                    except Player.DoesNotExist:
                        return redirect('public_team_detail', pk=team_pk)
    
    # Redirect về trang phù hợp
    if is_captain:
        return redirect('public_team_detail', pk=team_pk)
    else:
        # Tìm player của user này trong team
        try:
            player = Player.objects.get(team=team, user=request.user)
            return redirect('player_detail', pk=player.pk)
        except Player.DoesNotExist:
            return redirect('public_team_detail', pk=team_pk)  


@login_required
def upload_player_banner(request, player_pk):
    """Upload player banner image"""
    try:
        player = Player.objects.get(pk=player_pk, user=request.user)
    except Player.DoesNotExist:
        messages.error(request, "Không tìm thấy hồ sơ cầu thủ hoặc bạn không có quyền chỉnh sửa.")
        return redirect('dashboard')
    
    if request.method == 'POST':
        banner_image = request.FILES.get('banner_image')
        if banner_image:
            # Validate file type
            allowed_types = ['image/jpeg', 'image/jpg', 'image/png', 'image/webp']
            if banner_image.content_type not in allowed_types:
                messages.error(request, "Chỉ chấp nhận file ảnh (JPG, PNG, WebP).")
                return redirect('player_detail', pk=player_pk)
            
            # Tự động nén ảnh để giảm kích thước
            try:
                compressed_image = compress_banner_image(banner_image)
                player.banner_image = compressed_image
                player.save()
                
                messages.success(request, "Đã cập nhật ảnh bìa hồ sơ cầu thủ thành công! Ảnh đã được tự động nén để tối ưu.")
            except Exception as e:
                messages.error(request, f"Có lỗi xảy ra khi xử lý ảnh: {str(e)}")
                return redirect('player_detail', pk=player_pk)
    
    return redirect('player_detail', pk=player_pk)


@login_required
@require_POST
def cast_team_vote_view(request, team_pk):
    team_to_vote = get_object_or_404(Team, pk=team_pk)

    # Tìm một giải đấu mà đội này đang tham gia và còn đang diễn ra
    active_registration = TeamRegistration.objects.filter(
        team=team_to_vote, 
        tournament__status='IN_PROGRESS'
    ).first()

    if not active_registration:
        return JsonResponse({'status': 'error', 'message': 'Không thể bỏ phiếu cho đội không tham gia giải đấu nào đang diễn ra.'}, status=400)

    tournament = active_registration.tournament
    user = request.user

    # Logic kiểm tra quyền và số phiếu còn lại (tương tự player)
    max_votes = 1 # Tạm thời cho mỗi người 1 phiếu/đội/giải
    votes_cast_count = TeamVoteRecord.objects.filter(voter=user, tournament=tournament).count()

    if votes_cast_count >= max_votes:
        return JsonResponse({'status': 'error', 'message': 'Bạn đã hết phiếu bầu cho các đội trong giải đấu này.'}, status=403)
    if team_to_vote.captain == user:
        return JsonResponse({'status': 'error', 'message': 'Bạn không thể tự bỏ phiếu cho đội của mình.'}, status=403)
    if TeamVoteRecord.objects.filter(voter=user, voted_for=team_to_vote, tournament=tournament).exists():
        return JsonResponse({'status': 'error', 'message': f"Bạn đã bỏ phiếu cho đội {team_to_vote.name} trước đó rồi."}, status=403)

    try:
        with transaction.atomic():
            TeamVoteRecord.objects.create(voter=user, voted_for=team_to_vote, tournament=tournament, weight=1)
            team_to_vote.votes = F('votes') + 1
            team_to_vote.save()
            team_to_vote.refresh_from_db(fields=['votes'])

        return JsonResponse({
            'status': 'success',
            'message': f'Bạn đã bỏ phiếu thành công cho {team_to_vote.name}!',
            'new_vote_count': team_to_vote.votes,
        })
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': f'Đã có lỗi xảy ra ở server: {e}'}, status=500)    

@login_required
@require_POST # Chỉ cho phép truy cập bằng phương thức POST
def invite_player_view(request, player_pk, team_pk):
    """
    Xử lý việc đội trưởng của `team_pk` gửi lời mời đến `player_pk`.
    """
    inviting_team = get_object_or_404(Team, pk=team_pk)
    target_player = get_object_or_404(Player.objects.select_related('team__captain'), pk=player_pk)

    # --- Các bước kiểm tra quyền và điều kiện ---
    if inviting_team.captain != request.user:
        messages.error(request, "Bạn không phải là đội trưởng của đội này.")
        return redirect('transfer_market') # Chuyển về chợ chuyển nhượng

    # Cho phép mời cầu thủ tự do
    # if not target_player.team:
    #     messages.error(request, "Cầu thủ này là cầu thủ tự do, bạn có thể 'Chiêu mộ' trực tiếp.")
    #     return redirect('transfer_market')

    if target_player.team == inviting_team:
        messages.error(request, "Bạn không thể mời một cầu thủ đã ở trong đội của mình.")
        return redirect('transfer_market')

    if PlayerTransfer.objects.filter(inviting_team=inviting_team, player=target_player, status='PENDING').exists():
        messages.warning(request, f"Bạn đã gửi lời mời đến cầu thủ {target_player.full_name} rồi. Vui lòng chờ phản hồi.")
        return redirect('transfer_market')

    # === BẮT ĐẦU CẬP NHẬT LOGIC XỬ LÝ FORM ===
    form = PlayerTransferForm(request.POST)
    if form.is_valid():
        transfer_type = form.cleaned_data['transfer_type']
        loan_end_date = form.cleaned_data.get('loan_end_date')
        offer_amount = form.cleaned_data.get('offer_amount', 0)

        if transfer_type == PlayerTransfer.TransferType.LOAN and not loan_end_date:
            messages.error(request, "Bạn phải chọn ngày kết thúc hợp đồng cho mượn.")
            return redirect('transfer_market')

        try:
            with transaction.atomic():
                transfer = PlayerTransfer.objects.create(
                    inviting_team=inviting_team,
                    current_team=target_player.team,
                    player=target_player,
                    status=PlayerTransfer.Status.PENDING,
                    transfer_type=transfer_type,
                    loan_end_date=loan_end_date,
                    offer_amount=offer_amount
                )

            # Xác định người nhận thông báo
            if target_player.team:
                # Cầu thủ có đội -> thông báo cho đội trưởng
                captain_to_notify = target_player.team.captain
                notification_title = "Bạn có lời mời chuyển nhượng mới"
                notification_message = (
                    f"Đội '{inviting_team.name}' đã gửi lời mời chuyển nhượng cho cầu thủ "
                    f"'{target_player.full_name}' của bạn."
                )
                email_subject = f"[DBP Sports] Lời mời chuyển nhượng cho cầu thủ {target_player.full_name}"
            else:
                # Cầu thủ tự do -> thông báo cho cầu thủ hoặc người đại diện
                if target_player.user:
                    captain_to_notify = target_player.user
                    notification_title = "Bạn có lời mời gia nhập đội bóng"
                    notification_message = (
                        f"Đội '{inviting_team.name}' đã gửi lời mời cho bạn gia nhập đội bóng của họ."
                    )
                    email_subject = f"[DBP Sports] Lời mời gia nhập đội bóng từ {inviting_team.name}"
                else:
                    # Không có user account -> không thể gửi thông báo
                    captain_to_notify = None
            
            if captain_to_notify:
                # Cập nhật URL thông báo trong app để trỏ thẳng đến tab chuyển nhượng
                notification_url = request.build_absolute_uri(reverse('dashboard') + '?tab=transfers')

                # Gửi thông báo trong app (in-app notification)
                Notification.objects.create(
                    user=captain_to_notify,
                    title=notification_title,
                    message=notification_message,
                    notification_type=Notification.NotificationType.GENERIC,
                    related_url=notification_url
                )

                # === GỬI EMAIL THÔNG BÁO ===
                if captain_to_notify.email:
                    email_template = 'organizations/emails/new_transfer_invitation.html' if target_player.team else 'organizations/emails/free_agent_invitation.html'
                    send_notification_email(
                        subject=email_subject,
                        template_name=email_template,
                        context={
                            'inviting_team': inviting_team,
                            'current_team': target_player.team,
                            'player': target_player
                        },
                        recipient_list=[captain_to_notify.email],
                        request=request
                    )        

            messages.success(request, f"Đã gửi lời mời {transfer.get_transfer_type_display()} trị giá {offer_amount:,.0f} VNĐ đến cầu thủ {target_player.full_name} thành công!")

        except Exception as e:
            messages.error(request, f"An error occurred: {e}")
    else:
        error_str = ". ".join([f"{field}: {err[0]}" for field, err in form.errors.items()])
        messages.error(request, f"Dữ liệu lời mời không hợp lệ: {error_str}")
    # === KẾT THÚC CẬP NHẬT LOGIC ===

    return redirect('transfer_market')       


# LOGIC CHUYỂN NHƯỢNG
@login_required
@require_POST
def respond_to_transfer_view(request, transfer_pk):
    """
    Xử lý việc đội trưởng đồng ý hoặc từ chối một lời mời chuyển nhượng.
    """
    transfer = get_object_or_404(
        PlayerTransfer.objects.select_related(
            'player', 'inviting_team__captain', 'current_team__captain'
        ), 
        pk=transfer_pk
    )

    # Kiểm tra quyền phản hồi
    if transfer.current_team:
        # Cầu thủ có đội -> chỉ đội trưởng mới có quyền phản hồi
        if transfer.current_team.captain != request.user:
            messages.error(request, "Bạn không có quyền phản hồi lời mời này.")
            return redirect('dashboard')
    else:
        # Cầu thủ tự do -> chỉ cầu thủ đó mới có quyền phản hồi
        if transfer.player.user != request.user:
            messages.error(request, "Bạn không có quyền phản hồi lời mời này.")
            return redirect('dashboard')

    action = request.POST.get('action')

    try:
        with transaction.atomic():
            if action == 'accept':
                player = transfer.player
                inviting_team = transfer.inviting_team
                current_team = transfer.current_team
                offer_amount = transfer.offer_amount

                # === BƯỚC 1: KIỂM TRA XUNG ĐỘT SỐ ÁO TRƯỚC KHI LÀM GÌ KHÁC ===
                if Player.objects.filter(team=inviting_team, jersey_number=player.jersey_number).exists():
                    messages.error(request, f"Thất bại! Số áo {player.jersey_number} đã có người sử dụng trong đội '{inviting_team.name}'. Vui lòng yêu cầu đội bạn đổi số áo trước.")
                    # Tự động hủy lời mời này để tránh lỗi lặp lại
                    transfer.status = PlayerTransfer.Status.CANCELED
                    transfer.save()
                    # Gửi thông báo cho đội mời biết lý do
                    Notification.objects.create(
                        user=inviting_team.captain,
                        title=f"Chuyển nhượng cầu thủ {player.full_name} thất bại",
                        message=f"Lời mời của bạn đã bị hủy do xung đột số áo ({player.jersey_number}) trong đội hình của bạn."
                    )
                    return redirect(reverse('dashboard') + '?tab=transfers')
                
                # === BƯỚC 2: KIỂM TRA VÀ XỬ LÝ NGÂN SÁCH ===
                if inviting_team.budget < offer_amount:
                    messages.error(request, f"Thất bại! Đội '{inviting_team.name}' không đủ ngân sách (cần {offer_amount:,.0f} VNĐ, chỉ có {inviting_team.budget:,.0f} VNĐ).")
                    transfer.status = PlayerTransfer.Status.CANCELED
                    transfer.save()
                    Notification.objects.create(
                        user=inviting_team.captain,
                        title="Chuyển nhượng thất bại do không đủ ngân sách",
                        message=f"Lời mời của bạn cho cầu thủ '{player.full_name}' đã bị hủy."
                    )
                    return redirect(reverse('dashboard') + '?tab=transfers')

                # Trừ tiền đội mua, cộng tiền cho đội bán (nếu có)
                inviting_team.budget -= offer_amount
                inviting_team.save()
                
                if current_team:
                    current_team.budget += offer_amount
                    current_team.save()
                
                # === BƯỚC 3: HOÀN TẤT CHUYỂN NHƯỢNG VÀ GỬI THÔNG BÁO ===
                transfer.status = PlayerTransfer.Status.ACCEPTED
                transfer.save()
                
                old_team_name = player.team.name if player.team else "Cầu thủ tự do"
                player.team = inviting_team
                player.save()
                
                PlayerTransfer.objects.filter(player=player, status=PlayerTransfer.Status.PENDING).update(status=PlayerTransfer.Status.CANCELED)

                # Tạo thông báo thành công
                if current_team:
                    # Cầu thủ có đội -> thông báo cho đội trưởng
                    if transfer.transfer_type == PlayerTransfer.TransferType.PERMANENT:
                        success_message = f"Đã đồng ý bán đứt cầu thủ {player.full_name} sang đội {inviting_team.name} với giá {offer_amount:,.0f} VNĐ."
                    else:
                        success_message = f"Đã đồng ý cho mượn cầu thủ {player.full_name} đến hết ngày {transfer.loan_end_date.strftime('%d/%m/%Y')} với phí {offer_amount:,.0f} VNĐ."
                else:
                    # Cầu thủ tự do -> thông báo cho cầu thủ
                    if transfer.transfer_type == PlayerTransfer.TransferType.PERMANENT:
                        success_message = f"Bạn đã đồng ý gia nhập đội {inviting_team.name} với giá trị {offer_amount:,.0f} VNĐ."
                    else:
                        success_message = f"Bạn đã đồng ý gia nhập đội {inviting_team.name} theo hình thức cho mượn đến hết ngày {transfer.loan_end_date.strftime('%d/%m/%Y')} với phí {offer_amount:,.0f} VNĐ."
                messages.success(request, success_message)
                
                # ... (Phần gửi notification và email cho các bên liên quan giữ nguyên)
                Notification.objects.create(
                    user=transfer.inviting_team.captain,
                    title="Lời mời chuyển nhượng được chấp nhận!",
                    message=f"{old_team_name} đã đồng ý cho cầu thủ '{player.full_name}' chuyển sang đội của bạn."
                )
                if player.user:
                    Notification.objects.create(
                        user=player.user,
                        title="Bạn đã được chuyển sang đội mới!",
                        message=f"Bạn đã chính thức chuyển từ đội '{old_team_name}' sang đội '{transfer.inviting_team.name}'."
                    )
                # Gửi email cho đội trưởng đội mời
                if transfer.inviting_team.captain.email:
                    send_notification_email(
                        subject=f"[DBP Sports] Lời mời chuyển nhượng cho {player.full_name} được chấp nhận",
                        template_name='organizations/emails/transfer_accepted_notification.html',
                        context={'inviting_team': inviting_team, 'current_team': current_team, 'player': player, 'transfer': transfer},
                        recipient_list=[transfer.inviting_team.captain.email],
                        request=request
                    )
                
                # Gửi email cho cầu thủ tự do
                if not current_team and player.user and player.user.email:
                    send_notification_email(
                        subject=f"[DBP Sports] Chuyển nhượng thành công - Gia nhập đội {inviting_team.name}",
                        template_name='organizations/emails/free_agent_transfer_accepted.html',
                        context={'inviting_team': inviting_team, 'current_team': current_team, 'player': player, 'transfer': transfer},
                        recipient_list=[player.user.email],
                        request=request
                    )

            elif action == 'reject':
                transfer.status = PlayerTransfer.Status.REJECTED
                transfer.save()
                current_team_name = transfer.current_team.name if transfer.current_team else "Cầu thủ tự do"
                Notification.objects.create(
                    user=transfer.inviting_team.captain,
                    title="Lời mời chuyển nhượng bị từ chối",
                    message=f"{current_team_name} đã từ chối lời mời chuyển nhượng cho cầu thủ '{transfer.player.full_name}'."
                )

                if transfer.inviting_team.captain.email:
                    send_notification_email(
                        subject=f"[DBP Sports] Lời mời chuyển nhượng cho {transfer.player.full_name} bị từ chối",
                        template_name='organizations/emails/transfer_rejected_notification.html',
                        context={'inviting_team': transfer.inviting_team, 'current_team': transfer.current_team, 'player': transfer.player},
                        recipient_list=[transfer.inviting_team.captain.email],
                        request=request
                    )
                
                messages.info(request, "Bạn đã từ chối lời mời chuyển nhượng.")
            
            else:
                messages.error(request, "Hành động không hợp lệ.")

    except Exception as e:
        messages.error(request, f"An error occurred during processing: {e}")

    return redirect(reverse('dashboard') + '?tab=transfers')     

# === THỊ TRƯỜNG CHUYỂN NHƯỢNG ===
@never_cache
def transfer_market_view(request):
    """
    Hiển thị trang Thị trường chuyển nhượng với các chức năng lọc và sắp xếp nâng cao.
    """
    current_vote_value = get_current_vote_value()

    players_qs = Player.objects.select_related('team').annotate(
        market_value=F('transfer_value') + (F('votes') * Value(current_vote_value))
    )

    region_filter = request.GET.get('region', '')
    location_filter = request.GET.get('location', '')
    position_filter = request.GET.get('position', '')
    team_filter = request.GET.get('team', '')
    search_query = request.GET.get('q', '')
    sort_by = request.GET.get('sort', '-market_value')

    filtered_qs_for_top = players_qs
    if region_filter:
        filtered_qs_for_top = filtered_qs_for_top.filter(region=region_filter)
    if location_filter:
        filtered_qs_for_top = filtered_qs_for_top.filter(location_detail__icontains=location_filter)
        
    top_players = filtered_qs_for_top.order_by('-market_value')[:5]
    
    # Dòng này bây giờ sẽ hoạt động chính xác
    looking_for_club_players = filtered_qs_for_top.filter(is_looking_for_club=True).order_by('-updated_at')[:5]

    if region_filter:
        players_qs = players_qs.filter(region=region_filter)
    if location_filter:
        players_qs = players_qs.filter(location_detail__icontains=location_filter)
    if position_filter:
        players_qs = players_qs.filter(position=position_filter)
    if team_filter:
        players_qs = players_qs.filter(team_id=team_filter)
    if search_query:
        players_qs = players_qs.filter(full_name__icontains=search_query)

    valid_sorts = ['market_value', '-market_value', 'full_name', '-votes']
    if sort_by in valid_sorts:
        players_qs = players_qs.order_by(sort_by)

    all_teams_with_players = Team.objects.filter(players__isnull=False).distinct().order_by('name')
    captained_teams = []
    if request.user.is_authenticated:
        captained_teams = Team.objects.filter(captain=request.user)

    context = {
        'players': players_qs,
        'top_players': top_players,
        'looking_for_club_players': looking_for_club_players,
        'current_vote_value': current_vote_value,
        'position_choices': Player.POSITION_CHOICES,
        'all_teams': all_teams_with_players,
        'all_regions': Tournament.Region.choices,
        'current_filters': {
            'region': region_filter,
            'location': location_filter,
            'position': position_filter,
            'team': team_filter,
            'q': search_query,
            'sort': sort_by,
        },
        'captained_teams': captained_teams,
    }
    return render(request, 'tournaments/transfer_market.html', context)


# === THÊM 2 HÀM MỚI VÀO CUỐI TỆP ===
@login_required
@require_POST
def add_to_scouting_list(request, player_pk, team_pk):
    team = get_object_or_404(Team, pk=team_pk, captain=request.user)
    player = get_object_or_404(Player, pk=player_pk)

    if player.team == team:
        messages.warning(request, "Không thể theo dõi cầu thủ đã ở trong đội của bạn.")
    else:
        _, created = ScoutingList.objects.get_or_create(team=team, player=player)
        if created:
            messages.success(request, f"Đã thêm {player.full_name} vào danh sách theo dõi của đội {team.name}.")
        else:
            messages.info(request, f"{player.full_name} đã có trong danh sách theo dõi của bạn.")

    return redirect('transfer_market')


@login_required
@require_POST
def remove_from_scouting_list(request, scout_pk):
    scouted_player = get_object_or_404(ScoutingList, pk=scout_pk, team__captain=request.user)
    player_name = scouted_player.player.full_name
    scouted_player.delete()
    messages.success(request, f"Đã xóa {player_name} khỏi danh sách theo dõi.")
    return redirect(reverse('dashboard') + '?tab=scouting')    

# === lịch sử chuyển nhượng ===
def transfer_history_view(request):
    """
    Hiển thị trang lịch sử các vụ chuyển nhượng đã hoàn tất.
    """
    completed_transfers = PlayerTransfer.objects.filter(
        status=PlayerTransfer.Status.ACCEPTED
    ).select_related(
        'player', 'inviting_team', 'current_team'
    ).order_by('-updated_at')

    context = {
        'transfers': completed_transfers,
    }
    return render(request, 'tournaments/transfer_history.html', context)    

@login_required
@require_POST
def toggle_looking_for_club_view(request):
    """
    Xử lý việc cầu thủ bật/tắt trạng thái "Đang tìm CLB".
    """
    try:
        player_profile = request.user.player_profile
        player_profile.is_looking_for_club = not player_profile.is_looking_for_club
        player_profile.save(update_fields=['is_looking_for_club'])

        new_status_text = "BẬT" if player_profile.is_looking_for_club else "TẮT"
        messages.success(request, f"Đã {new_status_text} trạng thái 'Đang tìm CLB'.")

    except Player.DoesNotExist:
        messages.error(request, "Bạn không có hồ sơ cầu thủ để thực hiện hành động này.")
    except Exception as e:
        messages.error(request, f"An error occurred: {e}")

    return redirect(reverse('dashboard') + '?tab=player-profile')    


# Ghi lại thông tin lượt click baner tài trợ
def record_sponsor_click_view(request, pk):
    sponsorship = get_object_or_404(Sponsorship, pk=pk)

    # Ghi lại thông tin lượt click
    SponsorClick.objects.create(
        sponsorship=sponsorship,
        ip_address=request.META.get('REMOTE_ADDR'),
        user_agent=request.META.get('HTTP_USER_AGENT', '')
    )

    # Chuyển hướng người dùng đến trang của nhà tài trợ
    return redirect(sponsorship.website_url)


# === Mời Ntt ===
def sponsorship_proposal_view(request, pk):
    """
    Hiển thị trang hồ sơ mời tài trợ chuyên nghiệp cho một giải đấu.
    """
    # Lấy thông tin giải đấu dựa vào pk từ URL
    tournament = get_object_or_404(Tournament, pk=pk)

    # Lấy tất cả các gói tài trợ đã được tạo cho giải đấu này
    # sắp xếp theo thứ tự (order) đã định nghĩa
    sponsorship_packages = SponsorshipPackage.objects.filter(tournament=tournament).order_by('order')

    # Đếm số đội đã đăng ký và được duyệt
    registered_teams_count = TeamRegistration.objects.filter(
        tournament=tournament,
        payment_status='PAID'
    ).count()

    # Tạo context để gửi dữ liệu ra template
    context = {
        'tournament': tournament,
        'sponsorship_packages': sponsorship_packages,
        'registered_teams_count': registered_teams_count,
    }
    
    return render(request, 'tournaments/sponsorship_proposal.html', context)


# ===== VIEWS CHO HỆ THỐNG QUẢN LÝ TÀI CHÍNH =====

@login_required
def budget_dashboard(request, tournament_pk):
    """Dashboard quản lý tài chính giải đấu"""
    tournament = get_object_or_404(Tournament, pk=tournament_pk)
    
    # Kiểm tra quyền truy cập
    is_organizer = tournament.organization and tournament.organization.members.filter(pk=request.user.pk).exists()
    if not request.user.is_staff and not is_organizer:
        return HttpResponseForbidden("Bạn không có quyền truy cập trang này.")
    
    # Tạo hoặc lấy budget
    budget, created = TournamentBudget.objects.get_or_create(tournament=tournament)
    
    # Tự động cập nhật các khoản thu
    auto_update_revenue(budget)
    
    # Lấy dữ liệu
    revenue_items = budget.revenue_items.all()
    expense_items = budget.expense_items.all()
    history = budget.history.all()[:10]  # 10 bản ghi gần nhất
    
    # Tính toán tổng quan
    total_revenue = budget.get_total_revenue()
    total_expenses = budget.get_total_expenses()
    profit_loss = budget.get_profit_loss()
    budget_status = budget.get_budget_status()
    
    # Debug: In ra console để kiểm tra (có thể xóa sau khi test xong)
    # print(f"DEBUG: Total revenue items: {revenue_items.count()}")
    # print(f"DEBUG: Total expense items: {expense_items.count()}")
    # print(f"DEBUG: Total revenue: {total_revenue}")
    # print(f"DEBUG: Total expenses: {total_expenses}")
    # for item in revenue_items:
    #     print(f"DEBUG: Revenue item - {item.description}: {item.amount}")
    
    # Thống kê theo danh mục
    revenue_by_category = {}
    expense_by_category = {}
    
    for item in revenue_items:
        category = item.get_category_display()
        if category not in revenue_by_category:
            revenue_by_category[category] = 0
        revenue_by_category[category] += float(item.amount)
    
    for item in expense_items:
        category = item.get_category_display()
        if category not in expense_by_category:
            expense_by_category[category] = 0
        expense_by_category[category] += float(item.amount)
    
    # Thống kê đội
    paid_teams_count = tournament.registrations.filter(payment_status='PAID').count()
    total_teams_count = tournament.registrations.count()
    
    context = {
        'tournament': tournament,
        'budget': budget,
        'revenue_items': revenue_items,
        'expense_items': expense_items,
        'history': history,
        'total_revenue': total_revenue,
        'total_expenses': total_expenses,
        'profit_loss': profit_loss,
        'budget_status': budget_status,
        'revenue_by_category': revenue_by_category,
        'expense_by_category': expense_by_category,
        'is_organizer': is_organizer,
        'paid_teams_count': paid_teams_count,
        'total_teams_count': total_teams_count,
    }
    
    return render(request, 'tournaments/budget_dashboard.html', context)


@login_required
def budget_setup(request, tournament_pk):
    """Thiết lập ngân sách ban đầu"""
    tournament = get_object_or_404(Tournament, pk=tournament_pk)
    
    # Kiểm tra quyền truy cập
    is_organizer = tournament.organization and tournament.organization.members.filter(pk=request.user.pk).exists()
    if not request.user.is_staff and not is_organizer:
        return HttpResponseForbidden("Bạn không có quyền truy cập trang này.")
    
    budget, created = TournamentBudget.objects.get_or_create(tournament=tournament)
    
    if request.method == 'POST':
        form = TournamentBudgetForm(request.POST, instance=budget)
        if form.is_valid():
            form.save()
            # Ghi lịch sử
            BudgetHistory.objects.create(
                budget=budget,
                action='UPDATE_BUDGET',
                description=f'Cập nhật ngân sách ban đầu thành {budget.initial_budget:,} VNĐ',
                amount=budget.initial_budget,
                user=request.user
            )
            messages.success(request, "Ngân sách đã được cập nhật thành công!")
            return redirect('budget_dashboard', tournament_pk=tournament.pk)
    else:
        form = TournamentBudgetForm(instance=budget)
    
    context = {
        'tournament': tournament,
        'budget': budget,
        'form': form,
    }
    
    return render(request, 'tournaments/budget_setup.html', context)


@login_required
def add_revenue(request, tournament_pk):
    """Thêm khoản thu"""
    tournament = get_object_or_404(Tournament, pk=tournament_pk)
    
    # Kiểm tra quyền truy cập
    is_organizer = tournament.organization and tournament.organization.members.filter(pk=request.user.pk).exists()
    if not request.user.is_staff and not is_organizer:
        return HttpResponseForbidden("Bạn không có quyền truy cập trang này.")
    
    budget, created = TournamentBudget.objects.get_or_create(tournament=tournament)
    
    if request.method == 'POST':
        form = RevenueItemForm(request.POST)
        if form.is_valid():
            revenue_item = form.save(commit=False)
            revenue_item.budget = budget
            revenue_item.save()
            
            # Ghi lịch sử
            BudgetHistory.objects.create(
                budget=budget,
                action='ADD_REVENUE',
                description=f'Thêm khoản thu: {revenue_item.description}',
                amount=revenue_item.amount,
                user=request.user
            )
            
            messages.success(request, "Khoản thu đã được thêm thành công!")
            return redirect('budget_dashboard', tournament_pk=tournament.pk)
    else:
        form = RevenueItemForm()
    
    context = {
        'tournament': tournament,
        'budget': budget,
        'form': form,
    }
    
    return render(request, 'tournaments/add_revenue.html', context)


@login_required
def add_expense(request, tournament_pk):
    """Thêm khoản chi"""
    tournament = get_object_or_404(Tournament, pk=tournament_pk)
    
    # Kiểm tra quyền truy cập
    is_organizer = tournament.organization and tournament.organization.members.filter(pk=request.user.pk).exists()
    if not request.user.is_staff and not is_organizer:
        return HttpResponseForbidden("Bạn không có quyền truy cập trang này.")
    
    budget, created = TournamentBudget.objects.get_or_create(tournament=tournament)
    
    if request.method == 'POST':
        form = ExpenseItemForm(request.POST, request.FILES)
        if form.is_valid():
            expense_item = form.save(commit=False)
            expense_item.budget = budget
            expense_item.save()
            
            # Ghi lịch sử
            BudgetHistory.objects.create(
                budget=budget,
                action='ADD_EXPENSE',
                description=f'Thêm khoản chi: {expense_item.description}',
                amount=expense_item.amount,
                user=request.user
            )
            
            messages.success(request, "Khoản chi đã được thêm thành công!")
            return redirect('budget_dashboard', tournament_pk=tournament.pk)
    else:
        form = ExpenseItemForm()
    
    context = {
        'tournament': tournament,
        'budget': budget,
        'form': form,
    }
    
    return render(request, 'tournaments/add_expense.html', context)


@login_required
def quick_add_budget_item(request, tournament_pk):
    """Thêm nhanh khoản thu/chi"""
    tournament = get_object_or_404(Tournament, pk=tournament_pk)
    
    # Kiểm tra quyền truy cập
    is_organizer = tournament.organization and tournament.organization.members.filter(pk=request.user.pk).exists()
    if not request.user.is_staff and not is_organizer:
        return HttpResponseForbidden("Bạn không có quyền truy cập trang này.")
    
    budget, created = TournamentBudget.objects.get_or_create(tournament=tournament)
    
    if request.method == 'POST':
        form = BudgetQuickAddForm(request.POST)
        if form.is_valid():
            item_type = form.cleaned_data['type']
            description = form.cleaned_data['description']
            amount = form.cleaned_data['amount']
            date = form.cleaned_data['date']
            
            if item_type == 'revenue':
                revenue_item = RevenueItem.objects.create(
                    budget=budget,
                    category='OTHER',
                    description=description,
                    amount=amount,
                    date=date
                )
                action = 'ADD_REVENUE'
            else:
                expense_item = ExpenseItem.objects.create(
                    budget=budget,
                    category='OTHER',
                    description=description,
                    amount=amount,
                    date=date
                )
                action = 'ADD_EXPENSE'
            
            # Ghi lịch sử
            BudgetHistory.objects.create(
                budget=budget,
                action=action,
                description=f'Thêm nhanh: {description}',
                amount=amount,
                user=request.user
            )
            
            messages.success(request, f"Đã thêm {item_type} thành công!")
            return redirect('budget_dashboard', tournament_pk=tournament.pk)
    else:
        form = BudgetQuickAddForm()
    
    context = {
        'tournament': tournament,
        'budget': budget,
        'form': form,
    }
    
    return render(request, 'tournaments/quick_add_budget.html', context)


def auto_update_revenue(budget):
    """Tự động cập nhật các khoản thu từ dữ liệu giải đấu"""
    tournament = budget.tournament
    
    # 1. Tính phí đăng ký đội
    paid_teams = tournament.registrations.filter(payment_status='PAID').count()
    
    if paid_teams > 0:
        # Sử dụng phí đăng ký từ tournament
        team_fee = tournament.registration_fee
        total_team_fees = paid_teams * team_fee
        
        # Kiểm tra xem đã có khoản thu này chưa
        existing_fee = budget.revenue_items.filter(
            category='TEAM_FEES',
            is_auto_calculated=True
        ).first()
        
        if existing_fee:
            if existing_fee.amount != total_team_fees:
                existing_fee.amount = total_team_fees
                existing_fee.save()
        else:
            RevenueItem.objects.create(
                budget=budget,
                category='TEAM_FEES',
                description=f'Phí đăng ký {paid_teams} đội',
                amount=total_team_fees,
                date=tournament.start_date,
                is_auto_calculated=True
            )
    
    # 2. Tính tiền phạt từ thẻ
    yellow_cards = Card.objects.filter(match__tournament=tournament, card_type='YELLOW').count()
    red_cards = Card.objects.filter(match__tournament=tournament, card_type='RED').count()
    
    if yellow_cards > 0 or red_cards > 0:
        yellow_fine = 50000  # 50k/thẻ vàng
        red_fine = 100000    # 100k/thẻ đỏ
        total_penalties = (yellow_cards * yellow_fine) + (red_cards * red_fine)
        
        # Kiểm tra xem đã có khoản thu này chưa
        existing_penalty = budget.revenue_items.filter(
            category='PENALTIES',
            is_auto_calculated=True
        ).first()
        
        if existing_penalty:
            if existing_penalty.amount != total_penalties:
                existing_penalty.amount = total_penalties
                existing_penalty.description = f'Tiền phạt: {yellow_cards} thẻ vàng, {red_cards} thẻ đỏ'
                existing_penalty.save()
        else:
            RevenueItem.objects.create(
                budget=budget,
                category='PENALTIES',
                description=f'Tiền phạt: {yellow_cards} thẻ vàng, {red_cards} thẻ đỏ',
                amount=total_penalties,
                date=tournament.start_date,
                is_auto_calculated=True
            )
    
    # 3. Tính tài trợ
    total_sponsorship = tournament.sponsorships.filter(is_active=True).aggregate(
        total=Sum('package__price')
    )['total'] or 0
    
    if total_sponsorship > 0:
        existing_sponsorship = budget.revenue_items.filter(
            category='SPONSORSHIP',
            is_auto_calculated=True
        ).first()
        
        if existing_sponsorship:
            if existing_sponsorship.amount != total_sponsorship:
                existing_sponsorship.amount = total_sponsorship
                existing_sponsorship.save()
        else:
            RevenueItem.objects.create(
                budget=budget,
                category='SPONSORSHIP',
                description='Tài trợ từ các nhà tài trợ',
                amount=total_sponsorship,
                date=tournament.start_date,
                is_auto_calculated=True
            )


@login_required
@require_POST
def delete_budget_item(request, tournament_pk, item_type, item_id):
    """Xóa khoản thu hoặc chi"""
    tournament = get_object_or_404(Tournament, pk=tournament_pk)
    
    # Kiểm tra quyền truy cập
    is_organizer = tournament.organization and tournament.organization.members.filter(pk=request.user.pk).exists()
    if not request.user.is_staff and not is_organizer:
        return HttpResponseForbidden("Bạn không có quyền truy cập trang này.")
    
    budget, created = TournamentBudget.objects.get_or_create(tournament=tournament)
    
    try:
        if item_type == 'revenue':
            item = get_object_or_404(RevenueItem, pk=item_id, budget=budget)
            # Không cho phép xóa các khoản tự động tính
            if item.is_auto_calculated:
                messages.error(request, "Không thể xóa khoản thu tự động tính!")
                return redirect('budget_dashboard', tournament_pk=tournament.pk)
            
            # Ghi lịch sử
            BudgetHistory.objects.create(
                budget=budget,
                action='DELETE_REVENUE',
                description=f'Xóa khoản thu: {item.description}',
                amount=item.amount,
                user=request.user
            )
            
            item.delete()
            messages.success(request, "Khoản thu đã được xóa thành công!")
            
        elif item_type == 'expense':
            item = get_object_or_404(ExpenseItem, pk=item_id, budget=budget)
            
            # Ghi lịch sử
            BudgetHistory.objects.create(
                budget=budget,
                action='DELETE_EXPENSE',
                description=f'Xóa khoản chi: {item.description}',
                amount=item.amount,
                user=request.user
            )
            
            item.delete()
            messages.success(request, "Khoản chi đã được xóa thành công!")
            
        else:
            messages.error(request, "Loại khoản không hợp lệ!")
            
    except Exception as e:
        messages.error(request, f"Error occurred when deleting: {str(e)}")
    
    return redirect('budget_dashboard', tournament_pk=tournament.pk)


@login_required
def refresh_budget_auto(request, tournament_pk):
    """Cập nhật lại các khoản thu tự động"""
    tournament = get_object_or_404(Tournament, pk=tournament_pk)
    
    # Kiểm tra quyền truy cập
    is_organizer = tournament.organization and tournament.organization.members.filter(pk=request.user.pk).exists()
    if not request.user.is_staff and not is_organizer:
        return HttpResponseForbidden("Bạn không có quyền truy cập trang này.")
    
    budget, created = TournamentBudget.objects.get_or_create(tournament=tournament)
    
    # Gọi hàm cập nhật tự động
    auto_update_revenue(budget)
    
    messages.success(request, "Đã cập nhật các khoản thu tự động thành công!")
    return redirect('budget_dashboard', tournament_pk=tournament.pk)


# ===== VIEWS CHO HUẤN LUYỆN VIÊN =====

@login_required
@never_cache
def recruit_coach_list(request, team_pk):
    """Danh sách HLV để chiêu mộ"""
    from users.models import CoachProfile
    from .utils import user_can_manage_team
    
    team = get_object_or_404(Team, pk=team_pk)
    
    # Kiểm tra quyền
    if not user_can_manage_team(request.user, team):
        messages.error(request, "Bạn không có quyền chiêu mộ HLV cho đội này.")
        return redirect('team_detail', pk=team.pk)
    
    # Nếu đội đã có HLV
    if team.coach:
        messages.info(request, f"Đội đã có HLV {team.coach.full_name}. Bạn cần loại bỏ HLV hiện tại trước khi chiêu mộ HLV mới.")
        return redirect('team_detail', pk=team.pk)
    
    # Lấy danh sách HLV available
    coaches = CoachProfile.objects.filter(
        team__isnull=True,
        is_available=True
    ).select_related('user').order_by('-years_of_experience', '-created_at')
    
    # Filter theo khu vực nếu có
    region_filter = request.GET.get('region')
    if region_filter:
        coaches = coaches.filter(region=region_filter)
    
    # Filter theo kinh nghiệm
    exp_filter = request.GET.get('experience')
    if exp_filter:
        if exp_filter == '5+':
            coaches = coaches.filter(years_of_experience__gte=5)
        elif exp_filter == '10+':
            coaches = coaches.filter(years_of_experience__gte=10)
    
    # Tìm kiếm theo tên
    search_query = request.GET.get('q')
    if search_query:
        coaches = coaches.filter(
            Q(full_name__icontains=search_query) |
            Q(coaching_license__icontains=search_query) |
            Q(specialization__icontains=search_query)
        )
    
    # Lấy danh sách lời mời đã gửi
    sent_offers = CoachRecruitment.objects.filter(
        team=team,
        status=CoachRecruitment.Status.PENDING
    ).values_list('coach_id', flat=True)
    
    context = {
        'team': team,
        'coaches': coaches,
        'sent_offers': list(sent_offers),
        'region_choices': [
            ('MIEN_BAC', 'Miền Bắc'),
            ('MIEN_TRUNG', 'Miền Trung'),
            ('MIEN_NAM', 'Miền Nam'),
        ],
        'current_region': region_filter,
        'current_exp': exp_filter,
        'search_query': search_query or '',
    }
    
    return render(request, 'tournaments/recruit_coach_list.html', context)


@login_required
@require_POST
def send_coach_recruitment(request, team_pk, coach_pk):
    """Gửi lời mời chiêu mộ HLV"""
    from users.models import CoachProfile
    from .utils import user_can_manage_team
    from .forms import CoachRecruitmentForm
    
    team = get_object_or_404(Team, pk=team_pk)
    coach = get_object_or_404(CoachProfile, pk=coach_pk)
    
    # Kiểm tra quyền
    if not user_can_manage_team(request.user, team):
        return JsonResponse({'success': False, 'error': 'Bạn không có quyền thực hiện hành động này.'}, status=403)
    
    # Kiểm tra đội đã có HLV chưa
    if team.coach:
        return JsonResponse({'success': False, 'error': 'Đội đã có HLV.'}, status=400)
    
    # Kiểm tra HLV còn available không
    if not coach.is_available or coach.team:
        return JsonResponse({'success': False, 'error': 'HLV này không còn available.'}, status=400)
    
    # Kiểm tra đã gửi lời mời chưa
    existing = CoachRecruitment.objects.filter(
        team=team,
        coach=coach,
        status=CoachRecruitment.Status.PENDING
    ).exists()
    
    if existing:
        return JsonResponse({'success': False, 'error': 'Bạn đã gửi lời mời cho HLV này rồi.'}, status=400)
    
    # Tạo lời mời
    form = CoachRecruitmentForm(request.POST)
    if form.is_valid():
        recruitment = form.save(commit=False)
        recruitment.team = team
        recruitment.coach = coach
        recruitment.save()
        
        # Tạo thông báo cho HLV
        Notification.objects.create(
            user=coach.user,
            title=f"Lời mời từ đội {team.name}",
            message=f"Đội {team.name} muốn chiêu mộ bạn làm HLV! Mức lương: {recruitment.salary_offer:,} VNĐ" if recruitment.salary_offer else f"Đội {team.name} muốn chiêu mộ bạn làm HLV!",
            notification_type=Notification.NotificationType.GENERIC,
            related_url=reverse('coach_recruitment_detail', args=[recruitment.pk])
        )
        
        messages.success(request, f"Đã gửi lời mời chiêu mộ đến HLV {coach.full_name}!")
        return JsonResponse({'success': True})
    
    return JsonResponse({'success': False, 'error': form.errors}, status=400)


@login_required
@never_cache
def coach_recruitment_detail(request, pk):
    """Chi tiết lời mời chiêu mộ"""
    recruitment = get_object_or_404(
        CoachRecruitment.objects.select_related('team', 'coach', 'coach__user', 'team__captain'),
        pk=pk
    )
    
    # Kiểm tra quyền xem
    is_coach = request.user == recruitment.coach.user
    is_captain = request.user == recruitment.team.captain or (recruitment.team.coach and request.user == recruitment.team.coach.user)
    
    if not is_coach and not is_captain:
        return HttpResponseForbidden("Bạn không có quyền xem trang này.")
    
    context = {
        'recruitment': recruitment,
        'is_coach': is_coach,
        'is_captain': is_captain,
    }
    
    return render(request, 'tournaments/coach_recruitment_detail.html', context)


@login_required
@require_POST
def respond_to_recruitment(request, pk, action):
    """HLV chấp nhận hoặc từ chối lời mời"""
    recruitment = get_object_or_404(CoachRecruitment, pk=pk)
    
    # Chỉ HLV mới có thể trả lời
    if request.user != recruitment.coach.user:
        return JsonResponse({'success': False, 'error': 'Bạn không có quyền thực hiện hành động này.'}, status=403)
    
    # Chỉ có thể trả lời khi đang PENDING
    if recruitment.status != CoachRecruitment.Status.PENDING:
        return JsonResponse({'success': False, 'error': 'Lời mời này đã được xử lý rồi.'}, status=400)
    
    if action == 'accept':
        # Kiểm tra coach vẫn còn available
        if recruitment.coach.team or not recruitment.coach.is_available:
            return JsonResponse({'success': False, 'error': 'Bạn đã có đội rồi.'}, status=400)
        
        # Kiểm tra team chưa có coach khác
        if recruitment.team.coach:
            return JsonResponse({'success': False, 'error': 'Đội này đã có HLV rồi.'}, status=400)
        
        # Chấp nhận lời mời
        recruitment.status = CoachRecruitment.Status.ACCEPTED
        recruitment.save()  # Lưu status của recruitment
        
        recruitment.team.coach = recruitment.coach
        recruitment.team.save()
        
        # Cập nhật coach profile
        recruitment.coach.team = recruitment.team
        recruitment.coach.is_available = False
        recruitment.coach.save()
        
        # Từ chối tất cả lời mời khác đang pending cho coach này
        CoachRecruitment.objects.filter(
            coach=recruitment.coach,
            status=CoachRecruitment.Status.PENDING
        ).exclude(pk=recruitment.pk).update(status=CoachRecruitment.Status.CANCELED)
        
        # Thông báo cho đội trưởng
        Notification.objects.create(
            user=recruitment.team.captain,
            title=f"HLV {recruitment.coach.full_name} đã chấp nhận",
            message=f"HLV {recruitment.coach.full_name} đã chấp nhận lời mời làm HLV cho đội {recruitment.team.name}!",
            notification_type=Notification.NotificationType.GENERIC,
            related_url=reverse('team_detail', args=[recruitment.team.pk])
        )
        
        messages.success(request, f"Bạn đã trở thành HLV của đội {recruitment.team.name}!")
        return JsonResponse({'success': True, 'redirect_url': reverse('team_detail', args=[recruitment.team.pk])})
    
    elif action == 'reject':
        recruitment.status = CoachRecruitment.Status.REJECTED
        recruitment.save()
        
        # Thông báo cho đội trưởng
        Notification.objects.create(
            user=recruitment.team.captain,
            title=f"HLV {recruitment.coach.full_name} đã từ chối",
            message=f"HLV {recruitment.coach.full_name} đã từ chối lời mời làm HLV cho đội {recruitment.team.name}.",
            notification_type=Notification.NotificationType.GENERIC,
            related_url=reverse('recruit_coach_list', args=[recruitment.team.pk])
        )
        
        messages.info(request, "Đã từ chối lời mời.")
        return JsonResponse({'success': True})
    
    return JsonResponse({'success': False, 'error': 'Action không hợp lệ.'}, status=400)


@login_required
@require_POST
def remove_coach_from_team(request, team_pk):
    """Đội trưởng loại bỏ HLV khỏi đội"""
    from .utils import user_can_manage_team
    
    team = get_object_or_404(Team, pk=team_pk)
    
    # Chỉ đội trưởng mới có thể loại bỏ HLV (không phải HLV tự loại bỏ mình)
    if request.user != team.captain:
        return JsonResponse({'success': False, 'error': 'Chỉ đội trưởng mới có thể loại bỏ HLV.'}, status=403)
    
    if not team.coach:
        return JsonResponse({'success': False, 'error': 'Đội không có HLV.'}, status=400)
    
    coach = team.coach
    
    # Loại bỏ HLV
    team.coach = None
    team.save()
    
    # Cập nhật coach profile
    coach.team = None
    coach.is_available = True  # Đánh dấu lại là available
    coach.save()
    
    # Thông báo cho HLV
    Notification.objects.create(
        user=coach.user,
        title=f"Đã rời khỏi đội {team.name}",
        message=f"Bạn đã được đội trưởng {team.captain.get_full_name() or team.captain.username} loại bỏ khỏi vị trí HLV của đội {team.name}.",
        notification_type=Notification.NotificationType.GENERIC
    )
    
    messages.success(request, f"Đã loại bỏ HLV {coach.full_name} khỏi đội.")
    return JsonResponse({'success': True})


@login_required
@never_cache
def coach_dashboard(request):
    """Dashboard cho HLV - xem các lời mời chiêu mộ"""
    from users.models import CoachProfile
    
    # Kiểm tra user có CoachProfile không
    if not hasattr(request.user, 'coach_profile'):
        messages.warning(request, "Bạn cần tạo hồ sơ Huấn luyện viên trước.")
        return redirect('create_coach_profile')
    
    coach_profile = request.user.coach_profile
    
    # Lấy các lời mời đang chờ
    pending_recruitments = CoachRecruitment.objects.filter(
        coach=coach_profile,
        status=CoachRecruitment.Status.PENDING
    ).select_related('team', 'team__captain').order_by('-created_at')
    
    # Lấy lịch sử lời mời
    history_recruitments = CoachRecruitment.objects.filter(
        coach=coach_profile
    ).exclude(
        status=CoachRecruitment.Status.PENDING
    ).select_related('team', 'team__captain').order_by('-updated_at')[:10]
    
    context = {
        'coach_profile': coach_profile,
        'pending_recruitments': pending_recruitments,
        'history_recruitments': history_recruitments,
    }
    
    return render(request, 'tournaments/coach_dashboard.html', context)

@login_required
def create_free_agent_player(request):
    """Tạo player profile độc lập cho user có vai trò PLAYER"""
    
    # Kiểm tra user có vai trò PLAYER không
    if not request.user.profile.roles.filter(id='PLAYER').exists():
        messages.error(request, "Bạn cần có vai trò Cầu thủ để tạo hồ sơ cầu thủ.")
        return redirect('dashboard')
    
    # Kiểm tra user đã có player_profile chưa
    if hasattr(request.user, 'player_profile') and request.user.player_profile:
        messages.info(request, "Bạn đã có hồ sơ cầu thủ.")
        return redirect('player_detail', pk=request.user.player_profile.pk)
    
    if request.method == 'POST':
        form = PlayerCreationForm(request.POST, request.FILES)
        if form.is_valid():
            player = form.save(commit=False)
            player.user = request.user
            player.team = None  # Free agent
            player.save()
            messages.success(request, f"Đã tạo thành công hồ sơ cầu thủ '{player.full_name}'!")
            return redirect('player_detail', pk=player.pk)
        else:
            messages.error(request, "Có lỗi xảy ra. Vui lòng kiểm tra lại thông tin.")
    else:
        form = PlayerCreationForm()
    
    context = {
        'form': form,
        'is_free_agent': True,
    }
    return render(request, 'tournaments/create_player_profile.html', context)


@login_required
@require_POST
def calculate_shop_discount(request, tournament_pk):
    """API tính toán giảm giá từ shop cart cho payment flow"""
    try:
        tournament = get_object_or_404(Tournament, pk=tournament_pk)
        
        # Lấy cart của user
        cart, created = Cart.objects.get_or_create(user=request.user)
        
        # Tính tổng giá trị cart
        cart_total = cart.total_price
        
        # Tính giảm giá từ tournament
        discount_amount = tournament.calculate_shop_discount(cart.items.all())
        final_fee = tournament.get_final_registration_fee(cart.items.all())
        
        return JsonResponse({
            'success': True,
            'cart_total': float(cart_total),
            'discount_percentage': float(tournament.shop_discount_percentage),
            'discount_amount': float(discount_amount),
            'original_fee': float(tournament.registration_fee),
            'final_fee': float(final_fee),
            'cart_items_count': cart.total_items,
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


@login_required
def payment_with_shop(request, pk):
    """Payment page với tích hợp shop cart"""
    registration = get_object_or_404(TeamRegistration, pk=pk)
    team = registration.team
    tournament = registration.tournament

    if request.user != team.captain:
        return redirect('home')

    # Lấy cart của user
    cart, created = Cart.objects.get_or_create(user=request.user)
    
    # Tính toán giảm giá
    cart_total = cart.total_price
    discount_amount = tournament.calculate_shop_discount(cart.items.all())
    final_fee = tournament.get_final_registration_fee(cart.items.all())

    if request.method == 'POST':
        form = PaymentProofForm(request.POST, request.FILES, instance=registration)
        if form.is_valid():
            reg = form.save(commit=False)
            reg.payment_status = 'PENDING'
            
            # Xử lý tích hợp shop
            use_shop_discount = form.cleaned_data.get('use_shop_discount', False)
            if use_shop_discount and tournament.shop_discount_percentage > 0:
                if cart_total > 0:
                    messages.info(request, f'Bạn đã sử dụng giảm giá từ shop ({tournament.shop_discount_percentage}%). Đơn hàng shop sẽ được xử lý riêng.')
                else:
                    messages.warning(request, 'Giỏ hàng của bạn đang trống. Vui lòng thêm sản phẩm vào giỏ hàng để được giảm giá.')
            
            reg.save()

            send_notification_email(
                subject=f"Xác nhận thanh toán mới từ đội {team.name}",
                template_name='tournaments/emails/new_payment_proof.html',
                context={'team': team, 'tournament': tournament, 'use_shop_discount': use_shop_discount, 'cart_total': cart_total},
                recipient_list=[settings.ADMIN_EMAIL]
            )

            if team.captain.email:
                send_notification_email(
                    subject=f"Đã nhận được hóa đơn thanh toán của đội {team.name}",
                    template_name='tournaments/emails/payment_pending_confirmation.html',
                    context={'team': team, 'tournament': tournament, 'use_shop_discount': use_shop_discount, 'cart_total': cart_total},
                    recipient_list=[team.captain.email]
                )

            messages.success(request, 'Đã tải lên hóa đơn thành công! Vui lòng chờ Ban tổ chức xác nhận.')

            return redirect('team_detail', pk=team.pk)
    else:
        form = PaymentProofForm(instance=registration)

    context = {
        'form': form,
        'team': team,
        'registration': registration,
        'cart': cart,
        'cart_total': cart_total,
        'discount_amount': discount_amount,
        'final_fee': final_fee,
    }
    return render(request, 'tournaments/payment_proof.html', context)