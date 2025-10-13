# Generated manually

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0021_stadiumreview_coachreview'),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='banner_image',
            field=models.ImageField(blank=True, help_text='Ảnh bìa hiển thị ở đầu trang hồ sơ (khuyến nghị: 1920x400px)', null=True, upload_to='profile_banners/', verbose_name='Ảnh bìa hồ sơ'),
        ),
    ]

