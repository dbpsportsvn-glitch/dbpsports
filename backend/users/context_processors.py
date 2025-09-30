# backend/users/context_processors.py

def user_roles_context(request):
    """
    Thêm cờ kiểm tra vai trò vào context cho mọi template
    khi người dùng đã đăng nhập.
    """
    if not request.user.is_authenticated:
        return {}
    
    # Kiểm tra xem người dùng có vai trò 'PLAYER' trong hồ sơ không.
    is_player_role = request.user.profile.roles.filter(id='PLAYER').exists()
    
    return {
        'is_player_role': is_player_role
    }