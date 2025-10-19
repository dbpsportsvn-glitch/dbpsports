# backend/tournaments/admin.py

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
from .models import (Tournament, Team, Player, Match, Lineup, Group, Goal, Card, 
                     HomeBanner, Announcement, TournamentPhoto, Notification, TeamAchievement,
                     TeamRegistration, TournamentBudget, RevenueItem, ExpenseItem, BudgetHistory,
                     TournamentStaff, MatchNote, CoachRecruitment, PlayerTeamExit, StaffPayment) # <-- Import model mới
from .utils import send_notification_email, send_schedule_notification

# Admin configuration

# ===== CÁC Hàm Cho Bộ lọc (Giữ nguyên) =====
class MatchResultFilter(admin.SimpleListFilter):
    title = 'tình trạng kết quả'
    parameter_name = 'has_result'
    def lookups(self, request, model_admin): return (('yes', 'Đã có kết quả'), ('no', 'Chưa đá'),)
    def queryset(self, request, queryset):
        if self.value() == 'yes': return queryset.filter(team1_score__isnull=False, team2_score__isnull=False)
        if self.value() == 'no': return queryset.filter(team1_score__isnull=True, team2_score__isnull=True)

class PlayerCountFilter(admin.SimpleListFilter):
    title = 'tình trạng đội hình'
    parameter_name = 'player_count'
    def lookups(self, request, model_admin): return (('yes', 'Đã có cầu thủ'), ('no', 'Chưa có cầu thủ'),)
    def queryset(self, request, queryset):
        queryset = queryset.annotate(player_count=Count('players'))
        if self.value() == 'yes': return queryset.filter(player_count__gt=0)
        if self.value() == 'no': return queryset.filter(player_count=0)

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
    list_display = ("name", "status", "start_date", "registration_fee", "generate_schedule_link", "draw_groups_link", "bulk_upload_link", "budget_dashboard_link", "view_details_link")
    list_filter = ("status", "region"); search_fields = ("name",); list_editable = ("status",); date_hierarchy = "start_date"
    inlines = [GroupInline, TournamentPhotoInline]; list_per_page = 50
    actions = ['auto_create_next_knockout_round', 'create_third_place_match', 'create_semi_finals_with_best_runner_ups']
    
    class Meta:
        verbose_name = "Giải đấu"
        verbose_name_plural = "Giải đấu"
    fieldsets = (
        ('Thông tin cơ bản', {
            'fields': ('name', 'status', 'format', 'region', 'location_detail', 'start_date', 'end_date', 'image')
        }),
               ('Phí đăng ký', {
                   'fields': ('registration_fee', 'shop_discount_percentage'),
                   'description': 'Phí đăng ký cho mỗi đội tham gia giải đấu và phần trăm tiền lãi từ shop được trừ vào phí đăng ký'
               }),
        ('Thông tin thanh toán', {
            'fields': ('bank_name', 'bank_account_number', 'bank_account_name', 'payment_qr_code'),
            'classes': ('collapse',)
        }),
        ('Nội dung', {
            'fields': ('rules', 'gallery_url'),
            'classes': ('collapse',)
        }),
    )
    class Media: js = ('js/admin_state.js',)
    
    @admin.display(description='Tải ảnh hàng loạt')
    def bulk_upload_link(self, obj):
        url = reverse('tournament_bulk_upload', args=[obj.pk]); return format_html('<a class="button" href="{}" target="_blank">Tải ảnh</a>', url)
    
    def generate_schedule_link(self, obj):
        is_in_progress = obj.status == 'IN_PROGRESS'
        has_groups = obj.groups.exists()
        has_matches = obj.matches.exists()
        # Thay đổi logic kiểm tra dựa trên TeamRegistration
        has_unassigned_teams = TeamRegistration.objects.filter(tournament=obj, group__isnull=True, payment_status='PAID').exists()
        has_paid_teams = TeamRegistration.objects.filter(tournament=obj, payment_status='PAID').exists()
        if is_in_progress and has_groups and has_paid_teams and not has_unassigned_teams and not has_matches:
            url = reverse('generate_schedule', args=[obj.pk])
            return format_html('<a class="button" href="{}" target="_blank">Xếp Lịch</a>', url)
        return "—"
    generate_schedule_link.short_description = 'Xếp Lịch Thi Đấu'
    
    def draw_groups_link(self, obj):
        if obj.status == 'IN_PROGRESS' and TeamRegistration.objects.filter(tournament=obj, payment_status='PAID', group__isnull=True).exists():
            url = reverse('draw_groups', args=[obj.pk])
            return format_html('<a class="button" href="{}" target="_blank">Bốc thăm</a>', url)
        return "—"
    draw_groups_link.short_description = 'Bốc thăm Chia bảng'
    
    def budget_dashboard_link(self, obj):
        url = reverse('budget_dashboard', kwargs={'tournament_pk': obj.pk})
        return format_html(
            '<a href="{}" target="_blank" style="background: linear-gradient(135deg, #f59e0b, #d97706); color: white; padding: 6px 12px; border-radius: 6px; text-decoration: none; font-weight: bold; display: inline-block;">'
            '<i class="bi bi-calculator" style="margin-right: 4px;"></i>Quản lý tài chính</a>',
            url
        )
    budget_dashboard_link.short_description = 'Dashboard Tài chính'
    
    def view_details_link(self, obj):
        teams_url = reverse('admin:tournaments_teamregistration_changelist') + f'?tournament__id__exact={obj.pk}'
        matches_url = reverse('admin:tournaments_match_changelist') + f'?tournament__id__exact={obj.pk}'
        groups_url = reverse('admin:tournaments_group_changelist') + f'?tournament__id__exact={obj.pk}'
        return format_html('<a href="{}">Xem Đăng ký</a> | <a href="{}">Xem Bảng</a> | <a href="{}">Xem Trận</a>', teams_url, groups_url, matches_url)
    view_details_link.short_description = 'Quản lý Giải'
    
    @admin.action(description='Tự động tạo vòng Knockout tiếp theo (Tứ kết -> Bán kết -> Chung kết)')
    def auto_create_next_knockout_round(self, request, queryset):
        for tournament in queryset:
            if not tournament.matches.filter(match_round__in=['QUARTER', 'SEMI', 'FINAL']).exists():
                groups = list(tournament.groups.order_by('name'))
                if not groups: self.message_user(request, f"Giải '{tournament.name}' chưa có bảng đấu.", messages.ERROR); continue
                
                num_groups = len(groups)
                qualified_teams = []
                all_second_place = []  # Lưu đội nhì các bảng để chọn tốt nhất
                
                for group in groups:
                    standings = group.get_standings()
                    num_teams_in_group = len(standings)
                    
                    # Logic linh hoạt dựa trên số bảng và số đội trong bảng
                    if num_groups == 2:
                        # 2 bảng: lấy 2 đội đầu mỗi bảng để có 4 đội (Bán kết)
                        if num_teams_in_group >= 2:
                            num_qualified = 2
                            qualified_teams.extend([s['team_obj'] for s in standings[:num_qualified]])
                        else:
                            self.message_user(request, f"Bảng '{group.name}' cần ít nhất 2 đội để tạo knockout.", messages.ERROR)
                            continue
                    elif num_groups == 3:
                        # 3 bảng: lấy đội nhất mỗi bảng + 1 đội nhì tốt nhất = 4 đội (Bán kết)
                        if num_teams_in_group >= 2:
                            qualified_teams.append(standings[0]['team_obj'])  # Đội nhất
                            all_second_place.append(standings[1])  # Lưu đội nhì để so sánh
                        elif num_teams_in_group == 1:
                            qualified_teams.append(standings[0]['team_obj'])  # Chỉ có 1 đội thì lấy luôn
                        else:
                            self.message_user(request, f"Bảng '{group.name}' chưa có đội nào.", messages.ERROR)
                            continue
                    elif num_groups == 4:
                        # 4 bảng: lấy 2 đội đầu mỗi bảng để có 8 đội (Tứ kết)
                        if num_teams_in_group >= 2:
                            num_qualified = 2
                            qualified_teams.extend([s['team_obj'] for s in standings[:num_qualified]])
                        else:
                            self.message_user(request, f"Bảng '{group.name}' cần ít nhất 2 đội để tạo knockout.", messages.ERROR)
                            continue
                    else:
                        # Các trường hợp khác: logic cũ
                        if num_teams_in_group >= 4:
                            num_qualified = 2
                        elif num_teams_in_group >= 2:
                            num_qualified = 1
                        else:
                            self.message_user(request, f"Bảng '{group.name}' chưa đủ đội.", messages.ERROR)
                            continue
                        qualified_teams.extend([s['team_obj'] for s in standings[:num_qualified]])
                
                # Xử lý trường hợp 3 bảng: chọn 1 đội nhì tốt nhất
                if num_groups == 3 and len(all_second_place) >= 1:
                    all_second_place.sort(key=lambda x: (x['points'], x['gd'], x['gf']), reverse=True)
                    qualified_teams.append(all_second_place[0]['team_obj'])
                
                if len(qualified_teams) == 8:
                    tournament.matches.filter(match_round='QUARTER').delete()
                    pairings = [(qualified_teams[0], qualified_teams[3]), (qualified_teams[2], qualified_teams[1]), (qualified_teams[4], qualified_teams[7]), (qualified_teams[6], qualified_teams[5])]
                    for t1, t2 in pairings: Match.objects.create(tournament=tournament, match_round='QUARTER', team1=t1, team2=t2, match_time=timezone.now())
                    self.message_user(request, f"Đã tạo 4 cặp đấu Tứ kết cho giải '{tournament.name}'.", messages.SUCCESS)
                elif len(qualified_teams) == 4:
                    tournament.matches.filter(match_round='SEMI').delete()
                    pairings = [(qualified_teams[0], qualified_teams[3]), (qualified_teams[2], qualified_teams[1])]
                    for t1, t2 in pairings: Match.objects.create(tournament=tournament, match_round='SEMI', team1=t1, team2=t2, match_time=timezone.now())
                    self.message_user(request, f"Đã tạo 2 cặp đấu Bán kết cho giải '{tournament.name}' (4 đội từ {num_groups} bảng).", messages.SUCCESS)
                else: 
                    self.message_user(request, f"Số đội đủ điều kiện: {len(qualified_teams)}. Cần 4 đội (2 bảng x 2) hoặc 8 đội (4 bảng x 2) để tạo knockout.", messages.WARNING)
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
            if semi_finals.exists() and not tournament.matches.filter(match_round='FINAL').exists():
                finished_sf = semi_finals.filter(team1_score__isnull=False, team2_score__isnull=False)
                if finished_sf.count() != 2: self.message_user(request, f"Cần cập nhật tỉ số 2 trận Bán kết của giải '{tournament.name}'.", messages.WARNING); continue
                winners = [m.winner for m in finished_sf if m.winner]
                if len(winners) == 2:
                    tournament.matches.filter(match_round='FINAL').delete()
                    Match.objects.create(tournament=tournament, match_round='FINAL', team1=winners[0], team2=winners[1], match_time=timezone.now())
                    self.message_user(request, f"Đã tạo trận Chung kết cho giải '{tournament.name}'.", messages.SUCCESS)
                continue
    
    @admin.action(description='Tạo trận Tranh Hạng Ba (từ Bán kết)')
    def create_third_place_match(self, request, queryset):
        for tournament in queryset:
            if tournament.matches.filter(match_round='THIRD_PLACE').exists():
                self.message_user(request, f"Giải '{tournament.name}' đã có trận Tranh Hạng Ba.", messages.WARNING)
                continue
            semi_finals = tournament.matches.filter(match_round='SEMI', team1_score__isnull=False, team2_score__isnull=False)
            if semi_finals.count() != 2:
                self.message_user(request, f"Cần cập nhật đầy đủ tỉ số 2 trận Bán kết của giải '{tournament.name}' trước.", messages.WARNING)
                continue
            losers = [m.loser for m in semi_finals if m.loser]
            if len(losers) == 2:
                Match.objects.create(tournament=tournament, match_round='THIRD_PLACE', team1=losers[0], team2=losers[1], match_time=timezone.now())
                self.message_user(request, f"Đã tạo thành công trận Tranh Hạng Ba cho giải '{tournament.name}'.", messages.SUCCESS)
            else:
                self.message_user(request, f"Không thể xác định 2 đội thua từ Bán kết cho giải '{tournament.name}'.", messages.ERROR)

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
                if not standings: self.message_user(request, f"Bảng '{group.name}' chưa có đội nào.", messages.ERROR); return
                group_winners.append(standings[0])
                if len(standings) > 1: second_place_teams_with_stats.append(standings[1])
            
            second_place_teams_with_stats.sort(key=lambda x: (x['points'], x['gd'], x['gf']), reverse=True)
            num_runner_ups_needed = 4 - len(group_winners)
            if num_runner_ups_needed < 0: num_runner_ups_needed = 0

            if len(second_place_teams_with_stats) < num_runner_ups_needed:
                self.message_user(request, f"Không đủ số đội nhì bảng để tạo Bán kết cho giải '{tournament.name}'.", messages.ERROR)
                continue

            best_runner_ups = second_place_teams_with_stats[:num_runner_ups_needed]
            semi_finalists_with_stats = group_winners + best_runner_ups

            if len(semi_finalists_with_stats) != 4:
                self.message_user(request, f"Không thể xác định được 4 đội vào Bán kết cho giải '{tournament.name}'.", messages.ERROR)
                continue
            
            semi_finalists_with_stats.sort(key=lambda x: (x['points'], x['gd'], x['gf']), reverse=True)
            top_4_teams = [team_stats['team_obj'] for team_stats in semi_finalists_with_stats]
            pairings = [(top_4_teams[0], top_4_teams[3]), (top_4_teams[1], top_4_teams[2])]

            tournament.matches.filter(match_round='SEMI').delete()
            for team1, team2 in pairings:
                Match.objects.create(tournament=tournament, match_round='SEMI', team1=team1, team2=team2, match_time=timezone.now())
            
            self.message_user(request, f"Đã tạo Bán kết thành công cho giải '{tournament.name}'.", messages.SUCCESS)

