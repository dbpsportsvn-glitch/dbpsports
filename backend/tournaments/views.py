# tournaments/views.py

from django.shortcuts import render, get_object_or_404, redirect
from .models import Tournament, Team, Player, Match, Lineup
from django.contrib.auth.decorators import login_required # Để yêu cầu đăng nhập
from .forms import TeamCreationForm, PlayerCreationForm # Sửa dòng này

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
    # Lấy tất cả các trận đấu thuộc giải đấu này, sắp xếp theo thời gian
    matches = tournament.matches.all().order_by('match_time')

    context = {
        'tournament': tournament,
        'matches': matches, # Thêm danh sách trận đấu vào context
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


def match_detail(request, pk):
    match = get_object_or_404(Match, pk=pk)

    # Xác định xem người dùng hiện tại có phải đội trưởng không
    captain_team = None
    if request.user.is_authenticated:
        if match.team1.captain == request.user:
            captain_team = match.team1
        elif match.team2.captain == request.user:
            captain_team = match.team2

    # Xử lý khi đội trưởng gửi đội hình (submit form)
    if request.method == 'POST' and captain_team:
        for player in captain_team.players.all():
            status = request.POST.get(f'player_{player.pk}')
            if status:
                # Dùng update_or_create để tạo mới hoặc cập nhật nếu đã tồn tại
                Lineup.objects.update_or_create(
                    match=match,
                    player=player,
                    defaults={'team': captain_team, 'status': status}
                )
        return redirect('match_detail', pk=match.pk)

    # Lấy đội hình đã được đăng ký để hiển thị
    team1_lineup = Lineup.objects.filter(match=match, team=match.team1)
    team2_lineup = Lineup.objects.filter(match=match, team=match.team2)

    context = {
        'match': match,
        'captain_team': captain_team,
        'team1_lineup': team1_lineup,
        'team2_lineup': team2_lineup,
    }
    return render(request, 'tournaments/match_detail.html', context)   

@login_required
def manage_lineup(request, match_pk, team_pk):
    match = get_object_or_404(Match, pk=match_pk)
    team = get_object_or_404(Team, pk=team_pk)

    # Kiểm tra quyền: chỉ đội trưởng của đội này mới được vào
    if request.user != team.captain:
        return redirect('home')

    if request.method == 'POST':
        for player in team.players.all():
            status = request.POST.get(f'player_{player.pk}')
            if status:
                Lineup.objects.update_or_create(
                    match=match,
                    player=player,
                    defaults={'team': team, 'status': status}
                )
        # Sau khi lưu, quay lại trang chi tiết trận đấu
        return redirect('match_detail', pk=match.pk)

    # Lấy thông tin đội hình đã có để hiển thị trạng thái đã chọn
    existing_lineup = {lineup.player.pk: lineup.status for lineup in Lineup.objects.filter(match=match, team=team)}

    context = {
        'match': match,
        'team': team,
        'existing_lineup': existing_lineup
    }
    return render(request, 'tournaments/manage_lineup.html', context)    

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