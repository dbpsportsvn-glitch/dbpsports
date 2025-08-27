# tournaments/admin.py

from django.contrib import admin
from .models import Tournament, Team, Player, Match, Lineup

@admin.register(Tournament)
class TournamentAdmin(admin.ModelAdmin):
    list_display = ('name', 'start_date', 'end_date')
    search_fields = ('name',)

@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ('name', 'tournament', 'captain', 'coach_name')
    list_filter = ('tournament',)
    # Đưa trường tìm được (username) lên trước, sau đó thêm các trường khác
    search_fields = ('captain__username', 'name', 'coach_name',)

@admin.register(Player)
class PlayerAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'team', 'jersey_number', 'position')
    list_filter = ('team__tournament', 'team')
    search_fields = ('full_name',)

@admin.register(Match)
class MatchAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'tournament', 'match_time', 'location')
    list_filter = ('tournament',)

@admin.register(Lineup)
class LineupAdmin(admin.ModelAdmin):
    list_display = ('player', 'team', 'match', 'status')
    list_filter = ('match__tournament', 'team', 'status')
