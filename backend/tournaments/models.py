# File: backend/tournaments/models.py

from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse
from django.db.models import Q
from django.core.exceptions import ValidationError
from django.conf import settings
from organizations.models import Organization
from django.utils import timezone

from PIL import Image
from io import BytesIO
from django.core.files.base import ContentFile
import os # <-- Thêm import này

MAX_STARTERS = 11

class Tournament(models.Model):
    class Status(models.TextChoices):
        REGISTRATION_OPEN = 'REGISTRATION_OPEN', 'Đang mở đăng ký'
        IN_PROGRESS = 'IN_PROGRESS', 'Đang diễn ra'
        FINISHED = 'FINISHED', 'Đã kết thúc'

    class Region(models.TextChoices):
        MIEN_BAC = 'MIEN_BAC', 'Miền Bắc'
        MIEN_TRUNG = 'MIEN_TRUNG', 'Miền Trung'
        MIEN_NAM = 'MIEN_NAM', 'Miền Nam'
        KHAC = 'KHAC', 'Khác'

    organization = models.ForeignKey(
        "organizations.Organization",
        on_delete=models.CASCADE,
        related_name='tournaments',
        verbose_name="Đơn vị tổ chức",
        null=True, blank=True
    )
    name = models.CharField(max_length=200)
    start_date = models.DateField()
    end_date = models.DateField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.REGISTRATION_OPEN)
    image = models.ImageField(upload_to='tournament_banners/', null=True, blank=True)
    region = models.CharField("Khu vực", max_length=20, choices=Region.choices, default=Region.KHAC)
    bank_name = models.CharField("Tên ngân hàng", max_length=100, blank=True)
    bank_account_number = models.CharField("Số tài khoản", max_length=50, blank=True)
    bank_account_name = models.CharField("Tên chủ tài khoản", max_length=100, blank=True)
    payment_qr_code = models.ImageField("Ảnh mã QR", upload_to='qr_codes/', null=True, blank=True)
    rules = models.TextField("Điều lệ & Thông báo", blank=True, help_text="Nhập các điều lệ, quy định hoặc thông báo của giải đấu tại đây. Bạn có thể sử dụng mã HTML cơ bản để định dạng.")

    gallery_url = models.URLField(
        "Link Album Ảnh Gốc",
        max_length=500,
        blank=True,
        null=True,
        help_text="Dán đường link chia sẻ của album ảnh Google Drive hoặc Google Photos tại đây."
    )
    followers = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='followed_tournaments', blank=True, verbose_name="Người theo dõi")
    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('tournament_detail', kwargs={'pk': self.pk})

class Group(models.Model):
    tournament = models.ForeignKey(Tournament, on_delete=models.CASCADE, related_name='groups')
    name = models.CharField(max_length=50)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["tournament", "name"], name="uniq_group_name_in_tournament")]

    def __str__(self):
        return f"{self.name} - {self.tournament.name}"

    def get_standings(self):
        standings = {}
        teams_in_group = self.teams.all()
        for team in teams_in_group:
            standings[team.id] = {'played': 0, 'wins': 0, 'draws': 0, 'losses': 0, 'gf': 0, 'ga': 0, 'gd': 0, 'points': 0, 'team_obj': team}
        matches_in_group = self.tournament.matches.filter(
            team1__in=teams_in_group, team2__in=teams_in_group,
            team1_score__isnull=False, team2_score__isnull=False
        )
        for match in matches_in_group:
            team1_id, team2_id, score1, score2 = match.team1.id, match.team2.id, match.team1_score, match.team2_score
            if team1_id in standings and team2_id in standings:
                standings[team1_id]['played'] += 1; standings[team2_id]['played'] += 1
                standings[team1_id]['gf'] += score1; standings[team1_id]['ga'] += score2
                standings[team2_id]['gf'] += score2; standings[team2_id]['ga'] += score1
                if score1 > score2:
                    standings[team1_id]['wins'] += 1; standings[team1_id]['points'] += 3
                    standings[team2_id]['losses'] += 1
                elif score2 > score1:
                    standings[team2_id]['wins'] += 1; standings[team2_id]['points'] += 3
                    standings[team1_id]['losses'] += 1
                else:
                    standings[team1_id]['draws'] += 1; standings[team1_id]['points'] += 1
                    standings[team2_id]['draws'] += 1; standings[team2_id]['points'] += 1
        sorted_standings = list(standings.values())
        for stats in sorted_standings:
            stats['gd'] = stats['gf'] - stats['ga']
        sorted_standings.sort(key=lambda x: (x['points'], x['gd'], x['gf']), reverse=True)
        return sorted_standings