@admin.register(Team)
class TeamAdmin(ModelAdmin):
    list_display = ("name", "captain", "display_logo")
    search_fields = ("name", "captain__username")
    inlines = [PlayerInline]
    autocomplete_fields = ("captain",)
    list_select_related = ("captain",)
    list_per_page = 50
    
    class Meta:
        verbose_name = "Đội bóng"
        verbose_name_plural = "Đội bóng"

    def display_logo(self, obj):
        if obj.logo: return format_html(f'<img src="{obj.logo.url}" width="40" height="40" />')
        return "Chưa có Logo"
    display_logo.short_description = 'Logo'

@admin.register(TeamRegistration)
class TeamRegistrationAdmin(ModelAdmin):
    list_display = ('team', 'tournament', 'group', 'payment_status', 'display_proof', 'registered_at')
    list_filter = ('tournament', 'group', 'payment_status')
    search_fields = ('team__name', 'tournament__name')
    list_editable = ('payment_status', 'group')
    autocomplete_fields = ('team', 'tournament', 'group')
    list_select_related = ('team', 'tournament', 'group')
    actions = ['reject_payments', 'approve_payments', 'remove_team_from_tournament']
    
    class Meta:
        verbose_name = "Đăng ký đội"
        verbose_name_plural = "Đăng ký đội"

    def display_proof(self, obj):
        if obj.payment_proof:
            return format_html(f'<a href="{obj.payment_proof.url}" target="_blank">Xem hóa đơn</a>')
        return "Chưa có"
    display_proof.short_description = 'Hóa đơn'

    @admin.action(description='Duyệt thanh toán cho các đăng ký đã chọn')
    def approve_payments(self, request, queryset):
        # Lọc ra các registration có status PENDING
        pending_registrations = queryset.filter(payment_status='PENDING')
        updated_count = pending_registrations.count()
        
        # Cập nhật status và gửi email cho từng registration
        for reg in pending_registrations:
            reg.payment_status = 'PAID'
            reg.save()
            
            # Gửi email thông báo cho đội trưởng
            if reg.team.captain.email:
                send_notification_email(
                    subject=f"Xác nhận thanh toán thành công cho đội {reg.team.name}",
                    template_name='tournaments/emails/payment_confirmed.html',
                    context={'team': reg.team, 'tournament': reg.tournament},
                    recipient_list=[reg.team.captain.email]
                )
        
        self.message_user(request, f'Đã duyệt thành công thanh toán cho {updated_count} đội.')
    
    @admin.action(description='Từ chối thanh toán cho các đăng ký đã chọn')
    def reject_payments(self, request, queryset):
        # Lọc ra các registration có status PENDING
        pending_registrations = queryset.filter(payment_status='PENDING')
        rejected_count = pending_registrations.count()
        
        # Cập nhật status và gửi email cho từng registration
        for reg in pending_registrations:
            reg.payment_status = 'UNPAID'
            reg.payment_proof = None  # Xóa bằng chứng thanh toán
            reg.save()
            
            # Gửi email thông báo từ chối cho đội trưởng
            if reg.team.captain.email:
                send_notification_email(
                    subject=f"Thanh toán không hợp lệ cho đội {reg.team.name}",
                    template_name='tournaments/emails/payment_rejected.html',
                    context={'team': reg.team, 'tournament': reg.tournament, 'registration': reg},
                    recipient_list=[reg.team.captain.email]
                )
        
        self.message_user(request, f'Đã từ chối thanh toán cho {rejected_count} đội và gửi email thông báo.')
    
    @admin.action(description='Gỡ đội khỏi giải đấu (trả về trạng thái tự do)')
    def remove_team_from_tournament(self, request, queryset):
        removed_count = 0
        for registration in queryset:
            team_name = registration.team.name
            tournament_name = registration.tournament.name
            registration.delete()
            removed_count += 1
            
            # Gửi email thông báo cho đội trưởng
            if registration.team.captain.email:
                send_notification_email(
                    subject=f"Đội {team_name} đã được gỡ khỏi giải {tournament_name}",
                    template_name='tournaments/emails/team_removed_from_tournament.html',
                    context={'team': registration.team, 'tournament': registration.tournament},
                    recipient_list=[registration.team.captain.email]
                )
        
        self.message_user(request, f'Đã gỡ thành công {removed_count} đội khỏi các giải đấu. Các đội này đã trở về trạng thái tự do.')
    
    def save_model(self, request, obj, form, change):
        old_obj = TeamRegistration.objects.get(pk=obj.pk) if obj.pk else None
        super().save_model(request, obj, form, change)
        
        # Gửi email khi duyệt thanh toán
        if old_obj and old_obj.payment_status != 'PAID' and obj.payment_status == 'PAID':
            if obj.team.captain.email:
                send_notification_email(
                    subject=f"Xác nhận thanh toán thành công cho đội {obj.team.name}",
                    template_name='tournaments/emails/payment_confirmed.html',
                    context={'team': obj.team, 'tournament': obj.tournament},
                    recipient_list=[obj.team.captain.email]
                )
        
        # Gửi email khi từ chối thanh toán
        if old_obj and old_obj.payment_status != 'REJECTED' and obj.payment_status == 'REJECTED':
            if obj.team.captain.email:
                send_notification_email(
                    subject=f"Thanh toán không hợp lệ cho đội {obj.team.name}",
                    template_name='tournaments/emails/payment_rejected.html',
                    context={'team': obj.team, 'tournament': obj.tournament, 'registration': obj},
                    recipient_list=[obj.team.captain.email]
                )

