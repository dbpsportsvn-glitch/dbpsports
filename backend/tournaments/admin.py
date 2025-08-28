# tournaments/admin.py

from django.contrib import admin
from .models import Tournament, Team, Player, Match, Lineup, Group, Goal
from django.utils.html import format_html
from itertools import combinations
from django.utils import timezone 
import random
from django.contrib import messages
import random
from itertools import combinations # <-- Thêm dòng import này
from django.contrib import messages
from .models import Tournament, Team, Player, Match, Lineup, Group
from .utils import send_notification_email

# === THÊM CLASS MỚI NÀY VÀO ===
class GroupInline(admin.TabularInline):
    model = Group
    extra = 1 # Hiển thị sẵn 1 dòng trống để thêm

@admin.register(Tournament)
class TournamentAdmin(admin.ModelAdmin):
    list_display = ('name', 'status', 'start_date', 'end_date')
    list_filter = ('status',)
    search_fields = ('name',)
    list_editable = ('status',)
    actions = ['draw_groups', 'generate_group_stage_matches', 'generate_knockout_matches', 'generate_final_match']
    inlines = [GroupInline] # <-- Thêm dòng này

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

    # === THÊM TOÀN BỘ PHƯƠNG THỨC MỚI NÀY VÀO ===
    @admin.action(description='Tạo cặp đấu Tứ kết')
    def generate_knockout_matches(self, request, queryset):
        for tournament in queryset:
            groups = list(tournament.groups.all().order_by('name'))
            
            # Giả định có 2 bảng đấu (A và B)
            if len(groups) != 2:
                self.message_user(request, f"Chức năng này hiện chỉ hỗ trợ 2 bảng đấu.", messages.ERROR)
                continue

            # Lấy bảng xếp hạng cho từng bảng
            standings_A = groups[0].get_standings()
            standings_B = groups[1].get_standings()

            if len(standings_A) < 2 or len(standings_B) < 2:
                self.message_user(request, f"Không đủ đội trong các bảng của giải '{tournament.name}' để tạo Tứ kết.", messages.ERROR)
                continue

            # Xác định các đội nhất nhì bảng
            winner_A = standings_A[0]['team_obj']
            runner_up_A = standings_A[1]['team_obj']
            winner_B = standings_B[0]['team_obj']
            runner_up_B = standings_B[1]['team_obj']

            # Tạo các cặp đấu Tứ kết (ví dụ: Nhất A vs Nhì B, Nhất B vs Nhì A)
            Match.objects.get_or_create(
                tournament=tournament,
                match_round='SEMI', # Giả sử có 2 bảng thì vào thẳng Bán kết
                team1=winner_A,
                team2=runner_up_B,
                defaults={'match_time': timezone.now()}
            )
            Match.objects.get_or_create(
                tournament=tournament,
                match_round='SEMI', # Giả sử có 2 bảng thì vào thẳng Bán kết
                team1=winner_B,
                team2=runner_up_A,
                defaults={'match_time': timezone.now()}
            )
            self.message_user(request, f"Đã tạo các cặp đấu Bán kết cho giải '{tournament.name}'.", messages.SUCCESS)

    # === THÊM TOÀN BỘ PHƯƠNG THỨC MỚI NÀY VÀO ===
    @admin.action(description='Tạo trận Chung kết từ Bán kết')
    def generate_final_match(self, request, queryset):
        for tournament in queryset:
            # Tìm các trận bán kết đã có tỉ số
            semi_finals = tournament.matches.filter(match_round='SEMI', team1_score__isnull=False, team2_score__isnull=False)

            if semi_finals.count() != 2:
                self.message_user(request, f"Cần có đủ 2 trận Bán kết đã có tỉ số cho giải '{tournament.name}'.", messages.ERROR)
                continue

            # Xác định 2 đội chiến thắng
            winners = []
            for match in semi_finals:
                if match.team1_score > match.team2_score:
                    winners.append(match.team1)
                else:
                    winners.append(match.team2)
            
            # Tạo trận Chung kết
            if len(winners) == 2:
                Match.objects.get_or_create(
                    tournament=tournament,
                    match_round='FINAL',
                    team1=winners[0],
                    team2=winners[1],
                    defaults={'match_time': timezone.now()}
                )
                self.message_user(request, f"Đã tạo trận Chung kết cho giải '{tournament.name}'.", messages.SUCCESS)
            else:
                 self.message_user(request, f"Không thể xác định 2 đội chiến thắng từ các trận Bán kết.", messages.ERROR)

@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ('name', 'tournament', 'captain', 'payment_status', 'display_proof', 'display_logo') # Thêm display_proof
    list_filter = ('tournament', 'payment_status',)
    search_fields = ('captain__username', 'name',)
    list_editable = ('payment_status',)

    # === THÊM PHƯƠ-THỨC MỚI NÀY VÀO ===
    def save_model(self, request, obj, form, change):
        # Lưu lại trạng thái cũ trước khi lưu
        old_obj = Team.objects.get(pk=obj.pk) if obj.pk else None

        # Thực hiện việc lưu bình thường
        super().save_model(request, obj, form, change)

        # Kiểm tra xem trạng thái có thay đổi thành "Đã thanh toán" không
        if old_obj and old_obj.payment_status != 'PAID' and obj.payment_status == 'PAID':
            # Gửi email xác nhận cho đội trưởng
            captain_email = obj.captain.email
            if captain_email:
                send_notification_email(
                    subject=f"Xác nhận thanh toán thành công cho đội {obj.name}",
                    template_name='tournaments/emails/payment_confirmed.html',
                    context={'team': obj},
                    recipient_list=[captain_email]
                )

    def display_logo(self, obj):
        if obj.logo:
            return format_html(f'<img src="{obj.logo.url}" width="40" height="40" />')
        return "No Logo"
    display_logo.short_description = 'Logo'

    # === THÊM PHƯƠNG THỨC MỚI NÀY VÀO ===
    def display_proof(self, obj):
        if obj.payment_proof:
            return format_html(f'<a href="{obj.payment_proof.url}" target="_blank">Xem hóa đơn</a>')
        return "Chưa có"
    display_proof.short_description = 'Hóa đơn'

@admin.register(Player)
class PlayerAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'team', 'jersey_number', 'position')
    list_filter = ('team__tournament', 'team')
    search_fields = ('full_name',)

# === THÊM CLASS INLINE MỚI NÀY VÀO ===
class GoalInline(admin.TabularInline):
    model = Goal
    extra = 1 # Hiển thị sẵn 1 dòng trống

@admin.register(Match)
class MatchAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'tournament', 'match_time', 'team1_score', 'team2_score', 'location')
    list_filter = ('tournament',)
    list_editable = ('team1_score', 'team2_score',)
    list_display_links = ('__str__', 'match_time',)
    inlines = [GoalInline]

@admin.register(Lineup)
class LineupAdmin(admin.ModelAdmin):
    list_display = ('player', 'team', 'match', 'status')
    list_filter = ('match__tournament', 'team', 'status')

@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = ('name', 'tournament')
    list_filter = ('tournament',)
    # Thêm dòng này để tìm kiếm giải đấu
    search_fields = ('tournament__name',)    