class Team(models.Model):
    PAYMENT_STATUS_CHOICES = [('UNPAID', 'Chưa thanh toán'), ('PENDING', 'Chờ xác nhận'), ('PAID', 'Đã thanh toán')]
    tournament = models.ForeignKey(Tournament, on_delete=models.CASCADE, related_name='teams')
    name = models.CharField(max_length=100)
    coach_name = models.CharField(max_length=100, blank=True)
    captain = models.ForeignKey(User, on_delete=models.CASCADE, related_name='teams')
    group = models.ForeignKey(Group, on_delete=models.SET_NULL, null=True, blank=True, related_name='teams')
    logo = models.ImageField(upload_to='team_logos/', null=True, blank=True)
    main_photo = models.ImageField("Ảnh đại diện đội", upload_to='team_main_photos/', null=True, blank=True, help_text="Ảnh toàn đội sẽ hiển thị ở Phòng Truyền thống.")
    payment_status = models.CharField(max_length=10, choices=PAYMENT_STATUS_CHOICES, default='UNPAID')
    payment_proof = models.ImageField(upload_to='payment_proofs/', null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["tournament", "name"], name="uniq_team_name_in_tournament"),
            # === THÊM DÒNG NÀY VÀO ===
            models.UniqueConstraint(fields=["captain", "name"], name="unique_team_name_per_captain"),
        ]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if self.logo: self.logo = self.compress_image(self.logo)
        if self.payment_proof: self.payment_proof = self.compress_image(self.payment_proof)
        super().save(*args, **kwargs)

    def compress_image(self, image_field):
        # Tránh xử lý lại nếu file không thay đổi
        if not image_field._file: return image_field
        img = Image.open(image_field)
        if img.format == 'GIF': return image_field
        if img.mode in ('RGBA', 'P'): img = img.convert('RGB')
        buffer = BytesIO()
        if img.height > 1280 or img.width > 1280:
            img.thumbnail((1280, 1280))
        img.save(buffer, format='JPEG', quality=85, optimize=True)
        
        # === SỬA LỖI TẠI ĐÂY ===
        file_name = os.path.basename(image_field.name)
        new_image = ContentFile(buffer.getvalue(), name=file_name)
        return new_image

class Player(models.Model):
    FOOT_CHOICES = [('RIGHT', 'Phải'), ('LEFT', 'Trái'), ('BOTH', 'Cả hai')]
    POSITION_CHOICES = [('GK', 'Thủ môn'), ('DF', 'Hậu vệ'), ('MF', 'Tiền vệ'), ('FW', 'Tiền đạo')]
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='player_profile')
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='players')
    full_name = models.CharField(max_length=100)
    jersey_number = models.PositiveIntegerField()
    position = models.CharField(max_length=10, choices=POSITION_CHOICES)
    avatar = models.ImageField(upload_to='player_avatars/', null=True, blank=True)
    transfer_value = models.PositiveIntegerField("Giá trị chuyển nhượng (VNĐ)", default=0, help_text="Để 0 nếu chưa có định giá.")
    height = models.PositiveIntegerField("Chiều cao (cm)", null=True, blank=True)
    weight = models.PositiveIntegerField("Cân nặng (kg)", null=True, blank=True)
    preferred_foot = models.CharField("Chân thuận", max_length=5, choices=FOOT_CHOICES, blank=True)
    date_of_birth = models.DateField("Ngày sinh", null=True, blank=True)
    specialty_position = models.CharField("Vị trí sở trường", max_length=100, blank=True, help_text="Ví dụ: Tiền đạo cắm, Hậu vệ cánh trái...")
    agent_contact = models.CharField("Thông tin liên hệ (đại diện)", max_length=200, blank=True, help_text="Số điện thoại hoặc email của người đại diện.")
    votes = models.PositiveIntegerField("Số phiếu bình chọn", default=0)
    edit_count = models.PositiveIntegerField("Số lần chỉnh sửa", default=0, editable=False)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["team", "jersey_number"], name="uniq_jersey_per_team"),
            models.CheckConstraint(check=Q(jersey_number__gte=1) & Q(jersey_number__lte=99), name="jersey_between_1_99"),
        ]

    def __str__(self):
        return f"{self.full_name} (#{self.jersey_number})"
    
    def save(self, *args, **kwargs):
        if self.avatar and self.avatar._file:
            img = Image.open(self.avatar)
            if img.format != 'GIF':
                if img.mode in ('RGBA', 'P'): img = img.convert('RGB')
                buffer = BytesIO()
                if img.height > 800 or img.width > 800:
                    img.thumbnail((800, 800))
                img.save(buffer, format='JPEG', quality=85, optimize=True)
                
                # === SỬA LỖI TẠI ĐÂY ===
                file_name = os.path.basename(self.avatar.name)
                self.avatar = ContentFile(buffer.getvalue(), name=file_name)
        
        super().save(*args, **kwargs)

    def clean(self):
        if self.team_id and self.jersey_number is not None:
            exists = Player.objects.filter(team_id=self.team_id, jersey_number=self.jersey_number)
            if self.pk: exists = exists.exclude(pk=self.pk)
            if exists.exists():
                raise ValidationError({'jersey_number': 'Số áo đã tồn tại trong đội.'})


