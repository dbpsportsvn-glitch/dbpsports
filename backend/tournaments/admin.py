# tournaments/admin.py

import random
from itertools import combinations
from django.utils import timezone
from django.contrib import messages
from django.contrib import admin
from django.utils.html import format_html
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.urls import reverse
from django.conf import settings

from .models import Tournament, Team, Player, Match, Lineup, Group, Goal, Card
from .utils import send_notification_email

# ===== Inlines =====

class GroupInline(admin.TabularInline):
    model = Group
    extra = 1

class PlayerInline(admin.TabularInline):
    model = Player
    extra = 0
    fields = ("full_name", "jersey_number", "position")
    ordering = ("jersey_number",)
    show_change_link = True

class LineupInline(admin.TabularInline):
    model = Lineup
    extra = 0
    fields = ("player", "team", "status")
    raw_id_fields = ("player",)
    readonly_fields = ("team",)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        match_id = request.resolver_match.kwargs.get('object_id')
        if db_field.name == "player" and match_id:
            try:
                match = Match.objects.get(pk=match_id)
                kwargs["queryset"] = Player.objects.filter(
                    Q(team=match.team1) | Q(team=match.team2)
                ).order_by("team__name", "jersey_number", "full_name")
            except Match.DoesNotExist:
                pass
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

class GoalInline(admin.TabularInline):
    model = Goal
    extra = 0
    readonly_fields = ("team",)
    raw_id_fields = ("player",)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        match_id = request.resolver_match.kwargs.get('object_id')
        if db_field.name == "player" and match_id:
            try:
                match = Match.objects.get(pk=match_id)
                kwargs["queryset"] = Player.objects.filter(
                    Q(team=match.team1) | Q(team=match.team2)
                ).order_by("team__name", "jersey_number", "full_name")
            except Match.DoesNotExist:
                pass
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

class CardInline(admin.TabularInline):
    model = Card
    extra = 0
    readonly_fields = ("team",)
    raw_id_fields = ("player",)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        match_id = request.resolver_match.kwargs.get('object_id')
        if db_field.name == "player" and match_id:
            try:
                match = Match.objects.get(pk=match_id)
                kwargs["queryset"] = Player.objects.filter(
                    Q(team=match.team1) | Q(team=match.team2)
                ).order_by("team__name", "jersey_number", "full_name")
            except Match.DoesNotExist:
                pass
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

# ===== Admins =====

