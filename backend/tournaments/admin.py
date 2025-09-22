# tournaments/admin.py

import random
from itertools import combinations
from django.utils import timezone
from django.contrib import messages
from django.contrib import admin
from django.contrib.admin import ModelAdmin
from django.utils.html import format_html
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.urls import reverse
from django.conf import settings
from django.db.models import Count
from .models import Tournament, Team, Player, Match, Lineup, Group, Goal, Card, HomeBanner, Announcement, TournamentPhoto
from .utils import send_notification_email

# ===== CÁC Hàm Cho Bộ lọc (Giữ nguyên) =====

class MatchResultFilter(admin.SimpleListFilter):
    title = 'tình trạng kết quả'
    parameter_name = 'has_result'

    def lookups(self, request, model_admin):
        return (('yes', 'Đã có kết quả'), ('no', 'Chưa đá'),)

    def queryset(self, request, queryset):
        if self.value() == 'yes':
            return queryset.filter(team1_score__isnull=False, team2_score__isnull=False)
        if self.value() == 'no':
            return queryset.filter(team1_score__isnull=True, team2_score__isnull=True)

class PlayerCountFilter(admin.SimpleListFilter):
    title = 'tình trạng đội hình'
    parameter_name = 'player_count'

    def lookups(self, request, model_admin):
        return (('yes', 'Đã có cầu thủ'), ('no', 'Chưa có cầu thủ'),)

    def queryset(self, request, queryset):
        queryset = queryset.annotate(player_count=Count('players'))
        if self.value() == 'yes':
            return queryset.filter(player_count__gt=0)
        if self.value() == 'no':
            return queryset.filter(player_count=0)

# ===== Inlines (Giữ nguyên) =====
class GroupInline(admin.TabularInline): model = Group; extra = 1
class PlayerInline(admin.TabularInline): model = Player; extra = 0; fields = ("full_name", "jersey_number", "position"); ordering = ("jersey_number",); show_change_link = True

class LineupInline(admin.TabularInline):
    model = Lineup; extra = 0; fields = ("player", "team", "status"); raw_id_fields = ("player",); readonly_fields = ("team",)
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        match_id = request.resolver_match.kwargs.get('object_id')
        if db_field.name == "player" and match_id:
            try:
                match = Match.objects.get(pk=match_id)
                kwargs["queryset"] = Player.objects.filter(Q(team=match.team1) | Q(team=match.team2)).order_by("team__name", "jersey_number", "full_name")
            except Match.DoesNotExist: pass
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

class GoalInline(admin.TabularInline):
    model = Goal; extra = 0; readonly_fields = ("team",); raw_id_fields = ("player",)
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        match_id = request.resolver_match.kwargs.get('object_id')
        if db_field.name == "player" and match_id:
            try:
                match = Match.objects.get(pk=match_id)
                kwargs["queryset"] = Player.objects.filter(Q(team=match.team1) | Q(team=match.team2)).order_by("team__name", "jersey_number", "full_name")
            except Match.DoesNotExist: pass
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

class CardInline(admin.TabularInline):
    model = Card; extra = 0; readonly_fields = ("team",); raw_id_fields = ("player",)
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        match_id = request.resolver_match.kwargs.get('object_id')
        if db_field.name == "player" and match_id:
            try:
                match = Match.objects.get(pk=match_id)
                kwargs["queryset"] = Player.objects.filter(Q(team=match.team1) | Q(team=match.team2)).order_by("team__name", "jersey_number", "full_name")
            except Match.DoesNotExist: pass
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

class TournamentPhotoInline(admin.TabularInline):
    model = TournamentPhoto; extra = 1; readonly_fields = ('image_preview',); fields = ('image', 'image_preview', 'caption')
    @admin.display(description='Xem trước')
    def image_preview(self, obj):
        if obj.image: return format_html('<img src="{}" style="max-height: 100px; max-width: 150px;" />', obj.image.url)
        return "Chưa có ảnh"

