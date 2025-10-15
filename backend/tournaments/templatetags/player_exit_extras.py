# backend/tournaments/templatetags/player_exit_extras.py

from django import template
from ..models import PlayerTeamExit

register = template.Library()


@register.simple_tag
def has_pending_exit_request(player):
    """
    Kiểm tra xem cầu thủ có yêu cầu rời đội đang chờ xử lý không
    """
    if not player:
        return False
    
    return PlayerTeamExit.objects.filter(
        player=player,
        status=PlayerTeamExit.Status.PENDING
    ).exists()


@register.simple_tag
def get_pending_exit_request(player):
    """
    Lấy yêu cầu rời đội đang chờ xử lý của cầu thủ
    """
    if not player:
        return None
    
    try:
        return PlayerTeamExit.objects.get(
            player=player,
            status=PlayerTeamExit.Status.PENDING
        )
    except PlayerTeamExit.DoesNotExist:
        return None


@register.simple_tag
def get_team_exit_requests(team, status=None):
    """
    Lấy danh sách yêu cầu rời đội của một đội
    """
    if not team:
        return []
    
    queryset = PlayerTeamExit.objects.filter(current_team=team)
    
    if status:
        queryset = queryset.filter(status=status)
    
    return queryset.order_by('-created_at')


@register.filter
def get_exit_status_color(status):
    """
    Trả về màu sắc cho trạng thái yêu cầu rời đội
    """
    color_map = {
        'PENDING': 'warning',
        'APPROVED': 'success',
        'REJECTED': 'danger',
        'CANCELLED': 'secondary'
    }
    return color_map.get(status, 'secondary')


@register.filter
def get_exit_status_icon(status):
    """
    Trả về icon cho trạng thái yêu cầu rời đội
    """
    icon_map = {
        'PENDING': 'clock',
        'APPROVED': 'check-circle',
        'REJECTED': 'x-circle',
        'CANCELLED': 'dash-circle'
    }
    return icon_map.get(status, 'question-circle')
