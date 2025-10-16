from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from organizations.models import Organization
from shop.organization_models import (
    OrganizationCategory, OrganizationProduct, OrganizationShopSettings
)
from shop.models import ProductSize
from decimal import Decimal
import random

class Command(BaseCommand):
    help = 'Tạo dữ liệu mẫu cho Organization Shop'

    def add_arguments(self, parser):
        parser.add_argument(
            '--org-slug',
            type=str,
            help='Slug của organization để tạo dữ liệu mẫu',
        )

    def handle(self, *args, **options):
        org_slug = options.get('org_slug')
        
        if not org_slug:
            # Lấy organization đầu tiên nếu không chỉ định
            try:
                organization = Organization.objects.first()
                if not organization:
                    self.stdout.write(
                        self.style.ERROR('Không tìm thấy organization nào. Hãy tạo organization trước.')
                    )
                    return
            except Organization.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR('Không tìm thấy organization nào.')
                )
                return
        else:
            try:
                organization = Organization.objects.get(slug=org_slug)
            except Organization.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'Không tìm thấy organization với slug: {org_slug}')
                )
                return

        self.stdout.write(f'Tạo dữ liệu mẫu cho organization: {organization.name}')

        # Tạo hoặc cập nhật shop settings
        shop_settings, created = OrganizationShopSettings.objects.get_or_create(
            organization=organization,
            defaults={
                'shop_name': f'Shop {organization.name}',
                'shop_description': f'Cửa hàng chính thức của {organization.name} - Chuyên cung cấp các sản phẩm thể thao chất lượng cao.',
                'is_active': True,
                'shipping_fee': 30000,
                'free_shipping_threshold': 500000,
                'payment_cod': True,
                'payment_bank_transfer': True,
                'bank_info': 'Ngân hàng: Vietcombank\nSố tài khoản: 1234567890\nChủ tài khoản: Ban Tổ Chức',
                'shipping_policy': 'Giao hàng toàn quốc trong 2-5 ngày làm việc. Miễn phí ship cho đơn hàng từ 500,000đ.'
            }
        )

        if created:
            self.stdout.write(f'✓ Đã tạo shop settings cho {organization.name}')
        else:
            self.stdout.write(f'✓ Shop settings đã tồn tại cho {organization.name}')

        # Tạo ProductSize nếu chưa có
        sizes_data = [
            {'name': 'S', 'description': 'Small'},
            {'name': 'M', 'description': 'Medium'},
            {'name': 'L', 'description': 'Large'},
            {'name': 'XL', 'description': 'Extra Large'},
            {'name': 'XXL', 'description': 'Double Extra Large'},
        ]

        for size_data in sizes_data:
            size, created = ProductSize.objects.get_or_create(
                name=size_data['name'],
                defaults={'description': size_data['description']}
            )
            if created:
                self.stdout.write(f'✓ Đã tạo size: {size.name}')

        # Tạo danh mục sản phẩm
        categories_data = [
            {
                'name': 'Áo Thể Thao',
                'slug': 'ao-the-thao',
                'description': 'Các loại áo thể thao chất lượng cao, phù hợp cho mọi hoạt động thể thao.',
            },
            {
                'name': 'Quần Thể Thao',
                'slug': 'quan-the-thao',
                'description': 'Quần thể thao thoải mái, co giãn tốt cho các hoạt động vận động.',
            },
            {
                'name': 'Giày Thể Thao',
                'slug': 'giay-the-thao',
                'description': 'Giày thể thao chuyên nghiệp, hỗ trợ tốt cho chân và giảm chấn thương.',
            },
            {
                'name': 'Phụ Kiện Thể Thao',
                'slug': 'phu-kien-the-thao',
                'description': 'Các phụ kiện thể thao cần thiết như túi, mũ, găng tay...',
            },
            {
                'name': 'Thiết Bị Tập Luyện',
                'slug': 'thiet-bi-tap-luyen',
                'description': 'Thiết bị tập luyện tại nhà và phòng gym chuyên nghiệp.',
            },
        ]

        created_categories = []
        for cat_data in categories_data:
            category, created = OrganizationCategory.objects.get_or_create(
                organization=organization,
                slug=cat_data['slug'],
                defaults={
                    'name': cat_data['name'],
                    'description': cat_data['description'],
                    'is_active': True,
                }
            )
            created_categories.append(category)
            if created:
                self.stdout.write(f'✓ Đã tạo danh mục: {category.name}')

        # Tạo sản phẩm mẫu
        products_data = [
            # Áo Thể Thao
            {
                'name': 'Áo Thể Thao Nam Nike Dri-FIT',
                'slug': 'ao-the-thao-nam-nike-dri-fit',
                'category': 'ao-the-thao',
                'price': 450000,
                'sale_price': 380000,
                'stock': 50,
                'short_description': 'Áo thể thao nam Nike Dri-FIT với công nghệ thấm hút mồ hôi tiên tiến.',
                'description': 'Áo thể thao nam Nike Dri-FIT được thiết kế với công nghệ thấm hút mồ hôi tiên tiến, giúp bạn luôn khô ráo và thoải mái trong quá trình tập luyện. Chất liệu polyester cao cấp, co giãn tốt và bền màu.',
                'is_bestseller': True,
                'status': 'published',
            },
            {
                'name': 'Áo Thể Thao Nữ Adidas Climalite',
                'slug': 'ao-the-thao-nu-adidas-climalite',
                'category': 'ao-the-thao',
                'price': 420000,
                'sale_price': 350000,
                'stock': 35,
                'short_description': 'Áo thể thao nữ Adidas Climalite thiết kế nữ tính, chất liệu thoáng mát.',
                'description': 'Áo thể thao nữ Adidas Climalite với thiết kế nữ tính, chất liệu Climalite thoáng mát và thấm hút mồ hôi hiệu quả. Phù hợp cho các hoạt động thể thao và tập luyện hàng ngày.',
                'is_bestseller': False,
                'status': 'published',
            },
            {
                'name': 'Áo Thể Thao Unisex Puma Dry Cell',
                'slug': 'ao-the-thao-unisex-puma-dry-cell',
                'category': 'ao-the-thao',
                'price': 380000,
                'stock': 25,
                'short_description': 'Áo thể thao unisex Puma Dry Cell phù hợp cho cả nam và nữ.',
                'description': 'Áo thể thao unisex Puma Dry Cell với thiết kế unisex phù hợp cho cả nam và nữ. Công nghệ Dry Cell giúp thấm hút mồ hôi nhanh chóng, giữ cơ thể khô ráo.',
                'is_bestseller': False,
                'status': 'published',
            },

            # Quần Thể Thao
            {
                'name': 'Quần Short Thể Thao Nike Dri-FIT',
                'slug': 'quan-short-the-thao-nike-dri-fit',
                'category': 'quan-the-thao',
                'price': 320000,
                'sale_price': 280000,
                'stock': 40,
                'short_description': 'Quần short thể thao Nike Dri-FIT với túi zip tiện lợi.',
                'description': 'Quần short thể thao Nike Dri-FIT được thiết kế với túi zip tiện lợi để đựng điện thoại và các vật dụng cá nhân. Chất liệu Dri-FIT thấm hút mồ hôi, co giãn tốt.',
                'is_bestseller': True,
                'status': 'published',
            },
            {
                'name': 'Quần Dài Thể Thao Adidas Tiro',
                'slug': 'quan-dai-the-thao-adidas-tiro',
                'category': 'quan-the-thao',
                'price': 550000,
                'stock': 30,
                'short_description': 'Quần dài thể thao Adidas Tiro với thiết kế ôm dáng.',
                'description': 'Quần dài thể thao Adidas Tiro với thiết kế ôm dáng, chất liệu polyester co giãn tốt. Phù hợp cho các hoạt động thể thao và tập luyện trong phòng gym.',
                'is_bestseller': False,
                'status': 'published',
            },

            # Giày Thể Thao
            {
                'name': 'Giày Chạy Bộ Nike Air Zoom Pegasus',
                'slug': 'giay-chay-bo-nike-air-zoom-pegasus',
                'category': 'giay-the-thao',
                'price': 2500000,
                'sale_price': 2200000,
                'stock': 20,
                'short_description': 'Giày chạy bộ Nike Air Zoom Pegasus với công nghệ Zoom Air.',
                'description': 'Giày chạy bộ Nike Air Zoom Pegasus với công nghệ Zoom Air tiên tiến, đệm êm ái và hỗ trợ tốt cho chân. Phù hợp cho các vận động viên chạy bộ chuyên nghiệp.',
                'is_bestseller': True,
                'status': 'published',
            },
            {
                'name': 'Giày Thể Thao Adidas Ultraboost 22',
                'slug': 'giay-the-thao-adidas-ultraboost-22',
                'category': 'giay-the-thao',
                'price': 2800000,
                'stock': 15,
                'short_description': 'Giày thể thao Adidas Ultraboost 22 với Boost technology.',
                'description': 'Giày thể thao Adidas Ultraboost 22 với Boost technology độc quyền, đem lại cảm giác êm ái và năng lượng phản hồi tốt. Thiết kế hiện đại và sang trọng.',
                'is_bestseller': False,
                'status': 'published',
            },

            # Phụ Kiện Thể Thao
            {
                'name': 'Túi Thể Thao Nike Brasilia',
                'slug': 'tui-the-thao-nike-brasilia',
                'category': 'phu-kien-the-thao',
                'price': 450000,
                'sale_price': 380000,
                'stock': 25,
                'short_description': 'Túi thể thao Nike Brasilia với nhiều ngăn tiện lợi.',
                'description': 'Túi thể thao Nike Brasilia với thiết kế nhiều ngăn tiện lợi, chất liệu bền chắc. Phù hợp để đựng quần áo, giày và các phụ kiện thể thao khác.',
                'is_bestseller': False,
                'status': 'published',
            },
            {
                'name': 'Mũ Thể Thao Adidas 3-Stripes',
                'slug': 'mu-the-thao-adidas-3-stripes',
                'category': 'phu-kien-the-thao',
                'price': 180000,
                'stock': 40,
                'short_description': 'Mũ thể thao Adidas 3-Stripes với thiết kế cổ điển.',
                'description': 'Mũ thể thao Adidas 3-Stripes với thiết kế cổ điển, chất liệu cotton thoáng mát. Phù hợp cho các hoạt động thể thao ngoài trời và thời trang hàng ngày.',
                'is_bestseller': False,
                'status': 'published',
            },

            # Thiết Bị Tập Luyện
            {
                'name': 'Tạ Đơn 10kg - Bộ 2 Chiếc',
                'slug': 'ta-don-10kg-bo-2-chiec',
                'category': 'thiet-bi-tap-luyen',
                'price': 850000,
                'sale_price': 750000,
                'stock': 10,
                'short_description': 'Tạ đơn 10kg bộ 2 chiếc chất liệu cao cấp.',
                'description': 'Tạ đơn 10kg bộ 2 chiếc với chất liệu cao cấp, thiết kế ergonomic dễ cầm nắm. Phù hợp cho các bài tập tay, vai và ngực tại nhà hoặc phòng gym.',
                'is_bestseller': False,
                'status': 'published',
            },
            {
                'name': 'Thảm Tập Yoga Premium',
                'slug': 'tham-tap-yoga-premium',
                'category': 'thiet-bi-tap-luyen',
                'price': 320000,
                'stock': 30,
                'short_description': 'Thảm tập yoga premium chống trượt, dày 6mm.',
                'description': 'Thảm tập yoga premium với chất liệu chống trượt, độ dày 6mm đem lại sự thoải mái tối đa. Phù hợp cho các bài tập yoga, pilates và stretching.',
                'is_bestseller': False,
                'status': 'published',
            },

            # Sản phẩm bản nháp
            {
                'name': 'Áo Thể Thao Under Armour HeatGear',
                'slug': 'ao-the-thao-under-armour-heatgear',
                'category': 'ao-the-thao',
                'price': 480000,
                'stock': 0,
                'short_description': 'Áo thể thao Under Armour HeatGear với công nghệ làm mát.',
                'description': 'Áo thể thao Under Armour HeatGear với công nghệ làm mát tiên tiến, giúp điều hòa nhiệt độ cơ thể trong quá trình tập luyện cường độ cao.',
                'is_bestseller': False,
                'status': 'draft',
            },
        ]

        created_products = []
        for prod_data in products_data:
            # Tìm category
            category = next((cat for cat in created_categories if cat.slug == prod_data['category']), None)
            if not category:
                continue

            product, created = OrganizationProduct.objects.get_or_create(
                organization=organization,
                slug=prod_data['slug'],
                defaults={
                    'name': prod_data['name'],
                    'category': category,
                    'price': Decimal(str(prod_data['price'])),
                    'sale_price': Decimal(str(prod_data['sale_price'])) if prod_data.get('sale_price') else None,
                    'stock': prod_data['stock'],
                    'short_description': prod_data['short_description'],
                    'description': prod_data['description'],
                    'is_bestseller': prod_data.get('is_bestseller', False),
                    'status': prod_data['status'],
                }
            )
            created_products.append(product)
            if created:
                self.stdout.write(f'✓ Đã tạo sản phẩm: {product.name}')

        self.stdout.write(
            self.style.SUCCESS(
                f'\n🎉 Hoàn thành tạo dữ liệu mẫu cho {organization.name}!\n'
                f'✓ Shop Settings: {"Tạo mới" if created else "Đã tồn tại"}\n'
                f'✓ Danh mục: {len(created_categories)} danh mục\n'
                f'✓ Sản phẩm: {len(created_products)} sản phẩm\n'
                f'✓ Sizes: {ProductSize.objects.count()} kích thước\n\n'
                f'Bạn có thể truy cập shop tại: /shop/org/{organization.slug}/\n'
                f'Và quản lý shop tại: /shop/org/{organization.slug}/manage/'
            )
        )