# ===== Admins =====
@admin.register(Tournament)
class TournamentAdmin(admin.ModelAdmin):
    list_display = ("name", "status", "start_date", "generate_schedule_link", "draw_groups_link", "bulk_upload_link", "view_details_link")
    list_filter = ("status",); search_fields = ("name",); list_editable = ("status",); date_hierarchy = "start_date"
    inlines = [GroupInline, TournamentPhotoInline]; list_per_page = 50
    actions = ['auto_create_next_knockout_round', 'create_semi_finals_with_best_runner_ups']

    @admin.display(description='Tải ảnh hàng loạt')
    def bulk_upload_link(self, obj):
        url = reverse('tournament_bulk_upload', args=[obj.pk]); return format_html('<a class="button" href="{}" target="_blank">Tải ảnh</a>', url)
    def generate_schedule_link(self, obj):
        if obj.groups.exists() and not obj.matches.exists(): url = reverse('generate_schedule', args=[obj.pk]); return format_html('<a class="button" href="{}" target="_blank">Xếp Lịch</a>', url)
        return "—"
    generate_schedule_link.short_description = 'Xếp Lịch Thi Đấu'
    def draw_groups_link(self, obj):
        if obj.teams.filter(payment_status='PAID', group__isnull=True).exists(): url = reverse('draw_groups', args=[obj.pk]); return format_html('<a class="button" href="{}" target="_blank">Bốc thăm</a>', url)
        return "—"
    draw_groups_link.short_description = 'Bốc thăm Chia bảng'
    def view_details_link(self, obj):
        teams_url = reverse('admin:tournaments_team_changelist') + f'?tournament__id__exact={obj.pk}'
        matches_url = reverse('admin:tournaments_match_changelist') + f'?tournament__id__exact={obj.pk}'
        groups_url = reverse('admin:tournaments_group_changelist') + f'?tournament__id__exact={obj.pk}'
        return format_html('<a href="{}">Xem Đội</a> | <a href="{}">Xem Bảng</a> | <a href="{}">Xem Trận</a>', teams_url, groups_url, matches_url)
    view_details_link.short_description = 'Quản lý Giải'

    @admin.action(description='Tự động tạo vòng Knockout tiếp theo')
    def auto_create_next_knockout_round(self, request, queryset):
        for tournament in queryset:
            if not tournament.matches.filter(match_round__in=['QUARTER', 'SEMI', 'FINAL']).exists():
                groups = list(tournament.groups.order_by('name'))
                if not groups: self.message_user(request, f"Giải '{tournament.name}' chưa có bảng đấu.", messages.ERROR); continue
                qualified_teams = []
                for group in groups:
                    standings = group.get_standings()
                    if len(standings) < 2: self.message_user(request, f"Bảng '{group.name}' của giải '{tournament.name}' chưa đủ 2 đội.", messages.ERROR); continue
                    qualified_teams.extend([s['team_obj'] for s in standings[:2]])
                if len(qualified_teams) == 8:
                    tournament.matches.filter(match_round='QUARTER').delete()
                    pairings = [(qualified_teams[0], qualified_teams[3]), (qualified_teams[2], qualified_teams[1]), (qualified_teams[4], qualified_teams[7]), (qualified_teams[6], qualified_teams[5])]
                    for t1, t2 in pairings: Match.objects.create(tournament=tournament, match_round='QUARTER', team1=t1, team2=t2, match_time=timezone.now())
                    self.message_user(request, f"Đã tạo 4 cặp đấu Tứ kết cho giải '{tournament.name}'.", messages.SUCCESS)
                elif len(qualified_teams) == 4:
                    tournament.matches.filter(match_round='SEMI').delete()
                    pairings = [(qualified_teams[0], qualified_teams[3]), (qualified_teams[2], qualified_teams[1])]
                    for t1, t2 in pairings: Match.objects.create(tournament=tournament, match_round='SEMI', team1=t1, team2=t2, match_time=timezone.now())
                    self.message_user(request, f"Đã tạo 2 cặp đấu Bán kết cho giải '{tournament.name}'.", messages.SUCCESS)
                else: self.message_user(request, f"Không đủ số đội (cần 4 hoặc 8) để tạo knockout cho giải '{tournament.name}'.", messages.WARNING)
                continue
            quarter_finals = tournament.matches.filter(match_round='QUARTER')
            if quarter_finals.exists() and not tournament.matches.filter(match_round__in=['SEMI', 'FINAL']).exists():
                finished_qf = quarter_finals.filter(team1_score__isnull=False, team2_score__isnull=False)
                if finished_qf.count() != 4: self.message_user(request, f"Cần cập nhật tỉ số 4 trận Tứ kết của giải '{tournament.name}'.", messages.WARNING); continue
                winners = [m.winner for m in finished_qf if m.winner]
                if len(winners) == 4:
                    tournament.matches.filter(match_round='SEMI').delete()
                    Match.objects.create(tournament=tournament, match_round='SEMI', team1=winners[0], team2=winners[1], match_time=timezone.now())
                    Match.objects.create(tournament=tournament, match_round='SEMI', team1=winners[2], team2=winners[3], match_time=timezone.now())
                    self.message_user(request, f"Đã tạo 2 cặp Bán kết từ Tứ kết cho giải '{tournament.name}'.", messages.SUCCESS)
                continue
            semi_finals = tournament.matches.filter(match_round='SEMI')
            if semi_finals.exists() and not tournament.matches.filter(match_round__in=['FINAL', 'THIRD_PLACE']).exists():
                finished_sf = semi_finals.filter(team1_score__isnull=False, team2_score__isnull=False)
                if finished_sf.count() != 2: self.message_user(request, f"Cần cập nhật tỉ số 2 trận Bán kết của giải '{tournament.name}'.", messages.WARNING); continue
                winners = [m.winner for m in finished_sf if m.winner]
                losers = [m.loser for m in finished_sf if m.loser]
                if len(winners) == 2 and len(losers) == 2:
                    tournament.matches.filter(match_round__in=['FINAL', 'THIRD_PLACE']).delete()
                    Match.objects.create(tournament=tournament, match_round='FINAL', team1=winners[0], team2=winners[1], match_time=timezone.now())
                    Match.objects.create(tournament=tournament, match_round='THIRD_PLACE', team1=losers[0], team2=losers[1], match_time=timezone.now())
                    self.message_user(request, f"Đã tạo trận Chung kết và Tranh hạng ba cho giải '{tournament.name}'.", messages.SUCCESS)
                continue

    # === BẮT ĐẦU ACTION MỚI ĐÃ ĐƯỢC NÂNG CẤP ===
    @admin.action(description='Tạo Bán kết (chọn đội nhì bảng tốt nhất)')
    def create_semi_finals_with_best_runner_ups(self, request, queryset):
        for tournament in queryset:
            groups = list(tournament.groups.order_by('name'))
            if len(groups) < 2:
                self.message_user(request, f"Giải '{tournament.name}' cần có ít nhất 2 bảng đấu.", messages.ERROR)
                continue

            group_winners = []
            second_place_teams_with_stats = []

            for group in groups:
                standings = group.get_standings()
                if not standings:
                    self.message_user(request, f"Bảng '{group.name}' chưa có đội nào.", messages.ERROR)
                    return # Dừng lại nếu có lỗi
                
                # Lưu đội nhất bảng kèm thành tích để xếp hạng sau
                group_winners.append(standings[0])
                
                # Lưu đội nhì bảng nếu có
                if len(standings) > 1:
                    second_place_teams_with_stats.append(standings[1])
            
            # Sắp xếp các đội nhì bảng theo thành tích
            second_place_teams_with_stats.sort(key=lambda x: (x['points'], x['gd'], x['gf']), reverse=True)
            
            # Xác định số đội nhì bảng cần lấy
            num_runner_ups_needed = 4 - len(group_winners)
            if num_runner_ups_needed < 0: num_runner_ups_needed = 0 # Trường hợp có hơn 4 bảng

            if len(second_place_teams_with_stats) < num_runner_ups_needed:
                self.message_user(request, f"Không đủ số đội nhì bảng để tạo Bán kết cho giải '{tournament.name}'.", messages.ERROR)
                continue

            # Lấy các đội nhì bảng xuất sắc nhất
            best_runner_ups = second_place_teams_with_stats[:num_runner_ups_needed]
            
            # Gộp danh sách các đội vào bán kết
            semi_finalists_with_stats = group_winners + best_runner_ups

            if len(semi_finalists_with_stats) != 4:
                self.message_user(request, f"Không thể xác định được 4 đội vào Bán kết cho giải '{tournament.name}'.", messages.ERROR)
                continue
            
            # Sắp xếp 4 đội vào bán kết theo thành tích để chia cặp
            semi_finalists_with_stats.sort(key=lambda x: (x['points'], x['gd'], x['gf']), reverse=True)
            
            top_4_teams = [team_stats['team_obj'] for team_stats in semi_finalists_with_stats]

            # Chia cặp: 1 vs 4, 2 vs 3
            pairings = [(top_4_teams[0], top_4_teams[3]), (top_4_teams[1], top_4_teams[2])]

            tournament.matches.filter(match_round='SEMI').delete()
            for team1, team2 in pairings:
                Match.objects.create(tournament=tournament, match_round='SEMI', team1=team1, team2=team2, match_time=timezone.now())
            
            self.message_user(request, f"Đã tạo Bán kết thành công cho giải '{tournament.name}' từ các đội xuất sắc nhất.", messages.SUCCESS)

