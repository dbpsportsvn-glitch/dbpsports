# backend/users/migrations/0014_add_sponsor_data.py

from django.db import migrations

SPONSOR_ROLE_DATA = {
    "id": "SPONSOR",
    "name": "Nhà tài trợ",
    "icon": "bi-gem",
    "description": "Đồng hành và hỗ trợ các giải đấu, giúp phát triển cộng đồng và quảng bá thương hiệu.",
    "order": 100
}

def create_sponsor_role(apps, schema_editor):
    Role = apps.get_model('users', 'Role')
    # Dùng update_or_create để đảm bảo an toàn nếu migration được chạy lại
    Role.objects.update_or_create(id=SPONSOR_ROLE_DATA['id'], defaults=SPONSOR_ROLE_DATA)

def delete_sponsor_role(apps, schema_editor):
    Role = apps.get_model('users', 'Role')
    Role.objects.filter(id=SPONSOR_ROLE_DATA['id']).delete()

class Migration(migrations.Migration):

    dependencies = [
        ('users', '0013_alter_role_id'), # Phụ thuộc vào file 0013 mà Django vừa tạo
    ]

    operations = [
        migrations.RunPython(create_sponsor_role, delete_sponsor_role),
    ]