# backend/users/migrations/0008_add_manager_role.py

from django.db import migrations

MANAGER_ROLE_DATA = {
    "id": "TOURNAMENT_MANAGER",
    "name": "Quản lý Giải đấu",
    "icon": "bi-person-workspace",
    "description": "Được BTC cấp quyền để quản lý vận hành một giải đấu cụ thể, bao gồm xếp lịch, cập nhật tỉ số, và quản lý các vai trò chuyên môn khác.",
    "order": 70
}

def create_manager_role(apps, schema_editor):
    Role = apps.get_model('users', 'Role')
    Role.objects.update_or_create(id=MANAGER_ROLE_DATA['id'], defaults=MANAGER_ROLE_DATA)

def delete_manager_role(apps, schema_editor):
    Role = apps.get_model('users', 'Role')
    Role.objects.filter(id=MANAGER_ROLE_DATA['id']).delete()

class Migration(migrations.Migration):

    dependencies = [
        ('users', '0007_profile_is_profile_complete'), # File migration cuối cùng trước đó của bạn
    ]

    operations = [
        migrations.RunPython(create_manager_role, delete_manager_role),
    ]