class Match(models.Model):
    ROUND_CHOICES = [
        ('GROUP', 'Vòng bảng'),
        ('QUARTER', 'Tứ kết'),
        ('SEMI', 'Bán kết'),
        ('THIRD_PLACE', 'Tranh Hạng Ba'), # <-- DÒNG MỚI
        ('FINAL', 'Chung kết'),
    ]

    tournament = models.ForeignKey(Tournament, on_delete=models.CASCADE, related_name='matches')
    match_round = models.CharField(max_length=20, choices=ROUND_CHOICES, default='GROUP') # Tăng max_length
    team1 = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='matches_as_team1')
    team2 = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='matches_as_team2')
    match_time = models.DateTimeField()
    location = models.CharField(max_length=200, blank=True)
    team1_score = models.PositiveIntegerField(null=True, blank=True)
    team2_score = models.PositiveIntegerField(null=True, blank=True)
    team1_penalty_score = models.PositiveIntegerField("Tỉ số penalty đội 1", null=True, blank=True)
    team2_penalty_score = models.PositiveIntegerField("Tỉ số penalty đội 2", null=True, blank=True)
    livestream_url = models.URLField(max_length=500, null=True, blank=True)
    referee = models.CharField(max_length=100, null=True, blank=True)
    commentator = models.CharField(max_length=100, null=True, blank=True)
    ticker_text = models.CharField(max_length=255, blank=True, help_text="Dòng chữ chạy trên màn hình livestream. Nếu để trống, hệ thống sẽ dùng thông báo mặc định.")
    # === BẮT ĐẦU THÊM 2 TRƯỜNG MỚI TẠI ĐÂY ===
    cover_photo = models.ImageField(
        "Ảnh bìa trận đấu",
        upload_to='match_covers/',
        null=True,
        blank=True,
        help_text="Ảnh đại diện hiển thị cho trận đấu trong thư viện ảnh."
    )
    gallery_url = models.URLField(
        "Link Album ảnh của trận đấu",
        max_length=500,
        null=True,
        blank=True,
        help_text="Dán đường link album ảnh (Google Photos, Facebook,...) của riêng trận đấu này."
    )
    def get_absolute_url(self):
        return reverse("match_detail", kwargs={"pk": self.pk})

    def __str__(self):
        return f"{self.team1.name} vs {self.team2.name}"

    @property
    def winner(self):
        if self.team1_score is not None and self.team2_score is not None:
            if self.team1_score > self.team2_score:
                return self.team1
            elif self.team2_score > self.team1_score:
                return self.team2
            # Xử lý trường hợp hòa và có tỉ số penalty
            elif self.team1_penalty_score is not None and self.team2_penalty_score is not None:
                if self.team1_penalty_score > self.team2_penalty_score:
                    return self.team1
                elif self.team2_penalty_score > self.team1_penalty_score:
                    return self.team2
        return None

    @property
    def loser(self):
        if self.winner is not None:
            return self.team2 if self.winner == self.team1 else self.team1
        return None

    # Điều kiện đồng hồ
    @property
    def is_live(self):
        """Kiểm tra xem trận đấu có đang diễn ra không."""
        now = timezone.now()
        # Giả sử một trận đấu kéo dài 2 tiếng (120 phút)
        return self.match_time <= now < self.match_time + timedelta(minutes=120)

