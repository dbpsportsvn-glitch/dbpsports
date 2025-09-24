# backend/tournaments/context_processors.py

from .models import Team, Player, Announcement, Notification
from django.db.models import Q

def unread_announcements_count(request):
    """
    Đếm số lượng tin tức từ BTC (Announcements) mà người dùng chưa đọc.
    """
    if not request.user.is_authenticated:
        return {'unread_announcements_count': 0}

    tournament_ids_as_captain = set(
        Team.objects.filter(captain=request.user).values_list('tournament_id', flat=True)
    )
    tournament_ids_as_player = set(
        Player.objects.filter(user=request.user).values_list('team__tournament_id', flat=True)
    )
    tournament_ids_as_follower = set(
        request.user.followed_tournaments.values_list('id', flat=True)
    )
    all_relevant_ids = tournament_ids_as_captain.union(tournament_ids_as_player, tournament_ids_as_follower)

    if not all_relevant_ids:
        return {'unread_announcements_count': 0}

    q_public = Q(audience='PUBLIC', tournament_id__in=all_relevant_ids)
    q_captains_only = Q()
    if tournament_ids_as_captain:
        q_captains_only = Q(audience='CAPTAINS_ONLY', tournament_id__in=tournament_ids_as_captain)
    
    count = Announcement.objects.filter(
        q_public | q_captains_only,
        is_published=True
    ).exclude(
        read_by=request.user
    ).distinct().count()

    return {'unread_announcements_count': count}


def unread_notifications_count(request):
    """
    Đếm số lượng thông báo tự động (Notifications) mà người dùng chưa đọc.
    """
    if not request.user.is_authenticated:
        return {'unread_notifications_count': 0}

    count = Notification.objects.filter(user=request.user, is_read=False).count()
    
    return {'unread_notifications_count': count}