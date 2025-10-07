# backend/users/migrations/0010_add_referee_role.py

from django.db import migrations

REFEREE_ROLE_DATA = {
    "id": "REFEREE",
    "name": "Trọng tài",
    "icon": "bi-person-fill-check",
    "description": "Điều hành các trận đấu, đảm bảo tính công bằng và tuân thủ luật lệ. Có thể được BTC mời hoặc tìm việc qua Thị trường Việc làm.",
    "order": 30
}

def create_referee_role(apps, schema_editor):
    Role = apps.get_model('users', 'Role')
    Role.objects.update_or_create(id=REFEREE_ROLE_DATA['id'], defaults=REFEREE_ROLE_DATA)

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