class Lineup(models.Model):
    STATUS_CHOICES = [('STARTER', 'Đá chính'), ('SUBSTITUTE', 'Dự bị')]
    match = models.ForeignKey(Match, on_delete=models.CASCADE, related_name='lineups')
    player = models.ForeignKey(Player, on_delete=models.CASCADE, related_name='lineups')
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='+')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES)

    class Meta:
        unique_together = ('match', 'player')

    def __str__(self):
        return f"{self.player.full_name} ({self.status}) for {self.match}"

    def clean(self):
        if self.team_id not in [self.match.team1_id, self.match.team2_id]: raise ValidationError("Đội không thuộc trận này.")
        if self.player.team_id != self.team_id: raise ValidationError("Cầu thủ không thuộc đội này.")
        if self.status == "STARTER":
            qs = Lineup.objects.filter(match=self.match, team=self.team, status="STARTER")
            if self.pk: qs = qs.exclude(pk=self.pk)
            if qs.count() >= MAX_STARTERS: raise ValidationError(f"Tối đa {MAX_STARTERS} cầu thủ đá chính cho mỗi đội.")

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

class Goal(models.Model):
    match = models.ForeignKey(Match, on_delete=models.CASCADE, related_name='goals')
    player = models.ForeignKey(Player, on_delete=models.CASCADE, related_name='goals')
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='goals')
    minute = models.PositiveIntegerField(null=True, blank=True)
    # --- THÊM DÒNG MỚI NÀY VÀO ---
    is_own_goal = models.BooleanField("Bàn phản lưới?", default=False)
    created_at = models.DateTimeField(default=timezone.now)
    # -----------------------------
    class Meta:
        constraints = [models.CheckConstraint(check=Q(minute__gte=0) & Q(minute__lte=150), name="goal_minute_range")]
    def clean(self):
        if self.team_id is None and self.player_id: self.team_id = self.player.team_id
        if hasattr(self, 'match'):
            if self.team_id not in [self.match.team1_id, self.match.team2_id]: raise ValidationError("Đội ghi bàn không thuộc trận.")
            if self.player_id and self.player.team_id != self.team_id: raise ValidationError("Cầu thủ ghi bàn không thuộc đội.")
    def save(self, *args, **kwargs):
        if self.team_id is None and self.player_id: self.team_id = self.player.team_id
        self.full_clean()
        return super().save(*args, **kwargs)
    def __str__(self):
        return f"Goal by {self.player.full_name} in {self.match}"

class Card(models.Model):
    CARD_CHOICES = [('YELLOW', 'Thẻ vàng'), ('RED', 'Thẻ đỏ')]
    match = models.ForeignKey(Match, on_delete=models.CASCADE, related_name='cards')
    player = models.ForeignKey(Player, on_delete=models.CASCADE, related_name='cards')
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='cards')
    card_type = models.CharField(max_length=10, choices=CARD_CHOICES)
    minute = models.PositiveIntegerField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    class Meta:
        constraints = [models.CheckConstraint(check=Q(minute__gte=0) & Q(minute__lte=150), name="card_minute_range")]
    def clean(self):
        if self.team_id is None and self.player_id: self.team_id = self.player.team_id
        if hasattr(self, 'match'):
            if self.team_id not in [self.match.team1_id, self.match.team2_id]: raise ValidationError("Đội nhận thẻ không thuộc trận.")
            if self.player_id and self.player.team_id != self.team_id: raise ValidationError("Cầu thủ nhận thẻ không thuộc đội.")
    def save(self, *args, **kwargs):
        if self.team_id is None and self.player_id: self.team_id = self.player.team_id
        self.full_clean()
        return super().save(*args, **kwargs)
    def __str__(self):
        return f"{self.get_card_type_display()} for {self.player.full_name} in {self.match}"

class HomeBanner(models.Model):
    title = models.CharField(max_length=120)
    subtitle = models.CharField(max_length=200, blank=True)
    button_text = models.CharField(max_length=40, blank=True)
    button_url = models.URLField(blank=True)
    image = models.ImageField(upload_to='banners/')
    order = models.PositiveIntegerField(default=0, help_text="Thứ tự hiển thị, nhỏ trước")
    is_active = models.BooleanField(default=True)
    start_at = models.DateTimeField(null=True, blank=True)
    end_at = models.DateTimeField(null=True, blank=True)
    class Meta:
        ordering = ("order", "id")
    def __str__(self):
        return f"{self.title} (#{self.order})"