@admin.register(Tournament)
class TournamentAdmin(admin.ModelAdmin):
    list_display = ("name", "status", "start_date", "end_date", "image", "view_details_link")
    list_filter = ("status",)
    search_fields = ("name",)
    list_editable = ("status",)
    date_hierarchy = "start_date"
    inlines = [GroupInline]
    list_per_page = 50
    actions = ['draw_groups', 'generate_group_stage_matches', 'generate_knockout_matches', 'generate_final_match']

    def view_details_link(self, obj):
        teams_url = reverse('admin:tournaments_team_changelist') + f'?tournament__id__exact={obj.pk}'
        matches_url = reverse('admin:tournaments_match_changelist') + f'?tournament__id__exact={obj.pk}'
        groups_url = reverse('admin:tournaments_group_changelist') + f'?tournament__id__exact={obj.pk}'
        return format_html('<a href="{}">Xem Đội</a> | <a href="{}">Xem Bảng</a> | <a href="{}">Xem Trận</a>',
                           teams_url, groups_url, matches_url)
    view_details_link.short_description = 'Quản lý Giải'

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

    @admin.action(description='Tạo lịch thi đấu vòng bảng')
    def generate_group_stage_matches(self, request, queryset):
        for tournament in queryset:
            if tournament.status != 'REGISTRATION_OPEN':
                for group in tournament.groups.all():
                    teams_in_group = list(group.teams.all())
                    for team1, team2 in combinations(teams_in_group, 2):
                        Match.objects.get_or_create(
                            tournament=tournament,
                            team1=team1,
                            team2=team2,
                            defaults={'match_time': timezone.now()}
                        )
                self.message_user(request, f"Đã tạo lịch thi đấu cho giải '{tournament.name}'.", messages.SUCCESS)
            else:
                self.message_user(request, f"Không thể tạo lịch cho giải '{tournament.name}' vì vẫn đang mở đăng ký.", messages.ERROR)

    @admin.action(description='Tạo cặp đấu Bán kết từ 2 bảng')
    def generate_knockout_matches(self, request, queryset):
        for tournament in queryset:
            groups = list(tournament.groups.all().order_by('name'))
            if len(groups) != 2:
                self.message_user(request, "Chức năng này hiện chỉ hỗ trợ 2 bảng đấu.", messages.ERROR)
                continue
            standings_A = groups[0].get_standings()
            standings_B = groups[1].get_standings()
            if len(standings_A) < 2 or len(standings_B) < 2:
                self.message_user(request, f"Không đủ đội trong các bảng của giải '{tournament.name}'.", messages.ERROR)
                continue
            winner_A, runner_up_A = standings_A[0]['team_obj'], standings_A[1]['team_obj']
            winner_B, runner_up_B = standings_B[0]['team_obj'], standings_B[1]['team_obj']
            Match.objects.get_or_create(tournament=tournament, match_round='SEMI', team1=winner_A, team2=runner_up_B, defaults={'match_time': timezone.now()})
            Match.objects.get_or_create(tournament=tournament, match_round='SEMI', team1=winner_B, team2=runner_up_A, defaults={'match_time': timezone.now()})
            self.message_user(request, f"Đã tạo các cặp đấu Bán kết cho giải '{tournament.name}'.", messages.SUCCESS)

    @admin.action(description='Tạo trận Chung kết từ Bán kết')
    def generate_final_match(self, request, queryset):
        for tournament in queryset:
            semi_finals = tournament.matches.filter(match_round='SEMI', team1_score__isnull=False, team2_score__isnull=False)
            if self._count_safe(semi_finals) != 2:
                self.message_user(request, "Cần có đủ 2 trận Bán kết đã có tỉ số.", messages.ERROR)
                continue
            winners = [m.team1 if m.team1_score > m.team2_score else m.team2 for m in semi_finals]
            if len(winners) == 2:
                Match.objects.get_or_create(tournament=tournament, match_round='FINAL', team1=winners[0], team2=winners[1], defaults={'match_time': timezone.now()})
                self.message_user(request, f"Đã tạo trận Chung kết cho giải '{tournament.name}'.", messages.SUCCESS)
            else:
                self.message_user(request, "Không thể xác định 2 đội thắng từ Bán kết.", messages.ERROR)

    @staticmethod
    def _count_safe(qs):
        try:
            return qs.count()
        except Exception:
            return len(list(qs))

@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ("name", "tournament", "group", "payment_status", "captain", "display_proof", "display_logo")
    list_filter = ("tournament", "group", "payment_status")
    search_fields = ("name", "tournament__name", "captain__username")
    list_editable = ("payment_status",)
    inlines = [PlayerInline]
    autocomplete_fields = ("group", "tournament", "captain")
    list_select_related = ("tournament", "group", "captain")
    list_per_page = 50

    def display_logo(self, obj):
        if obj.logo:
            return format_html(f'<img src="{obj.logo.url}" width="40" height="40" />')
        return "Chưa có Logo"
    display_logo.short_description = 'Logo'

    def display_proof(self, obj):
        if obj.payment_proof:
            return format_html(f'<a href="{obj.payment_proof.url}" target="_blank">Xem hóa đơn</a>')
        return "Chưa có"
    display_proof.short_description = 'Hóa đơn'

    def save_model(self, request, obj, form, change):
        old_obj = Team.objects.get(pk=obj.pk) if obj.pk else None
        super().save_model(request, obj, form, change)
        if old_obj and old_obj.payment_status != 'PAID' and obj.payment_status == 'PAID':
            captain_email = obj.captain.email
            if captain_email:
                send_notification_email(
                    subject=f"Xác nhận thanh toán thành công cho đội {obj.name}",
                    template_name='tournaments/emails/payment_confirmed.html',
                    context={'team': obj},
                    recipient_list=[captain_email]
                )