# === Các class Admin khác giữ nguyên không đổi ===
@admin.register(Team)
class TeamAdmin(ModelAdmin):
    list_display = ("name", "tournament", "group", "payment_status", "captain", "display_proof", "display_logo")
    list_filter = ("tournament", "group", "payment_status", PlayerCountFilter); search_fields = ("name", "tournament__name", "captain__username"); list_editable = ("payment_status",)
    inlines = [PlayerInline]; autocomplete_fields = ("group", "tournament", "captain"); list_select_related = ("tournament", "group", "captain"); list_per_page = 50; actions = ['approve_payments']
    @admin.action(description='Duyệt thanh toán cho các đội đã chọn')
    def approve_payments(self, request, queryset):
        updated_count = queryset.filter(payment_status='PENDING').update(payment_status='PAID')
        for team in queryset.filter(pk__in=queryset.values_list('pk', flat=True)):
            if team.captain.email: send_notification_email(subject=f"Xác nhận thanh toán thành công cho đội {team.name}", template_name='tournaments/emails/payment_confirmed.html', context={'team': team}, recipient_list=[team.captain.email])
        self.message_user(request, f'Đã duyệt thành công thanh toán cho {updated_count} đội.')
    def display_logo(self, obj):
        if obj.logo: return format_html(f'<img src="{obj.logo.url}" width="40" height="40" />')
        return "Chưa có Logo"
    display_logo.short_description = 'Logo'
    def display_proof(self, obj):
        if obj.payment_proof: return format_html(f'<a href="{obj.payment_proof.url}" target="_blank">Xem hóa đơn</a>')
        return "Chưa có"
    display_proof.short_description = 'Hóa đơn'
    def save_model(self, request, obj, form, change):
        old_obj = Team.objects.get(pk=obj.pk) if obj.pk else None
        super().save_model(request, obj, form, change)
        if old_obj and old_obj.payment_status != 'PAID' and obj.payment_status == 'PAID':
            if obj.captain.email: send_notification_email(subject=f"Xác nhận thanh toán thành công cho đội {obj.name}", template_name='tournaments/emails/payment_confirmed.html', context={'team': obj}, recipient_list=[obj.captain.email])

