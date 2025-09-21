# File: backend/tournaments/models.py

from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse
from django.db.models import Q
from django.core.exceptions import ValidationError
from django.conf import settings
from organizations.models import Organization

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

    def __str__(self):
        return self.name

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
    payment_status = models.CharField(max_length=10, choices=PAYMENT_STATUS_CHOICES, default='UNPAID')
    payment_proof = models.ImageField(upload_to='payment_proofs/', null=True, blank=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["tournament", "name"], name="uniq_team_name_in_tournament")]

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
    POSITION_CHOICES = [('GK', 'Thủ môn'), ('DF', 'Hậu vệ'), ('MF', 'Tiền vệ'), ('FW', 'Tiền đạo')]
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='player_profile')
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='players')
    full_name = models.CharField(max_length=100)
    jersey_number = models.PositiveIntegerField()
    position = models.CharField(max_length=10, choices=POSITION_CHOICES)
    avatar = models.ImageField(upload_to='player_avatars/', null=True, blank=True)

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
    ROUND_CHOICES = [('GROUP', 'Vòng bảng'), ('QUARTER', 'Tứ kết'), ('SEMI', 'Bán kết'), ('FINAL', 'Chung kết')]
    tournament = models.ForeignKey(Tournament, on_delete=models.CASCADE, related_name='matches')
    match_round = models.CharField(max_length=10, choices=ROUND_CHOICES, default='GROUP')
    team1 = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='matches_as_team1')
    team2 = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='matches_as_team2')
    match_time = models.DateTimeField()
    location = models.CharField(max_length=200, blank=True)
    team1_score = models.PositiveIntegerField(null=True, blank=True)
    team2_score = models.PositiveIntegerField(null=True, blank=True)
    livestream_url = models.URLField(max_length=500, null=True, blank=True)
    referee = models.CharField(max_length=100, null=True, blank=True)
    commentator = models.CharField(max_length=100, null=True, blank=True)
    ticker_text = models.CharField(max_length=255, blank=True, help_text="Dòng chữ chạy trên màn hình livestream. Nếu để trống, hệ thống sẽ dùng thông báo mặc định.")

    def get_absolute_url(self):
        return reverse("match_detail", kwargs={"pk": self.pk})

    def __str__(self):
        return f"{self.team1.name} vs {self.team2.name}"

    @property
    def winner(self):
        if self.team1_score is not None and self.team2_score is not None:
            if self.team1_score > self.team2_score: return self.team1
            elif self.team2_score > self.team1_score: return self.team2
        return None

class Lineup(models.Model):
    STATUS_CHOICES = [('STARTER', 'Đá chính'), ('SUBSTITUTE', 'Dự bị')]
    match = models.ForeignKey(Match, on_delete=models.CASCADE, related_name='lineups')
    player = models.ForeignKey(Player, on_delete=models.CASCADE, related_name='lineups')
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='lineups')
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