class Comment(models.Model):
    match = models.ForeignKey(Match, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='comments')
    text = models.TextField(max_length=500)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        ordering = ['created_at']
    def __str__(self):
        return f'Comment by {self.user.username} on {self.match}'

class Announcement(models.Model):
    AUDIENCE_CHOICES = [('PUBLIC', 'Gửi cho Mọi người (Cầu thủ & Đội trưởng)'), ('CAPTAINS_ONLY', 'Chỉ gửi cho Đội trưởng')]
    audience = models.CharField("Đối tượng", max_length=15, choices=AUDIENCE_CHOICES, default='PUBLIC', help_text="Chọn nhóm người dùng sẽ thấy thông báo này.")
    tournament = models.ForeignKey(Tournament, on_delete=models.CASCADE, related_name='announcements')
    title = models.CharField("Tiêu đề", max_length=200)
    content = models.TextField("Nội dung")
    created_at = models.DateTimeField(auto_now_add=True)
    is_published = models.BooleanField("Công khai", default=True, help_text="Bỏ chọn nếu đây là bản nháp.")
    read_by = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='read_announcements', blank=True, verbose_name="Đã đọc bởi")
    class Meta:
        ordering = ['-created_at']
    def __str__(self):
        return self.title

# === BẮT ĐẦU THÊM MODEL MỚI TẠI ĐÂY ===
class TournamentPhoto(models.Model):
    """Lưu trữ một ảnh trong thư viện của giải đấu."""
    tournament = models.ForeignKey(
        Tournament, 
        on_delete=models.CASCADE, 
        related_name='photos',
        verbose_name="Giải đấu"
    )
    image = models.ImageField("Ảnh", upload_to='tournament_photos/')
    caption = models.CharField("Chú thích", max_length=200, blank=True)
    uploaded_at = models.DateTimeField("Ngày tải lên", auto_now_add=True)

    class Meta:
        ordering = ['-uploaded_at']
        verbose_name = "Ảnh Giải đấu"
        verbose_name_plural = "Thư viện ảnh Giải đấu"

    def __str__(self):
        return f"Ảnh của giải {self.tournament.name} - {self.pk}"

    def save(self, *args, **kwargs):
        # Tối ưu ảnh trước khi lưu (giống như model Player/Team)
        if self.image and self.image._file:
            img = Image.open(self.image)
            if img.format != 'GIF':
                if img.mode in ('RGBA', 'P'):
                    img = img.convert('RGB')
                
                buffer = BytesIO()
                # Giảm kích thước ảnh lớn hơn 2K
                if img.height > 1920 or img.width > 1920:
                    img.thumbnail((1920, 1920))
                
                img.save(buffer, format='JPEG', quality=85, optimize=True)
                
                file_name = os.path.basename(self.image.name)
                self.image = ContentFile(buffer.getvalue(), name=file_name)

        super().save(*args, **kwargs)