@admin.register(Player)
class PlayerAdmin(ModelAdmin):
    list_display = ("full_name", "link_to_team", "jersey_number", "position", "display_avatar", "display_qr_code")
    list_filter = ("team__tournaments", "position", "team")
    search_fields = ("full_name", "team__name", "jersey_number")
    list_editable = ("position",)
    ordering = ("team", "jersey_number")
    autocomplete_fields = ("team",)
    list_select_related = ("team",)
    list_per_page = 50
    
    class Meta:
        verbose_name = "Cầu thủ"
        verbose_name_plural = "Cầu thủ"

    @admin.display(description='Đội', ordering='team__name')
    def link_to_team(self, obj):
        if obj.team:
            link = reverse("admin:tournaments_team_change", args=[obj.team.id])
            return format_html('<a href="{}">{}</a>', link, obj.team.name)
        return "Cầu thủ tự do"

    def display_avatar(self, obj):
        if obj.avatar:
            return format_html('<img src="{}" width="40" height="40" style="object-fit: cover; border-radius: 50%;" />', obj.avatar.url)
        return "Chưa có ảnh"
    display_avatar.short_description = 'Ảnh đại diện'

    # === THÊM HÀM MỚI NÀY VÀO CUỐI CLASS ===
    @admin.display(description='Mã QR ủng hộ')
    def display_qr_code(self, obj):
        if obj.donation_qr_code:
            return format_html(f'<a href="{obj.donation_qr_code.url}" target="_blank">Xem ảnh</a>')
        return "Chưa có"


