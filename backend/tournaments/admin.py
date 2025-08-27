# tournaments/admin.py

from django.contrib import admin
from .models import Tournament, Team, Player # Thêm Team và Player vào đây

# Đăng ký các model
admin.site.register(Tournament)
admin.site.register(Team)
admin.site.register(Player)