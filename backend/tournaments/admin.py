# tournaments/admin.py

from django.contrib import admin
from .models import Tournament, Team, Player, Match # Thêm Match vào đây

# Đăng ký các model
admin.site.register(Tournament)
admin.site.register(Team)
admin.site.register(Player)
admin.site.register(Match) # Thêm dòng này