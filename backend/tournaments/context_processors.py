# backend/tournaments/context_processors.py

from .models import Team, Player, Announcement
from django.db.models import Q

def unread_announcements_count(request):
    if not request.user.is_authenticated:
        return {'unread_announcements_count': 0}

    # Lấy danh sách ID các giải đấu mà người dùng là đội trưởng
    tournament_ids_as_captain = set(
        Team.objects.filter(captain=request.user).values_list('tournament_id', flat=True)
    )
    
    # Lấy danh sách ID các giải đấu mà người dùng là cầu thủ
    tournament_ids_as_player = set(
        Player.objects.filter(user=request.user).values_list('team__tournament_id', flat=True)
    )
    
    all_relevant_ids = tournament_ids_as_captain.union(tournament_ids_as_player)

    if not all_relevant_ids:
        return {'unread_announcements_count': 0}

    # Các thông báo công khai mà người dùng có liên quan
    q_public = Q(audience='PUBLIC', tournament_id__in=all_relevant_ids)
    
    # Các thông báo chỉ dành cho đội trưởng
    q_captains_only = Q()
    if tournament_ids_as_captain:
        q_captains_only = Q(audience='CAPTAINS_ONLY', tournament_id__in=tournament_ids_as_captain)
    
    # Đếm các thông báo thỏa mãn điều kiện VÀ người dùng chưa đọc
    count = Announcement.objects.filter(
        q_public | q_captains_only,
        is_published=True
    ).exclude(
        read_by=request.user
    ).count()

    return {'unread_announcements_count': count}