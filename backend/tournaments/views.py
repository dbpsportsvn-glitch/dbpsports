# tournaments/views.py

from django.shortcuts import render, get_object_or_404, redirect
from .models import Tournament, Team, Player # Đảm bảo có Team và Player ở đây
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
    context = {
        'tournament': tournament
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