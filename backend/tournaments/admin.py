# tournaments/admin.py

from django.contrib import admin
from .models import Tournament, Team, Player, Match, Lineup, Group
from django.utils.html import format_html
from itertools import combinations
from django.utils import timezone 

# tournaments/admin.py
import random
from django.contrib import messages

# tournaments/admin.py

import random
from itertools import combinations # <-- Thêm dòng import này
from django.contrib import messages
from .models import Tournament, Team, Player, Match, Lineup, Group

@admin.register(Tournament)
class TournamentAdmin(admin.ModelAdmin):
    list_display = ('name', 'status', 'start_date', 'end_date')
    list_filter = ('status',)
    search_fields = ('name',)
    list_editable = ('status',)
    actions = ['draw_groups', 'generate_group_stage_matches'] # <-- Thêm action mới vào đây

    @admin.action(description='Bốc thăm chia bảng cho các giải đã chọn')
    def draw_groups(self, request, queryset):
        for tournament in queryset:
            teams = list(tournament.teams.all())
            groups = list(tournament.groups.all())
            if not groups:
                self.message_user(request, f"Giải '{tournament.name}' chưa có bảng đấu.", messages.ERROR)
                continue
            random.shuffle(teams)
            for i, team in enumerate(teams):
                team.group = groups[i % len(groups)]
                team.save()
            self.message_user(request, f"Đã bốc thăm thành công cho giải '{tournament.name}'.", messages.SUCCESS)

    # === THÊM TOÀN BỘ PHƯƠNG THỨC MỚI NÀY VÀO ===
    @admin.action(description='Tạo lịch thi đấu vòng bảng')
    def generate_group_stage_matches(self, request, queryset):
        for tournament in queryset:
            if tournament.status != 'REGISTRATION_OPEN':
                for group in tournament.groups.all():
                    teams_in_group = list(group.teams.all())
                    
                    for team1, team2 in combinations(teams_in_group, 2):
                        # Sửa lại đoạn code dưới đây
                        match, created = Match.objects.get_or_create(
                            tournament=tournament,
                            team1=team1,
                            team2=team2,
                            # Gán giá trị mặc định cho các trường bắt buộc
                            defaults={'match_time': timezone.now()}
                        )
                self.message_user(request, f"Đã tạo lịch thi đấu cho giải '{tournament.name}'.", messages.SUCCESS)
            else:
                self.message_user(request, f"Không thể tạo lịch cho giải '{tournament.name}' vì vẫn đang mở đăng ký.", messages.ERROR)


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ('name', 'tournament', 'captain', 'display_logo')
    list_filter = ('tournament',)
    search_fields = ('captain__username', 'name', 'coach_name',)

    def display_logo(self, obj):
        if obj.logo:
            return format_html(f'<img src="{obj.logo.url}" width="40" height="40" />')
        return "No Logo"
    display_logo.short_description = 'Logo'

@admin.register(Player)
class PlayerAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'team', 'jersey_number', 'position')
    list_filter = ('team__tournament', 'team')
    search_fields = ('full_name',)

@admin.register(Match)
class MatchAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'tournament', 'match_time', 'team1_score', 'team2_score', 'location')
    list_filter = ('tournament',)
    list_editable = ('team1_score', 'team2_score',)
    list_display_links = ('__str__', 'match_time',) # <-- Thêm dòng này

@admin.register(Lineup)
class LineupAdmin(admin.ModelAdmin):
    list_display = ('player', 'team', 'match', 'status')
    list_filter = ('match__tournament', 'team', 'status')

@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = ('name', 'tournament')
    list_filter = ('tournament',)    
