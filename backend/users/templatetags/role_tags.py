"""
Custom template tags để kiểm tra vai trò của user
"""

from django import template

register = template.Library()


@register.filter(name='has_role')
def has_role(user, role_id):
    """
    Kiểm tra user có vai trò cụ thể không.
    
    Usage trong template:
        {% if user|has_role:'COACH' %}
            <!-- Hiển thị nội dung cho HLV -->
        {% endif %}
    
    Args:
        user: User object
        role_id: String ID của role (COACH, STADIUM, PLAYER, etc.)
    
    Returns:
        bool: True nếu user có role đó, False otherwise
    """
    if not user or not user.is_authenticated:
        return False
    
    try:
        # Cache result trong request để tránh query nhiều lần
        cache_key = f'_has_role_{role_id}'
        if hasattr(user, cache_key):
            return getattr(user, cache_key)
        
        # Query và cache kết quả
        result = user.profile.roles.filter(id=role_id).exists()
        setattr(user, cache_key, result)
        return result
    except:
        return False


@register.filter(name='has_any_role')
def has_any_role(user, role_ids):
    """
    Kiểm tra user có ít nhất một trong các vai trò.
    
    Usage:
        {% if user|has_any_role:'COACH,CAPTAIN,PLAYER' %}
            <!-- Hiển thị -->
        {% endif %}
    
    Args:
        user: User object
        role_ids: String các role IDs cách nhau bởi dấu phẩy
    
    Returns:
        bool: True nếu có ít nhất 1 role
    """
    if not user or not user.is_authenticated:
        return False
    
    try:
        role_list = [r.strip() for r in role_ids.split(',')]
        return user.profile.roles.filter(id__in=role_list).exists()
    except:
        return False


@register.simple_tag
def get_user_roles(user):
    """
    Lấy danh sách tất cả vai trò của user.
    
    Usage:
        {% get_user_roles user as user_roles %}
        {% for role in user_roles %}
            {{ role.name }}
        {% endfor %}
    
    Args:
        user: User object
    
    Returns:
        QuerySet: Danh sách roles của user
    """
    if not user or not user.is_authenticated:
        return []
    
    try:
        return user.profile.roles.all()
    except:
        return []

