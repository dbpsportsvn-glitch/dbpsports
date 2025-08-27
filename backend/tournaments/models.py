# tournaments/models.py

from django.db import models
from django.contrib.auth.models import User # <-- Thêm dòng import này

class Tournament(models.Model):
    name = models.CharField(max_length=200)
    start_date = models.DateField()
    end_date = models.DateField()

    def __str__(self):
        return self.name

# === THÊM HAI CLASS DƯỚI ĐÂY ===

class Team(models.Model):
    tournament = models.ForeignKey(Tournament, on_delete=models.CASCADE, related_name='teams')
    name = models.CharField(max_length=100)
    coach_name = models.CharField(max_length=100, blank=True)
    # Thêm dòng dưới đây để lưu lại ai là đội trưởng
    captain = models.ForeignKey(User, on_delete=models.CASCADE, related_name='teams')
    logo = models.ImageField(upload_to='team_logos/', null=True, blank=True)

    def __str__(self):
        return self.name

class Player(models.Model):
    # Kết nối với đội bóng: một đội có nhiều cầu thủ
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='players')
    full_name = models.CharField(max_length=100)
    jersey_number = models.PositiveIntegerField()
    position = models.CharField(max_length=50) # Ví dụ: Thủ môn, Hậu vệ...

    def __str__(self):
        return f"{self.full_name} (#{self.jersey_number})"


class Match(models.Model):
    tournament = models.ForeignKey(Tournament, on_delete=models.CASCADE, related_name='matches')
    team1 = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='matches_as_team1')
    team2 = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='matches_as_team2')
    match_time = models.DateTimeField()
    location = models.CharField(max_length=200, blank=True)
    team1_score = models.PositiveIntegerField(null=True, blank=True)
    team2_score = models.PositiveIntegerField(null=True, blank=True)

    def __str__(self):
        return f"{self.team1.name} vs {self.team2.name} at {self.tournament.name}"

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
        # Đảm bảo một cầu thủ không thể được đăng ký hai lần cho cùng một trận đấu
        unique_together = ('match', 'player')

    def __str__(self):
        return f"{self.player.full_name} ({self.status}) for {self.match}"        