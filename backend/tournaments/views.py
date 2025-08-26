# tournaments/views.py

from django.shortcuts import render
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