@admin.register(Match)
class MatchAdmin(ModelAdmin):
    list_display = ("__str__", "tournament", "colored_round", "display_match_time", "team1_score", "team2_score",); list_filter = ("tournament", "match_round", MatchResultFilter); search_fields = ("team1__name", "team2__name", "tournament__name"); list_editable = ("team1_score", "team2_score",); date_hierarchy = "match_time"; inlines = [LineupInline, GoalInline, CardInline]; autocomplete_fields = ("team1", "team2", "tournament"); list_select_related = ("tournament", "team1", "team2"); list_per_page = 50
    
    class Meta:
        verbose_name = "Trận đấu"
        verbose_name_plural = "Trận đấu"
    @admin.display(description='Thời gian thi đấu', ordering='match_time')
    def display_match_time(self, obj): return format_html("{}<br>{}", obj.match_time.strftime("%H:%M"), obj.match_time.strftime("%d-%m-%Y"))
    fieldsets = (
        ('Thông tin chung', {'fields': ('tournament', 'match_round', 'team1', 'team2', 'livestream_url', 'ticker_text', 'cover_photo', 'gallery_url')}),
        ('Kết quả & Lịch thi đấu', {'fields': ('team1_score', 'team2_score', 'team1_penalty_score', 'team2_penalty_score', 'match_time', 'location', 'referee', 'commentator')}),
    )
    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        if (obj.match_round != 'GROUP' and obj.team1_score is not None and obj.team1_score == obj.team2_score and (obj.team1_penalty_score is None or obj.team2_penalty_score is None)):
            self.message_user(request, "Cảnh báo: Trận đấu có tỉ số hòa, vui lòng cập nhật tỉ số luân lưu để xác định đội thắng.", messages.WARNING)
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

