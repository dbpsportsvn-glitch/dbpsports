# backend/users/migrations/0005_seed_roles.py

from django.db import migrations

# === BẮT ĐẦU THÊM MỚI TẠI ĐÂY ===
ROLES_DATA = [
    {
        "id": "ORGANIZER", "name": "Ban Tổ chức", "icon": "bi-shield-check",
        "description": "Đăng cai và quản lý các giải đấu của riêng bạn, tiếp cận các công cụ quản lý chuyên nghiệp.",
        "order": 10
    },
    {
        "id": "PLAYER", "name": "Cầu thủ", "icon": "bi-person-badge",
        "description": "Tham gia các đội bóng, được ghi nhận thành tích và nhận phiếu bầu để tăng giá trị chuyển nhượng.",
        "order": 20
    },
    {
        "id": "COMMENTATOR", "name": "Bình Luận Viên", "icon": "bi-mic-fill",
        "description": "Được các BTC mời tham gia bình luận, truy cập phòng điều khiển livestream.",
        "order": 40
    },
    {
        "id": "MEDIA", "name": "Đơn vị Truyền thông", "icon": "bi-camera-reels-fill",
        "description": "Đặc quyền truy cập các tính năng Media, đăng tải hình ảnh, video và quản lý thư viện cho giải đấu.",
        "order": 50
    },
    {
        "id": "PHOTOGRAPHER", "name": "Nhiếp Ảnh Gia", "icon": "bi-camera-fill",
        "description": "Được các BTC mời tác nghiệp, dễ dàng đăng tải và quản lý album ảnh cho từng trận đấu.",
        "order": 60
    },
    {
        "id": "COLLABORATOR", "name": "Cộng Tác Viên", "icon": "bi-person-plus-fill",
        "description": "Hỗ trợ BTC trong các công tác như y tế, an ninh, hậu cần... và được ghi nhận trong thành phần BTC giải.",
        "order": 80
    },
]

def create_roles(apps, schema_editor):
    Role = apps.get_model('users', 'Role')
    for role_data in ROLES_DATA:
        Role.objects.update_or_create(id=role_data['id'], defaults=role_data)

def delete_roles(apps, schema_editor):
    Role = apps.get_model('users', 'Role')
    role_ids = [r['id'] for r in ROLES_DATA]
    Role.objects.filter(id__in=role_ids).delete()
# === KẾT THÚC THÊM MỚI ===

class Migration(migrations.Migration):

    dependencies = [
        ('users', '0004_role_profile_has_selected_roles_profile_roles'), # Tên file này có thể khác
    ]

    operations = [
        # === THÊM DÒNG NÀY VÀO ===
        migrations.RunPython(create_roles, delete_roles),
    ]