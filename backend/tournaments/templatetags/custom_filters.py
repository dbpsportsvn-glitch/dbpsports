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
        return f"{int(value):,}".replace(",", ".") + " VNĐ"
    except (ValueError, TypeError):
        return value