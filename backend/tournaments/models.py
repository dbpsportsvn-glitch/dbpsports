# tournaments/models.py

from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse
from django.db.models import Q
from django.core.exceptions import ValidationError

MAX_STARTERS = 11  # số cầu thủ đá chính tối đa cho mỗi đội trong một trận

# --- Model Tournament ---
class Tournament(models.Model):
    STATUS_CHOICES = [
        ('REGISTRATION_OPEN', 'Đang mở đăng ký'),
        ('IN_PROGRESS', 'Đang diễn ra'),
        ('FINISHED', 'Đã kết thúc'),
    ]

    name = models.CharField(max_length=200)
    start_date = models.DateField()
    end_date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='REGISTRATION_OPEN')
    image = models.ImageField(upload_to='tournament_banners/', null=True, blank=True)

    def __str__(self):
        return self.name

# --- Model Group ---
class Group(models.Model):
    tournament = models.ForeignKey(Tournament, on_delete=models.CASCADE, related_name='groups')
    name = models.CharField(max_length=50)  # Ví dụ: "Bảng A", "Bảng B"

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["tournament", "name"],
                name="uniq_group_name_in_tournament",
            ),
        ]

    def __str__(self):
        return f"{self.name} - {self.tournament.name}"

    def get_standings(self):
        standings = {}
        teams_in_group = self.teams.all()

        for team in teams_in_group:
            standings[team.id] = {
                'played': 0, 'wins': 0, 'draws': 0, 'losses': 0,
                'gf': 0, 'ga': 0, 'gd': 0, 'points': 0, 'team_obj': team
            }

        matches_in_group = self.tournament.matches.filter(
            team1__in=teams_in_group,
            team2__in=teams_in_group,
            team1_score__isnull=False,
            team2_score__isnull=False
        )

        for match in matches_in_group:
            team1_id = match.team1.id
            team2_id = match.team2.id
            score1 = match.team1_score
            score2 = match.team2_score

            if team1_id in standings and team2_id in standings:
                standings[team1_id]['played'] += 1
                standings[team2_id]['played'] += 1
                standings[team1_id]['gf'] += score1
                standings[team1_id]['ga'] += score2
                standings[team2_id]['gf'] += score2
                standings[team2_id]['ga'] += score1

                if score1 > score2:
                    standings[team1_id]['wins'] += 1
                    standings[team1_id]['points'] += 3
                    standings[team2_id]['losses'] += 1
                elif score2 > score1:
                    standings[team2_id]['wins'] += 1
                    standings[team2_id]['points'] += 3
                    standings[team1_id]['losses'] += 1
                else:
                    standings[team1_id]['draws'] += 1
                    standings[team1_id]['points'] += 1
                    standings[team2_id]['draws'] += 1
                    standings[team2_id]['points'] += 1

        sorted_standings = list(standings.values())
        for stats in sorted_standings:
            stats['gd'] = stats['gf'] - stats['ga']

        sorted_standings.sort(key=lambda x: (x['points'], x['gd'], x['gf']), reverse=True)

        return sorted_standings

# --- Model Team ---
class Team(models.Model):
    PAYMENT_STATUS_CHOICES = [
        ('UNPAID', 'Chưa thanh toán'),
        ('PENDING', 'Chờ xác nhận'),
        ('PAID', 'Đã thanh toán'),
    ]

    tournament = models.ForeignKey(Tournament, on_delete=models.CASCADE, related_name='teams')
    name = models.CharField(max_length=100)
    coach_name = models.CharField(max_length=100, blank=True)
    captain = models.ForeignKey(User, on_delete=models.CASCADE, related_name='teams')
    group = models.ForeignKey(Group, on_delete=models.SET_NULL, null=True, blank=True, related_name='teams')
    logo = models.ImageField(upload_to='team_logos/', null=True, blank=True)
    payment_status = models.CharField(max_length=10, choices=PAYMENT_STATUS_CHOICES, default='UNPAID')
    payment_proof = models.ImageField(upload_to='payment_proofs/', null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["tournament", "name"],
                name="uniq_team_name_in_tournament",
            ),
        ]

    def __str__(self):
        return self.name

# --- Model Player ---
class Player(models.Model):
    POSITION_CHOICES = [
        ('GK', 'Thủ môn'),
        ('DF', 'Hậu vệ'),
        ('MF', 'Tiền vệ'),
        ('FW', 'Tiền đạo'),
    ]

    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='players')
    full_name = models.CharField(max_length=100)
    jersey_number = models.PositiveIntegerField()
    position = models.CharField(max_length=10, choices=POSITION_CHOICES)
    avatar = models.ImageField(upload_to='player_avatars/', null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["team", "jersey_number"],
                name="uniq_jersey_per_team",
            ),
            models.CheckConstraint(
                check=Q(jersey_number__gte=1) & Q(jersey_number__lte=99),
                name="jersey_between_1_99",
            ),
        ]

    def __str__(self):
        return f"{self.full_name} (#{self.jersey_number})"

