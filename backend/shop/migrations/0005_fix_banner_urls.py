from django.db import migrations

def fix_banner_urls(apps, schema_editor):
    """Fix button_url for all existing banners"""
    ShopBanner = apps.get_model('shop', 'ShopBanner')
    
    for banner in ShopBanner.objects.all():
        if "{% url 'shop:product_list' %}" in banner.button_url:
            banner.button_url = "/shop/products/"
            banner.save()

def reverse_fix_banner_urls(apps, schema_editor):
    """Reverse migration - not needed"""
    pass

class Migration(migrations.Migration):
    dependencies = [
        ('shop', '0004_alter_shopbanner_button_url'),
    ]

    operations = [
        migrations.RunPython(fix_banner_urls, reverse_fix_banner_urls),
    ]
