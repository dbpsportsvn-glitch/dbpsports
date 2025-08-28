# tournaments/admin.py

from django.contrib import admin
from .models import Tournament, Team, Player, Match, Lineup
from django.utils.html import format_html

@admin.register(Tournament)
class TournamentAdmin(admin.ModelAdmin):
    list_display = ('name', 'start_date', 'end_date')
    search_fields = ('name',)

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
