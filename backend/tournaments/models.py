# tournaments/models.py

from django.db import models
from django.contrib.auth.models import User # <-- Thêm dòng import này

class Tournament(models.Model):
    name = models.CharField(max_length=200)
    start_date = models.DateField()
    end_date = models.DateField()

    def __str__(self):
        return self.name

    def get_standings(self):
        standings = {}
        # Khởi tạo thông số cho tất cả các đội trong giải
        for team in self.teams.all():
            standings[team.id] = {  # Sử dụng ID của đội để tránh nhầm lẫn
                'played': 0, 'wins': 0, 'draws': 0, 'losses': 0,
                'gf': 0, 'ga': 0, 'gd': 0, 'points': 0, 'team_obj': team
            }

        # Lặp qua tất cả các trận đấu của giải đã có tỉ số
        for match in self.matches.filter(team1_score__isnull=False, team2_score__isnull=False):
            team1_id = match.team1.id
            team2_id = match.team2.id
            score1 = match.team1_score
            score2 = match.team2_score

            # Cập nhật thông số cho cả hai đội
            if team1_id in standings and team2_id in standings:
                # Trận đã chơi
                standings[team1_id]['played'] += 1
                standings[team2_id]['played'] += 1
                # Bàn thắng, bàn thua
                standings[team1_id]['gf'] += score1
                standings[team1_id]['ga'] += score2
                standings[team2_id]['gf'] += score2
                standings[team2_id]['ga'] += score1

                # Tính điểm
                if score1 > score2: # Đội 1 thắng
                    standings[team1_id]['wins'] += 1
                    standings[team1_id]['points'] += 3
                    standings[team2_id]['losses'] += 1
                elif score2 > score1: # Đội 2 thắng
                    standings[team2_id]['wins'] += 1
                    standings[team2_id]['points'] += 3
                    standings[team1_id]['losses'] += 1
                else: # Hòa
                    standings[team1_id]['draws'] += 1
                    standings[team1_id]['points'] += 1
                    standings[team2_id]['draws'] += 1
                    standings[team2_id]['points'] += 1 # <-- Lỗi đã được sửa ở đây

        # Chuyển từ dictionary sang list và tính hiệu số
        sorted_standings = []
        for team_id, stats in standings.items():
            stats['gd'] = stats['gf'] - stats['ga']
            sorted_standings.append(stats)

        # Sắp xếp bảng xếp hạng: ưu tiên điểm, rồi đến hiệu số, rồi đến bàn thắng
        sorted_standings.sort(key=lambda x: (x['points'], x['gd'], x['gf']), reverse=True)

        return sorted_standings

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