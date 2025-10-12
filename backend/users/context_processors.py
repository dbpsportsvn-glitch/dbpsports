# backend/users/context_processors.py

def user_roles_context(request):
    """
    Thêm các cờ kiểm tra vai trò vào context cho mọi template
    khi người dùng đã đăng nhập.
    """
    if not request.user.is_authenticated:
        return {}
    
    # Kiểm tra và tạo profile nếu chưa có
    try:
        profile = request.user.profile
    except:
        # Tự động tạo profile nếu user chưa có
        from users.models import Profile
        profile = Profile.objects.create(user=request.user)
    
    # Lấy tất cả các vai trò của người dùng trong một lần truy vấn
    user_role_ids = set(profile.roles.values_list('id', flat=True))
    
    is_player_role = 'PLAYER' in user_role_ids
    is_organizer_role = 'ORGANIZER' in user_role_ids
    
    return {
        'is_player_role': is_player_role,
        'is_organizer_role': is_organizer_role,
    }