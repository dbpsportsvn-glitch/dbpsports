# tournaments/models.py

from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse

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
    name = models.CharField(max_length=50) # Ví dụ: "Bảng A", "Bảng B"

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

    def __str__(self):
        return self.name

# --- Model Player ---
class Player(models.Model):
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='players')
    full_name = models.CharField(max_length=100)
    jersey_number = models.PositiveIntegerField()
    position = models.CharField(max_length=50)
    avatar = models.ImageField(upload_to='player_avatars/', null=True, blank=True)

    def __str__(self):
        return f"{self.full_name} (#{self.jersey_number})"

# --- Model Match ---
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

class Goal(models.Model):
    match = models.ForeignKey(Match, on_delete=models.CASCADE, related_name='goals')
    player = models.ForeignKey(Player, on_delete=models.CASCADE, related_name='goals')
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='goals')
    minute = models.PositiveIntegerField(null=True, blank=True) # Thời điểm ghi bàn (tùy chọn)

    def __str__(self):
        return f"Goal by {self.player.full_name} in {self.match}"       

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

    def __str__(self):
        return f"{self.get_card_type_display()} for {self.player.full_name} in {self.match}"         