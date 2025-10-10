# backend/users/migrations/0010_add_referee_role.py

from django.db import migrations

# Xóa 'order': 30 khỏi dictionary này
REFEREE_ROLE_DATA = {
    "id": "REFEREE",
    "name": "Trọng tài",
    "icon": "bi-person-fill-check",
    "description": "Điều hành các trận đấu, đảm bảo tính công bằng và tuân thủ luật lệ. Có thể được BTC mời hoặc tìm việc qua Thị trường Việc làm.",
}

def create_referee_role(apps, schema_editor):
    Role = apps.get_model('users', 'Role')
    # Chỉ cập nhật các trường ngoài khóa chính 'id'
    defaults = {k: v for k, v in REFEREE_ROLE_DATA.items() if k != 'id'}
    Role.objects.update_or_create(id=REFEREE_ROLE_DATA['id'], defaults=defaults)

def delete_referee_role(apps, schema_editor):
    Role = apps.get_model('users', 'Role')
    Role.objects.filter(id=REFEREE_ROLE_DATA['id']).delete()

class Migration(migrations.Migration):

    dependencies = [
        ('users', '0009_alter_role_id'), 
    ]

    operations = [
        migrations.RunPython(create_referee_role, delete_referee_role),
    ]