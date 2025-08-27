# tournaments/views.py

from django.shortcuts import render, get_object_or_404
from .models import Tournament  # 1. Import "bản thiết kế" Tournament

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