@admin.register(TournamentPhoto)
class TournamentPhotoAdmin(admin.ModelAdmin): 
    list_display = ('id', 'tournament', 'caption', 'image_preview', 'uploaded_at')
    list_filter = ('tournament',)
    search_fields = ('caption', 'tournament__name')
    list_display_links = ('id', 'tournament')
    readonly_fields = ('image_preview',)
    list_per_page = 20
    
    class Meta:
        verbose_name = "Ảnh giải đấu"
        verbose_name_plural = "Ảnh giải đấu"
    @admin.display(description='Xem trước')
    def image_preview(self, obj):
        if obj.image: return format_html('<img src="{}" style="max-height: 100px; max-width: 150px;" />', obj.image.url)
        return "Không có ảnh"
@admin.register(Group)
class GroupAdmin(ModelAdmin): 
    list_display = ("name", "tournament"); list_filter = ("tournament",); search_fields = ("name", "tournament__name"); list_per_page = 50
    
    class Meta:
        verbose_name = "Bảng đấu"
        verbose_name_plural = "Bảng đấu"

@admin.register(Lineup)
class LineupAdmin(ModelAdmin): 
    list_display = ("player", "team", "match", "status"); list_filter = ("match__tournament", "team", "status"); search_fields = ("player__full_name", "match__team1__name", "match__team2__name"); autocomplete_fields = ("match", "player", "team"); list_select_related = ("match", "team", "player"); list_per_page = 50
    
    class Meta:
        verbose_name = "Đội hình"
        verbose_name_plural = "Đội hình"

