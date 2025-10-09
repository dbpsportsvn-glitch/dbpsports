# tournaments/templatetags/custom_filters.py
from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """
    Lấy một giá trị từ dictionary bằng key trong template.
    """
    return dictionary.get(key)

@register.filter(name='vnd_format')
def vnd_format(value):
    """
    Định dạng một số thành chuỗi tiền tệ VNĐ với dấu chấm ngăn cách.
    Ví dụ: 69000 -> "69.000 VNĐ"
    """
    try:
        # Sử dụng f-string với định dạng dấu phẩy, sau đó thay thế
        return f"{int(value):,}".replace(",", ".") + " VNĐ"
    except (ValueError, TypeError):
        return value

# Thêm bộ lọc mới tại đây
@register.filter(name='filter_by_team')
def filter_by_team(queryset, team_id):
    """
    Lọc một queryset dựa trên team.id.
    """
    if not team_id:
        return []
    return [item for item in queryset if item.team_id == team_id]