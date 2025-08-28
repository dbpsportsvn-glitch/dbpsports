# tournaments/views.py

from django.shortcuts import render, get_object_or_404, redirect
from .models import Tournament, Team, Player, Match, Lineup
from django.contrib.auth.decorators import login_required # Để yêu cầu đăng nhập
from .forms import TeamCreationForm, PlayerCreationForm # Sửa dòng này
from django.http import HttpResponseForbidden
from django.db import transaction
from django.urls import reverse
from django.db.models import Sum # Thêm import này

def home(request):
    # 2. Lấy tất cả các đối tượng Tournament từ database
    all_tournaments = Tournament.objects.all()
    
    # 3. Đóng gói dữ liệu để gửi ra template
    context = {
        'tournaments_list': all_tournaments,
    }
    
    # 4. Gửi dữ liệu qua biến 'context'
    return render(request, 'tournaments/home.html', context)

def livestream_view(request):
    return render(request, 'tournaments/livestream.html')

def shop_view(request):
    return render(request, 'tournaments/shop.html')

def tournament_detail(request, pk):
    tournament = get_object_or_404(Tournament, pk=pk)

    # Lấy tất cả các trận
    all_matches = tournament.matches.all().order_by('match_time')
    group_matches = all_matches.filter(match_round='GROUP')
    knockout_matches = all_matches.filter(match_round__in=['SEMI', 'FINAL']) # Lấy cả bán kết và chung kết

    # === TÍNH TOÁN CÁC THÔNG SỐ THỐNG KÊ ===
    total_teams = tournament.teams.count()
    total_players = Player.objects.filter(team__tournament=tournament).count()
    finished_matches = all_matches.filter(team1_score__isnull=False)
    total_goals = finished_matches.aggregate(total=Sum('team1_score') + Sum('team2_score'))['total'] or 0

    context = {
        'tournament': tournament,
        'group_matches': group_matches,
        'knockout_matches': knockout_matches,
        # Gửi các thông số ra template
        'total_teams': total_teams,
        'total_players': total_players,
        'total_goals': total_goals,
        'finished_matches_count': finished_matches.count(),
    }
    return render(request, 'tournaments/tournament_detail.html', context)    

    # Chuẩn bị riêng các trận Knock-out
    semi_final_matches = all_matches.filter(match_round='SEMI')
    final_match = all_matches.filter(match_round='FINAL').first() # Chỉ có 1 trận chung kết

    context = {
        'tournament': tournament,
        'group_matches': group_matches,
        # Gửi riêng các trận knock-out ra ngoài
        'semi_final_matches': semi_final_matches,
        'final_match': final_match,
    }
    return render(request, 'tournaments/tournament_detail.html', context)

def team_detail(request, pk):
    team = get_object_or_404(Team, pk=pk)

    # Xử lý form thêm cầu thủ
    if request.method == 'POST':
        # Chỉ đội trưởng mới có quyền thêm cầu thủ
        if request.user == team.captain:
            player_form = PlayerCreationForm(request.POST)
            if player_form.is_valid():
                player = player_form.save(commit=False)
                player.team = team # Gán cầu thủ vào đội này
                player.save()
                return redirect('team_detail', pk=team.pk) # Tải lại trang để xem cầu thủ mới

    # Tạo một form trống cho lần truy cập đầu tiên (GET)
    player_form = PlayerCreationForm()

    context = {
        'team': team,
        'player_form': player_form, # Gửi form vào template
    }
    return render(request, 'tournaments/team_detail.html', context) 

# tournaments/views.py
@login_required # Yêu cầu người dùng phải đăng nhập để truy cập view này
def create_team(request, tournament_pk):
    tournament = get_object_or_404(Tournament, pk=tournament_pk)
    if request.method == 'POST':
        form = TeamCreationForm(request.POST)
        if form.is_valid():
            team = form.save(commit=False)
            team.tournament = tournament # Gán đội vào giải đấu này
            team.captain = request.user   # Gán người dùng hiện tại làm đội trưởng
            team.save()
            # Sau khi tạo đội thành công, chuyển đến trang chi tiết của đội đó
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
        form = PlayerCreationForm(request.POST, instance=player)
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

    context = {
        "match": match,
        "captain_team": captain_team,
        "team1_lineup": team1_lineup,
        "team2_lineup": team2_lineup,
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
        with transaction.atomic():
            for player in team.players.all():
                status = request.POST.get(f"player_{player.pk}", "")
                if status:
                    Lineup.objects.update_or_create(
                        match=match, player=player,
                        defaults={"team": team, "status": status}
                    )
                else:
                    Lineup.objects.filter(match=match, player=player, team=team).delete()
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