@admin.register(Goal)
class GoalAdmin(ModelAdmin): 
    list_display = ("match", "team", "player", "minute"); list_filter = ("match__tournament", "team"); search_fields = ("player__full_name",); autocomplete_fields = ("match", "player", "team"); list_select_related = ("match", "team", "player"); list_per_page = 50
    
    class Meta:
        verbose_name = "Bàn thắng"
        verbose_name_plural = "Bàn thắng"

@admin.register(Card)
class CardAdmin(ModelAdmin): 
    list_display = ("match", "team", "player", "card_type", "minute"); list_filter = ("match__tournament", "team", "card_type"); search_fields = ("player__full_name",); autocomplete_fields = ("match", "player", "team"); list_select_related = ("match", "team", "player"); list_per_page = 50
    
    class Meta:
        verbose_name = "Thẻ phạt"
        verbose_name_plural = "Thẻ phạt"
@admin.register(HomeBanner)
class HomeBannerAdmin(ModelAdmin): 
    list_display = ("title", "order", "is_active", "preview"); list_editable = ("order", "is_active"); search_fields = ("title",); list_per_page = 50
    
    class Meta:
        verbose_name = "Banner trang chủ"
        verbose_name_plural = "Banner trang chủ"
    
    def preview(self, obj):
        if obj.image: return format_html('<img src="{}" style="height:36px;border-radius:6px;object-fit:cover">', obj.image.url)
        return "-"
    preview.short_description = "Ảnh"
@admin.register(Announcement)
class AnnouncementAdmin(ModelAdmin): 
    list_display = ('title', 'tournament', 'audience', 'is_published', 'created_at'); list_filter = ('tournament', 'is_published', 'audience'); search_fields = ('title', 'content'); list_editable = ('is_published',); date_hierarchy = 'created_at'; actions = ['send_email_notification']
    class Media: js = ('js/admin_state.js',)
    
    class Meta:
        verbose_name = "Thông báo"
        verbose_name_plural = "Thông báo"
    @admin.action(description='Gửi email thông báo cho các đội trưởng')
    def send_email_notification(self, request, queryset):
        sent_count = 0
        for announcement in queryset:
            if not announcement.is_published: self.message_user(request, f"Thông báo '{announcement.title}' chưa được công khai nên không thể gửi.", messages.WARNING); continue
            tournament = announcement.tournament
            registrations = TeamRegistration.objects.filter(tournament=tournament, team__captain__email__isnull=False).select_related('team__captain')
            recipient_list = {reg.team.captain.email for reg in registrations}
            if recipient_list:
                try: 
                    send_notification_email(subject=f"[Thông báo] {tournament.name}: {announcement.title}", template_name='tournaments/emails/announcement_notification.html', context={'announcement': announcement}, recipient_list=list(recipient_list))
                    sent_count += 1
                except Exception as e: self.message_user(request, f"Gặp lỗi khi gửi thông báo '{announcement.title}': {e}", messages.ERROR)
            else: self.message_user(request, f"Không tìm thấy email đội trưởng nào cho giải '{tournament.name}'.", messages.WARNING)
        if sent_count > 0: self.message_user(request, f"Đã gửi thành công {sent_count} thông báo qua email.", messages.SUCCESS)

@admin.register(TeamAchievement)
class TeamAchievementAdmin(admin.ModelAdmin): 
    list_display = ('team', 'achievement_type', 'tournament', 'achieved_at'); list_filter = ('tournament', 'achievement_type'); search_fields = ('team__name', 'tournament__name', 'description'); autocomplete_fields = ('team', 'tournament')
    
    class Meta:
        verbose_name = "Thành tích đội"
        verbose_name_plural = "Thành tích đội"

