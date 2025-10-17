# Generated manually

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0018_add_shop_banner'),
    ]

    operations = [
        migrations.AddField(
            model_name='organizationorder',
            name='discount_amount',
            field=models.DecimalField(decimal_places=0, default=0, max_digits=10, verbose_name='Số tiền giảm giá'),
        ),
    ]
