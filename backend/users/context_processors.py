# backend/users/context_processors.py

def user_roles_context(request):
    """
    Thêm các cờ kiểm tra vai trò vào context cho mọi template
    khi người dùng đã đăng nhập.
    """
    if not request.user.is_authenticated:
        return {}
    
    # Lấy tất cả các vai trò của người dùng trong một lần truy vấn
    user_role_ids = set(request.user.profile.roles.values_list('id', flat=True))
    
    is_player_role = 'PLAYER' in user_role_ids
    is_organizer_role = 'ORGANIZER' in user_role_ids
    
    return {
        'is_player_role': is_player_role,
        'is_organizer_role': is_organizer_role,
    }