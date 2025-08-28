# tournaments/admin.py

from django.contrib import admin
from .models import Tournament, Team, Player, Match, Lineup, Group
from django.utils.html import format_html

# tournaments/admin.py
import random
from django.contrib import messages

@admin.register(Tournament)
class TournamentAdmin(admin.ModelAdmin):
    list_display = ('name', 'status', 'start_date', 'end_date')
    list_filter = ('status',)
    search_fields = ('name',)
    list_editable = ('status',)
    actions = ['draw_groups'] # Thêm action mới

    @admin.action(description='Bốc thăm chia bảng cho các giải đã chọn')
    def draw_groups(self, request, queryset):
        for tournament in queryset:
            teams = list(tournament.teams.all())
            groups = list(tournament.groups.all())

            if not groups:
                self.message_user(request, f"Giải '{tournament.name}' chưa có bảng đấu nào được tạo.", messages.ERROR)
                continue

            random.shuffle(teams)

            num_teams = len(teams)
            num_groups = len(groups)

            for i, team in enumerate(teams):
                group_index = i % num_groups
                team.group = groups[group_index]
                team.save()

            self.message_user(request, f"Đã bốc thăm chia bảng thành công cho giải '{tournament.name}'.", messages.SUCCESS)

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
    # Thêm dòng này để cho phép sửa nhanh
    list_editable = ('team1_score', 'team2_score',)

@admin.register(Lineup)
class LineupAdmin(admin.ModelAdmin):
    list_display = ('player', 'team', 'match', 'status')
    list_filter = ('match__tournament', 'team', 'status')

@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = ('name', 'tournament')
    list_filter = ('tournament',)    