# ===== ADMIN CHO CÁC MODEL TÀI CHÍNH =====
@admin.register(TournamentBudget)
class TournamentBudgetAdmin(admin.ModelAdmin):
    list_display = ('tournament', 'initial_budget', 'get_total_revenue', 'get_total_expenses', 'get_profit_loss', 'get_budget_status', 'budget_dashboard_link', 'created_at')
    list_filter = ('tournament__status', 'tournament__region', 'created_at')
    search_fields = ('tournament__name',)
    readonly_fields = ('created_at', 'updated_at')
    autocomplete_fields = ('tournament',)
    
    class Meta:
        verbose_name = "Ngân sách giải đấu"
        verbose_name_plural = "Ngân sách giải đấu"
    
    def get_total_revenue(self, obj):
        return f"{obj.get_total_revenue():,} VNĐ"
    get_total_revenue.short_description = "Tổng thu"
    
    def get_total_expenses(self, obj):
        return f"{obj.get_total_expenses():,} VNĐ"
    get_total_expenses.short_description = "Tổng chi"
    
    def get_profit_loss(self, obj):
        profit_loss = obj.get_profit_loss()
        if profit_loss > 0:
            return format_html('<span style="color: green;">+{} VNĐ</span>', f'{profit_loss:,}')
        elif profit_loss < 0:
            return format_html('<span style="color: red;">{} VNĐ</span>', f'{profit_loss:,}')
        else:
            return f"{profit_loss:,} VNĐ"
    get_profit_loss.short_description = "Lời/Lỗ"
    
    def budget_dashboard_link(self, obj):
        """Link đến dashboard tài chính"""
        url = reverse('budget_dashboard', args=[obj.tournament.pk])
        return format_html(
            '<a href="{}" target="_blank" style="background: linear-gradient(135deg, #f59e0b, #d97706); color: white; padding: 6px 12px; border-radius: 6px; text-decoration: none; font-weight: bold; display: inline-block;">'
            '<i class="bi bi-calculator" style="margin-right: 4px;"></i>Quản lý tài chính</a>',
            url
        )
    budget_dashboard_link.short_description = "Dashboard"

@admin.register(RevenueItem)
class RevenueItemAdmin(admin.ModelAdmin):
    list_display = ('budget', 'category', 'description', 'amount', 'is_auto_calculated', 'date')
    list_filter = ('category', 'is_auto_calculated', 'date')
    search_fields = ('description', 'budget__tournament__name')
    readonly_fields = ('created_at',)
    autocomplete_fields = ('budget',)
    
    class Meta:
        verbose_name = "Khoản thu"
        verbose_name_plural = "Khoản thu"

@admin.register(ExpenseItem)
class ExpenseItemAdmin(admin.ModelAdmin):
    list_display = ('budget', 'category', 'description', 'amount', 'date')
    list_filter = ('category', 'date')
    search_fields = ('description', 'budget__tournament__name')
    readonly_fields = ('created_at',)
    autocomplete_fields = ('budget',)
    
    class Meta:
        verbose_name = "Khoản chi"
        verbose_name_plural = "Khoản chi"

@admin.register(BudgetHistory)
class BudgetHistoryAdmin(admin.ModelAdmin):
    list_display = ('budget', 'action', 'description', 'amount', 'user', 'timestamp')
    list_filter = ('action', 'timestamp')
    search_fields = ('description', 'budget__tournament__name', 'user__username')
    readonly_fields = ('timestamp',)
    autocomplete_fields = ('budget', 'user')
    
    class Meta:
        verbose_name = "Lịch sử ngân sách"
        verbose_name_plural = "Lịch sử ngân sách"

@admin.register(TournamentStaff)
class TournamentStaffAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'tournament', 'get_user_email')
    list_filter = ('role', 'tournament')
    search_fields = ('user__username', 'user__email', 'user__first_name', 'user__last_name', 'tournament__name')
    autocomplete_fields = ('tournament', 'user', 'role')
    list_select_related = ('tournament', 'user', 'role')
    list_per_page = 50
    
    class Meta:
        verbose_name = "Nhân sự giải đấu"
        verbose_name_plural = "Nhân sự giải đấu"
    
    @admin.display(description='Email', ordering='user__email')
    def get_user_email(self, obj):
        return obj.user.email if obj.user.email else "Chưa có email"
    
    fieldsets = (
        ('Thông tin cơ bản', {
            'fields': ('tournament', 'user', 'role')
        }),
    )