@admin.register(Player)
class PlayerAdmin(admin.ModelAdmin):
    list_display = ("full_name", "team", "jersey_number", "position", "display_avatar")
    list_filter = ("team__tournament", "team", "position")
    search_fields = ("full_name", "team__name")
    ordering = ("team", "jersey_number")
    autocomplete_fields = ("team",)
    list_select_related = ("team",)
    list_per_page = 50

    def display_avatar(self, obj):
        if obj.avatar:
            return format_html('<img src="{}" width="40" height="40" style="object-fit: cover; border-radius: 50%;" />', obj.avatar.url)
        return "Chưa có ảnh"
    display_avatar.short_description = 'Ảnh đại diện'

@admin.register(Match)
class MatchAdmin(admin.ModelAdmin):
    list_display = ("__str__", "tournament", "colored_round", "match_round", "match_time", "location", "team1_score", "team2_score", "referee")
    list_filter = ("tournament", "match_round")
    list_editable = ("team1_score", "team2_score")
    list_display_links = ("__str__", "match_time")
    search_fields = ("team1__name", "team2__name", "tournament__name")
    date_hierarchy = "match_time"
    inlines = [LineupInline, GoalInline, CardInline]
    autocomplete_fields = ("team1", "team2", "tournament")
    list_select_related = ("tournament", "team1", "team2")
    list_per_page = 50

    @admin.display(description='Vòng đấu', ordering='match_round')
    def colored_round(self, obj):
        if obj.match_round == 'GROUP':
            color, text = 'grey', 'Vòng bảng'
        elif obj.match_round == 'SEMI':
            color, text = 'orange', 'Bán kết'
        elif obj.match_round == 'FINAL':
            color, text = 'green', 'Chung kết'
        else:
            color, text = 'blue', obj.get_match_round_display()
        return format_html('<span style="color: {}; font-weight: bold;">{}</span>', color, text)

    def save_formset(self, request, form, formset, change):
        instances = formset.save(commit=False)
        try:
            for instance in instances:
                # Tự động gán team theo player
                if isinstance(instance, (Lineup, Goal, Card)) and getattr(instance, "player", None):
                    instance.team = instance.player.team
                instance.save()
            formset.save_m2m()
        except ValidationError as e:
            msg = "; ".join(getattr(e, "messages", [str(e)]))
            self.message_user(request, msg, level=messages.ERROR)

@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = ("name", "tournament")
    list_filter = ("tournament",)
    search_fields = ("name", "tournament__name")
    list_per_page = 50

@admin.register(Lineup)
class LineupAdmin(admin.ModelAdmin):
    list_display = ("player", "team", "match", "status")
    list_filter = ("match__tournament", "team", "status")
    search_fields = ("player__full_name", "match__team1__name", "match__team2__name")
    autocomplete_fields = ("match", "player", "team")
    list_select_related = ("match", "team", "player")
    list_per_page = 50

@admin.register(Goal)
class GoalAdmin(admin.ModelAdmin):
    list_display = ("match", "team", "player", "minute")
    list_filter = ("match__tournament", "team")
    search_fields = ("player__full_name",)
    autocomplete_fields = ("match", "player", "team")
    list_select_related = ("match", "team", "player")
    list_per_page = 50

@admin.register(Card)
class CardAdmin(admin.ModelAdmin):
    list_display = ("match", "team", "player", "card_type", "minute")
    list_filter = ("match__tournament", "team", "card_type")
    search_fields = ("player__full_name",)
    autocomplete_fields = ("match", "player", "team")
    list_select_related = ("match", "team", "player")
    list_per_page = 50
