# Dán toàn bộ code này để thay thế nội dung file backend/tournaments/context_processors.py

from .models import Team, Player, Announcement, Notification, TeamRegistration
from django.db.models import Q
from shop.models import Cart

def unread_announcements_count(request):
    """
    Đếm số lượng tin tức từ BTC (Announcements) mà người dùng chưa đọc.
    """
    if not request.user.is_authenticated:
        return {'unread_announcements_count': 0}

    # SỬA LỖI: Truy vấn qua TeamRegistration để lấy ID giải đấu
    tournament_ids_as_captain = set(
        TeamRegistration.objects.filter(team__captain=request.user).values_list('tournament_id', flat=True)
    )

    # SỬA LỖI: Truy vấn qua TeamRegistration để lấy ID giải đấu
    tournament_ids_as_player = set(
        TeamRegistration.objects.filter(team__players__user=request.user).values_list('tournament_id', flat=True)
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


def user_cart_context(request):
    """
    Thêm cart của user vào context cho tất cả template
    """
    if not request.user.is_authenticated:
        return {'user_cart': None}
    
    try:
        cart = Cart.objects.get(user=request.user)
        return {'user_cart': cart}
    except Cart.DoesNotExist:
        return {'user_cart': None}