# shop/templatetags/shop_filters.py
from django import template

register = template.Library()

@register.filter(name='vnd')
def vnd(value):
    """
    Định dạng số thành chuỗi tiền tệ với dấu chấm ngăn cách (kiểu Việt Nam).
    Ví dụ: 3450000 -> "3.450.000"
    """
    try:
        # Chuyển thành int, format với dấu phẩy, rồi thay bằng dấu chấm
        return f"{int(value):,}".replace(",", ".")
    except (ValueError, TypeError):
        return value