# === BẮT ĐẦU THÊM MODEL MỚI ===
class Notification(models.Model):
    """
    Lưu trữ các thông báo tự động được tạo bởi hệ thống.
    """
    # Các loại thông báo, có thể mở rộng sau này
    class NotificationType(models.TextChoices):
        MATCH_RESULT = 'MATCH_RESULT', 'Kết quả trận đấu'
        NEW_TEAM = 'NEW_TEAM', 'Đội mới đăng ký'
        DRAW_COMPLETE = 'DRAW_COMPLETE', 'Bốc thăm hoàn tất'  
        SCHEDULE_CREATED = 'SCHEDULE_CREATED', 'Lịch thi đấu mới' 
        VOTE_AWARDED = 'VOTE_AWARDED', 'Nhận phiếu bầu'
        GENERIC = 'GENERIC', 'Thông báo chung'

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField("Tiêu đề", max_length=255)
    message = models.TextField("Nội dung")
    notification_type = models.CharField(
        "Loại thông báo",
        max_length=20,
        choices=NotificationType.choices,
        default=NotificationType.GENERIC
    )
    is_read = models.BooleanField("Đã đọc", default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    related_url = models.URLField("Link liên quan", max_length=500, null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        # === BẮT ĐẦU THÊM MỚI ===
        indexes = [
            models.Index(fields=['user', 'is_read']),
        ]
        # === KẾT THÚC THÊM MỚI ===

    def __str__(self):
        return f"Thông báo cho {self.user.username}: {self.title}"

# === THÊM MODEL MỚI VÀO CUỐI FILE ===
class TeamAchievement(models.Model):
    """
    Lưu trữ một thành tích mà một đội bóng đạt được trong một giải đấu.
    """
    ACHIEVEMENT_CHOICES = [
        ('CHAMPION', 'Vô địch'),
        ('RUNNER_UP', 'Á quân'),
        ('THIRD_PLACE', 'Hạng ba'),
        ('FAIR_PLAY', 'Giải Phong cách / Fair Play'),
        ('OTHER', 'Khác'),
    ]

    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='achievements', verbose_name="Đội bóng")
    tournament = models.ForeignKey(Tournament, on_delete=models.CASCADE, related_name='team_achievements', verbose_name="Giải đấu")
    achievement_type = models.CharField("Loại danh hiệu", max_length=20, choices=ACHIEVEMENT_CHOICES)
    description = models.CharField("Mô tả (tùy chọn)", max_length=255, blank=True, help_text="Ghi rõ hơn về danh hiệu, ví dụ: 'Vô địch mùa giải 2025'")
    achieved_at = models.DateField("Ngày đạt được", default=timezone.now)

    class Meta:
        ordering = ['-achieved_at']
        verbose_name = "Thành tích Đội bóng"
        verbose_name_plural = "Thành tích Đội bóng"
        unique_together = ('team', 'tournament', 'achievement_type') # Đảm bảo mỗi đội chỉ có 1 danh hiệu/giải

    def __str__(self):
        return f"{self.team.name} - {self.get_achievement_type_display()} tại {self.tournament.name}"

# === THÊM MODEL MỚI VÀO CUỐI FILE ===
class Substitution(models.Model):
    """Lưu trữ một sự kiện thay người trong trận đấu."""
    match = models.ForeignKey(Match, on_delete=models.CASCADE, related_name='substitutions', verbose_name="Trận đấu")
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='substitutions', verbose_name="Đội")
    player_in = models.ForeignKey(Player, on_delete=models.CASCADE, related_name='substitutions_in', verbose_name="Cầu thủ vào sân")
    player_out = models.ForeignKey(Player, on_delete=models.CASCADE, related_name='substitutions_out', verbose_name="Cầu thủ ra sân")
    minute = models.PositiveIntegerField("Phút", null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['minute']
        verbose_name = "Lượt thay người"
        verbose_name_plural = "Các lượt thay người"

    def __str__(self):
        return f"{self.player_in.full_name} vào thay {self.player_out.full_name} ở phút {self.minute}'"

    def clean(self):
        # Tự động gán đội dựa trên cầu thủ vào sân
        if self.player_in_id and not self.team_id:
            self.team = self.player_in.team
        
        # Kiểm tra tính hợp lệ
        if self.player_in and self.player_out and self.player_in.team != self.player_out.team:
            raise ValidationError("Cầu thủ vào và ra phải cùng một đội.")
        if self.player_in == self.player_out:
            raise ValidationError("Cầu thủ vào và ra không được là một.")
            
        # === SỬA LỖI TẠI ĐÂY ===
        # Chỉ kiểm tra khi đối tượng match đã được gán
        if hasattr(self, 'match'):
            if self.team_id not in [self.match.team1_id, self.match.team2_id]:
                raise ValidationError("Đội thay người không thuộc trận đấu này.")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

# === Sự kiện các mốc thời gian ===
class MatchEvent(models.Model):
    """Lưu trữ các sự kiện mốc thời gian của trận đấu."""
    class EventType(models.TextChoices):
        MATCH_START = 'MATCH_START', 'Trận đấu bắt đầu'
        HALF_TIME = 'HALF_TIME', 'Hết hiệp 1'
        MATCH_END = 'MATCH_END', 'Trận đấu kết thúc'
        EXTRA_TIME_START = 'EXTRA_TIME_START', 'Hiệp phụ bắt đầu'
        PENALTY_SHOOTOUT_START = 'PENALTY_SHOOTOUT_START', 'Loạt sút luân lưu'

    match = models.ForeignKey(Match, on_delete=models.CASCADE, related_name='events')
    event_type = models.CharField("Loại sự kiện", max_length=30, choices=EventType.choices)
    text = models.CharField("Nội dung hiển thị", max_length=255)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['created_at']
        verbose_name = "Sự kiện trận đấu"
        verbose_name_plural = "Các sự kiện trận đấu"

    def __str__(self):
        return f"{self.get_event_type_display()} - {self.match}"        