@admin.register(MatchNote)
class MatchNoteAdmin(admin.ModelAdmin):
    list_display = ('match', 'author', 'note_type', 'team', 'updated_at')
    list_filter = ('note_type', 'match__tournament')
    search_fields = ('author__username', 'match__team1__name', 'match__team2__name', 'team__name')
    autocomplete_fields = ('match', 'author', 'team')
    list_select_related = ('match', 'author', 'team', 'match__tournament')
    readonly_fields = ('created_at', 'updated_at')
    list_per_page = 50
    
    class Meta:
        verbose_name = "Ghi chú trận đấu"
        verbose_name_plural = "Ghi chú trận đấu"
    
    fieldsets = (
        ('Thông tin cơ bản', {
            'fields': ('match', 'author', 'note_type', 'team')
        }),
        ('Ghi chú của Bình luận viên', {
            'fields': ('commentator_notes_team1', 'commentator_notes_team2'),
            'classes': ('collapse',)
        }),
        ('Ghi chú của Đội trưởng', {
            'fields': ('captain_note',),
            'classes': ('collapse',)
        }),
        ('Thời gian', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(StaffPayment)
class StaffPaymentAdmin(admin.ModelAdmin):
    list_display = ('staff_member', 'role', 'tournament', 'rate_per_unit', 'number_of_units', 'total_amount', 'status', 'payment_date', 'created_at')
    list_filter = ('status', 'payment_unit', 'tournament', 'role')
    search_fields = ('staff_member__user__username', 'staff_member__user__email', 'staff_member__user__first_name', 'staff_member__user__last_name', 'tournament__name', 'role__name')
    autocomplete_fields = ('tournament', 'staff_member', 'role')
    list_select_related = ('tournament', 'staff_member__user', 'staff_member__role', 'role')
    list_per_page = 50
    readonly_fields = ('total_amount', 'created_at', 'updated_at')
    
    class Meta:
        verbose_name = "Tiền công nhân viên"
        verbose_name_plural = "Tiền công nhân viên"
    
    @admin.display(description='Tên nhân viên', ordering='staff_member__user__first_name')
    def get_staff_name(self, obj):
        return obj.staff_member.user.get_full_name()
    
    @admin.display(description='Vai trò', ordering='role__name')
    def get_role_name(self, obj):
        return obj.role.name
    
    @admin.display(description='Giải đấu', ordering='tournament__name')
    def get_tournament_name(self, obj):
        return obj.tournament.name
    
    @admin.display(description='Tổng tiền công', ordering='total_amount')
    def get_total_display(self, obj):
        return f"{obj.total_amount:,} VNĐ"
    
    fieldsets = (
        ('Thông tin cơ bản', {
            'fields': ('tournament', 'staff_member', 'role')
        }),
        ('Thông tin thanh toán', {
            'fields': ('rate_per_unit', 'payment_unit', 'number_of_units', 'total_amount')
        }),
        ('Trạng thái quản lý', {
            'fields': ('status', 'payment_date', 'notes')
        }),
        ('Thông tin hệ thống', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(CoachRecruitment)
class CoachRecruitmentAdmin(admin.ModelAdmin):
    list_display = ('team', 'coach', 'status', 'salary_offer', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('team__name', 'coach__full_name', 'coach__user__username')
    autocomplete_fields = ('team', 'coach')
    list_select_related = ('team', 'coach', 'coach__user')
    readonly_fields = ('created_at', 'updated_at')
    list_per_page = 50
    
    class Meta:
        verbose_name = "Tuyển dụng HLV"
        verbose_name_plural = "Tuyển dụng HLV"
    
    fieldsets = (
        ('Thông tin cơ bản', {
            'fields': ('team', 'coach', 'status')
        }),
        ('Đề nghị hợp đồng', {
            'fields': ('salary_offer', 'contract_duration', 'message')
        }),
        ('Thông tin hệ thống', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(PlayerTeamExit)
class PlayerTeamExitAdmin(ModelAdmin):
    """Admin cho model PlayerTeamExit"""
    list_display = (
        'player', 'current_team', 'exit_type', 'status', 
        'created_at', 'processed_at', 'processed_by'
    )
    list_filter = (
        'status', 'exit_type', 'current_team', 'created_at'
    )
    search_fields = (
        'player__full_name', 'current_team__name', 
        'reason', 'admin_notes'
    )
    readonly_fields = ('created_at', 'updated_at', 'processed_at')
    list_per_page = 50
    ordering = ['-created_at']
    
    fieldsets = (
        ('Thông tin yêu cầu', {
            'fields': ('player', 'current_team', 'exit_type', 'reason')
        }),
        ('Xử lý yêu cầu', {
            'fields': ('status', 'processed_by', 'processed_at', 'admin_notes')
        }),
        ('Thông tin hệ thống', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        """Tự động cập nhật thông tin xử lý khi thay đổi status"""
        if change and 'status' in form.changed_data:
            if obj.status != 'PENDING':
                obj.processed_by = request.user
                obj.processed_at = timezone.now()
        super().save_model(request, obj, form, change)