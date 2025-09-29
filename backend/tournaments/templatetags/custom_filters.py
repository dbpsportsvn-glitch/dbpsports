# tournaments/templatetags/custom_filters.py
from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)

# === THÊM ĐOẠN CODE NÀY VÀO CUỐI FILE ===
@register.filter(name='vnd_format')
def vnd_format(value):
    """
    Định dạng một số thành chuỗi tiền tệ VNĐ với dấu chấm ngăn cách.
    Ví dụ: 69000 -> "69.000 VNĐ"
    """
    try:
        # Chuyển số thành chuỗi, định dạng với dấu phẩy
        # Sau đó thay thế dấu phẩy bằng dấu chấm
        return f"{int(value):,}".replace(",", ".") + " VNĐ"
    except (ValueError, TypeError):
        return value
# === KẾT THÚC THÊM MỚI ===    