@admin.register(Player)
class PlayerAdmin(ModelAdmin):
    list_display = ("full_name", "link_to_team", "jersey_number", "position", "display_avatar"); list_filter = ("team__tournament", "position", "team"); search_fields = ("full_name", "team__name", "jersey_number"); list_editable = ("position",); ordering = ("team", "jersey_number"); autocomplete_fields = ("team",); list_select_related = ("team",); list_per_page = 50
    @admin.display(description='Đội', ordering='team__name')
    def link_to_team(self, obj):
        link = reverse("admin:tournaments_team_change", args=[obj.team.id]); return format_html('<a href="{}">{}</a>', link, obj.team.name)
    def display_avatar(self, obj):
        if obj.avatar: return format_html('<img src="{}" width="40" height="40" style="object-fit: cover; border-radius: 50%;" />', obj.avatar.url)
        return "Chưa có ảnh"
    display_avatar.short_description = 'Ảnh đại diện'

@admin.register(Match)
class MatchAdmin(ModelAdmin):
    list_display = ("__str__", "tournament", "colored_round", "display_match_time", "team1_score", "team2_score",); list_filter = ("tournament", "match_round", MatchResultFilter); search_fields = ("team1__name", "team2__name", "tournament__name"); list_editable = ("team1_score", "team2_score",); date_hierarchy = "match_time"; inlines = [LineupInline, GoalInline, CardInline]; autocomplete_fields = ("team1", "team2", "tournament"); list_select_related = ("tournament", "team1", "team2"); list_per_page = 50
    @admin.display(description='Thời gian thi đấu', ordering='match_time')
    def display_match_time(self, obj): return format_html("{}<br>{}", obj.match_time.strftime("%H:%M"), obj.match_time.strftime("%d-%m-%Y"))
    fieldsets = ((None, {'fields': ('tournament', 'match_round', ('team1', 'team2'))}), ('Kết quả & Lịch thi đấu', {'fields': (('team1_score', 'team2_score'), 'match_time', 'location', 'referee', 'commentator')}), ('Cài đặt Livestream', {'classes': ('collapse',), 'fields': ('livestream_url', 'ticker_text')}),)
    @admin.display(description='Vòng đấu', ordering='match_round')
    def colored_round(self, obj):
        if obj.match_round == 'GROUP': color, text = 'grey', 'Vòng bảng'
        elif obj.match_round == 'QUARTER': color, text = '#7B68EE', 'Tứ kết'
        elif obj.match_round == 'SEMI': color, text = 'orange', 'Bán kết'
        elif obj.match_round == 'THIRD_PLACE': color, text = '#CD853F', 'Hạng Ba'
        elif obj.match_round == 'FINAL': color, text = 'green', 'Chung kết'
        else: color, text = 'blue', obj.get_match_round_display()
        return format_html('<span style="color: {}; font-weight: bold;">{}</span>', color, text)
    def save_formset(self, request, form, formset, change):
        instances = formset.save(commit=False)
        try:
            for instance in instances:
                if isinstance(instance, (Lineup, Goal, Card)) and getattr(instance, "player", None): instance.team = instance.player.team
                instance.save()
            formset.save_m2m()
        except ValidationError as e: self.message_user(request, "; ".join(getattr(e, "messages", [str(e)])), level=messages.ERROR)