# --- Model Match ---

    def clean(self):
        # Tránh trùng số áo trong cùng đội
        if self.team_id and self.jersey_number is not None:
            exists = Player.objects.filter(team_id=self.team_id, jersey_number=self.jersey_number)
            if self.pk:
                exists = exists.exclude(pk=self.pk)
            if exists.exists():
                raise ValidationError({'jersey_number': 'Số áo đã tồn tại trong đội.'})

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)
class Match(models.Model):
    ROUND_CHOICES = [
        ('GROUP', 'Vòng bảng'),
        ('QUARTER', 'Tứ kết'),
        ('SEMI', 'Bán kết'),
        ('FINAL', 'Chung kết'),
    ]

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

    def get_absolute_url(self):
        return reverse("match_detail", kwargs={"pk": self.pk})

    def __str__(self):
        return f"{self.team1.name} vs {self.team2.name}"

# --- Model Lineup ---
class Lineup(models.Model):
    STATUS_CHOICES = [
        ('STARTER', 'Đá chính'),
        ('SUBSTITUTE', 'Dự bị'),
    ]

    match = models.ForeignKey(Match, on_delete=models.CASCADE, related_name='lineups')
    player = models.ForeignKey(Player, on_delete=models.CASCADE, related_name='lineups')
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='lineups')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES)

    class Meta:
        unique_together = ('match', 'player')

    def __str__(self):
        return f"{self.player.full_name} ({self.status}) for {self.match}"

    def clean(self):
        # Đội phải tham gia trận
        if self.team_id not in [self.match.team1_id, self.match.team2_id]:
            raise ValidationError("Đội không thuộc trận này.")
        # Cầu thủ phải thuộc đội
        if self.player.team_id != self.team_id:
            raise ValidationError("Cầu thủ không thuộc đội này.")
        # Tối đa 11 đá chính
        if self.status == "STARTER":
            qs = Lineup.objects.filter(match=self.match, team=self.team, status="STARTER")
            if self.pk:
                qs = qs.exclude(pk=self.pk)
            if qs.count() >= MAX_STARTERS:
                raise ValidationError(f"Tối đa {MAX_STARTERS} cầu thủ đá chính cho mỗi đội.")

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

# --- Model Goal ---
class Goal(models.Model):
    match = models.ForeignKey(Match, on_delete=models.CASCADE, related_name='goals')
    player = models.ForeignKey(Player, on_delete=models.CASCADE, related_name='goals')
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='goals')
    minute = models.PositiveIntegerField(null=True, blank=True)  # Thời điểm ghi bàn (tùy chọn)

    class Meta:
        constraints = [
            models.CheckConstraint(
                check=Q(minute__gte=0) & Q(minute__lte=150),
                name="goal_minute_range",
            ),
        ]

    
    def clean(self):
        # Tự điền team theo cầu thủ nếu để trống
        if self.team_id is None and self.player_id:
            self.team_id = self.player.team_id
        # Kiểm tra thuộc trận và khớp đội
        if self.team_id not in [self.match.team1_id, self.match.team2_id]:
            raise ValidationError("Đội ghi bàn không thuộc trận.")
        if self.player_id and self.player.team_id != self.team_id:
            raise ValidationError("Cầu thủ ghi bàn không thuộc đội.")

    def save(self, *args, **kwargs):
        if self.team_id is None and self.player_id:
            self.team_id = self.player.team_id
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self):
        return f"Goal by {self.player.full_name} in {self.match}"

# --- Model Card ---
class Card(models.Model):
    CARD_CHOICES = [
        ('YELLOW', 'Thẻ vàng'),
        ('RED', 'Thẻ đỏ'),
    ]

    match = models.ForeignKey(Match, on_delete=models.CASCADE, related_name='cards')
    player = models.ForeignKey(Player, on_delete=models.CASCADE, related_name='cards')
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='cards')
    card_type = models.CharField(max_length=10, choices=CARD_CHOICES)
    minute = models.PositiveIntegerField(null=True, blank=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                check=Q(minute__gte=0) & Q(minute__lte=150),
                name="card_minute_range",
            ),
        ]

    def clean(self):
        # Tự điền team theo cầu thủ nếu để trống
        if self.team_id is None and self.player_id:
            self.team_id = self.player.team_id
        # Kiểm tra thuộc trận và khớp đội
        if self.team_id not in [self.match.team1_id, self.match.team2_id]:
            raise ValidationError("Đội nhận thẻ không thuộc trận.")
        if self.player_id and self.player.team_id != self.team_id:
            raise ValidationError("Cầu thủ nhận thẻ không thuộc đội.")

    def save(self, *args, **kwargs):
        if self.team_id is None and self.player_id:
            self.team_id = self.player.team_id
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.get_card_type_display()} for {self.player.full_name} in {self.match}"

# --- Home Banner ---
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