@admin.register(Group)
class GroupAdmin(ModelAdmin): list_display = ("name", "tournament"); list_filter = ("tournament",); search_fields = ("name", "tournament__name"); list_per_page = 50
@admin.register(Lineup)
class LineupAdmin(ModelAdmin): list_display = ("player", "team", "match", "status"); list_filter = ("match__tournament", "team", "status"); search_fields = ("player__full_name", "match__team1__name", "match__team2__name"); autocomplete_fields = ("match", "player", "team"); list_select_related = ("match", "team", "player"); list_per_page = 50
@admin.register(Goal)
class GoalAdmin(ModelAdmin): list_display = ("match", "team", "player", "minute"); list_filter = ("match__tournament", "team"); search_fields = ("player__full_name",); autocomplete_fields = ("match", "player", "team"); list_select_related = ("match", "team", "player"); list_per_page = 50
@admin.register(Card)
class CardAdmin(ModelAdmin): list_display = ("match", "team", "player", "card_type", "minute"); list_filter = ("match__tournament", "team", "card_type"); search_fields = ("player__full_name",); autocomplete_fields = ("match", "player", "team"); list_select_related = ("match", "team", "player"); list_per_page = 50
@admin.register(HomeBanner)
class HomeBannerAdmin(ModelAdmin):
    list_display = ("title", "order", "is_active", "preview"); list_editable = ("order", "is_active"); search_fields = ("title",); list_per_page = 50
    def preview(self, obj):
        if obj.image: return format_html('<img src="{}" style="height:36px;border-radius:6px;object-fit:cover">', obj.image.url)
        return "-"
    preview.short_description = "Ảnh"

@admin.register(Announcement)
class AnnouncementAdmin(ModelAdmin):
    list_display = ('title', 'tournament', 'audience', 'is_published', 'created_at'); list_filter = ('tournament', 'is_published', 'audience'); search_fields = ('title', 'content'); list_editable = ('is_published',); date_hierarchy = 'created_at'; actions = ['send_email_notification']
    @admin.action(description='Gửi email thông báo cho các đội trưởng')
    def send_email_notification(self, request, queryset):
        sent_count = 0
        for announcement in queryset:
            if not announcement.is_published: self.message_user(request, f"Thông báo '{announcement.title}' chưa được công khai nên không thể gửi.", messages.WARNING); continue
            tournament = announcement.tournament
            captains = Team.objects.filter(tournament=tournament).select_related('captain')
            recipient_list = {c.captain.email for c in captains if c.captain.email}
            if recipient_list:
                try: send_notification_email(subject=f"[Thông báo] {tournament.name}: {announcement.title}", template_name='tournaments/emails/announcement_notification.html', context={'announcement': announcement}, recipient_list=list(recipient_list)); sent_count += 1
                except Exception as e: self.message_user(request, f"Gặp lỗi khi gửi thông báo '{announcement.title}': {e}", messages.ERROR)
            else: self.message_user(request, f"Không tìm thấy email đội trưởng nào cho giải '{tournament.name}'.", messages.WARNING)
        if sent_count > 0: self.message_user(request, f"Đã gửi thành công {sent_count} thông báo qua email.", messages.SUCCESS)