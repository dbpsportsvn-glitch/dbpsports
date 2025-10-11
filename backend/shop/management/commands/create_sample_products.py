from django.core.management.base import BaseCommand
from shop.models import Category, Product, ProductImage
from django.core.files.base import ContentFile
from PIL import Image
import io


class Command(BaseCommand):
    help = 'Tạo dữ liệu mẫu cho shop'

    def handle(self, *args, **options):
        self.stdout.write('Creating sample data...')

        # Create categories
        categories_data = [
            {
                'name': 'Football Shoes',
                'slug': 'football-shoes',
                'description': 'Professional football shoes with high quality'
            },
            {
                'name': 'Football Apparel',
                'slug': 'football-apparel',
                'description': 'Jerseys, shorts, football socks'
            },
            {
                'name': 'Sports Accessories',
                'slug': 'sports-accessories',
                'description': 'Gloves, wraps, training equipment'
            },
            {
                'name': 'Team Uniforms',
                'slug': 'team-uniforms',
                'description': 'Vietnam national team match kits'
            },
            {
                'name': 'Pickleball Shoes',
                'slug': 'pickleball-shoes',
                'description': 'Professional pickleball shoes'
            },
            {
                'name': 'Pickleball Apparel',
                'slug': 'pickleball-apparel',
                'description': 'Pickleball clothing and accessories'
            },
            {
                'name': 'Badminton Shoes',
                'slug': 'badminton-shoes',
                'description': 'Professional badminton shoes'
            },
            {
                'name': 'Running Shoes',
                'slug': 'running-shoes',
                'description': 'Professional running shoes'
            },
            {
                'name': 'Basketball Shoes',
                'slug': 'basketball-shoes',
                'description': 'Professional basketball shoes'
            },
            {
                'name': 'Polo Shirts',
                'slug': 'polo-shirts',
                'description': 'Professional polo shirts'
            },
            {
                'name': 'T-Shirts',
                'slug': 't-shirts',
                'description': 'Professional t-shirts'
            },
            {
                'name': 'Jackets',
                'slug': 'jackets',
                'description': 'Professional jackets'
            },
            {
                'name': 'Pants',
                'slug': 'pants',
                'description': 'Professional pants'
            }
        ]

        categories = {}
        for cat_data in categories_data:
            category, created = Category.objects.get_or_create(
                slug=cat_data['slug'],
                defaults=cat_data
            )
            categories[cat_data['slug']] = category
            if created:
                self.stdout.write(f'Created category: {category.name}')

        # Create sample products
        products_data = [
            {
                'name': 'DBP Pro Football Shoes 2025',
                'slug': 'dbp-pro-football-shoes-2025',
                'description': 'Professional football shoes with latest technology. Premium rubber sole, specially designed toe for better grip and ball control.',
                'short_description': 'Professional football shoes with high tech',
                'price': 1200000,
                'sale_price': 999000,
                'category': categories['football-shoes'],
                'sku': 'DBP-SHOE-001',
                'stock_quantity': 50,
                'weight': 0.8,
                'status': 'published',
                'is_featured': True,
                'is_bestseller': True
            },
            {
                'name': 'Vietnam National Team Jersey 2025',
                'slug': 'vietnam-national-team-jersey-2025',
                'description': 'Official jersey of Vietnam national football team. Premium material, breathable, beautiful design with team logo and sponsor.',
                'short_description': 'Official Vietnam national team jersey',
                'price': 450000,
                'sale_price': 399000,
                'category': categories['team-uniforms'],
                'sku': 'DBP-JERSEY-001',
                'stock_quantity': 100,
                'weight': 0.3,
                'status': 'published',
                'is_featured': True,
                'is_bestseller': False
            },
            {
                'name': 'DBP Sport Football Shorts',
                'slug': 'dbp-sport-football-shorts',
                'description': 'High quality football shorts, good elasticity, breathable. Modern design, suitable for both training and competition.',
                'short_description': 'High quality football shorts',
                'price': 250000,
                'category': categories['football-apparel'],
                'sku': 'DBP-SHORT-001',
                'stock_quantity': 75,
                'weight': 0.2,
                'status': 'published',
                'is_featured': False,
                'is_bestseller': True
            },
            {
                'name': 'DBP Elite Goalkeeper Gloves',
                'slug': 'dbp-elite-goalkeeper-gloves',
                'description': 'Professional goalkeeper gloves with premium grip technology. Good protection, excellent grip, suitable for goalkeepers of all levels.',
                'short_description': 'Professional goalkeeper gloves',
                'price': 350000,
                'sale_price': 299000,
                'category': categories['sports-accessories'],
                'sku': 'DBP-GLOVE-001',
                'stock_quantity': 30,
                'weight': 0.4,
                'status': 'published',
                'is_featured': False,
                'is_bestseller': False
            },
            {
                'name': 'DBP Performance Football Socks',
                'slug': 'dbp-performance-football-socks',
                'description': 'Premium football socks with antibacterial technology, breathable. Ergonomic design, good support for feet throughout the match.',
                'short_description': 'Premium antibacterial football socks',
                'price': 150000,
                'category': categories['football-apparel'],
                'sku': 'DBP-SOCK-001',
                'stock_quantity': 200,
                'weight': 0.1,
                'status': 'published',
                'is_featured': False,
                'is_bestseller': True
            },
            {
                'name': 'DBP Complete Football Kit',
                'slug': 'dbp-complete-football-kit',
                'description': 'Complete football kit including jersey, shorts and socks. Premium material, beautiful design, suitable for football teams.',
                'short_description': 'Complete football kit',
                'price': 850000,
                'sale_price': 699000,
                'category': categories['football-apparel'],
                'sku': 'DBP-KIT-001',
                'stock_quantity': 25,
                'weight': 0.6,
                'status': 'published',
                'is_featured': True,
                'is_bestseller': False
            },
            {
                'name': 'DBP Pickleball Paddle Pro',
                'slug': 'dbp-pickleball-paddle-pro',
                'description': 'Professional pickleball paddle with carbon fiber face. Lightweight design for optimal performance.',
                'short_description': 'Professional pickleball paddle',
                'price': 1200000,
                'sale_price': 999000,
                'category': categories['pickleball-apparel'],
                'sku': 'DBP-PADDLE-001',
                'stock_quantity': 15,
                'weight': 0.3,
                'status': 'published',
                'is_featured': True,
                'is_bestseller': False
            },
            {
                'name': 'DBP Pickleball Shoes Elite',
                'slug': 'dbp-pickleball-shoes-elite',
                'description': 'Professional pickleball shoes with excellent grip and support. Perfect for court sports.',
                'short_description': 'Professional pickleball shoes',
                'price': 800000,
                'sale_price': 699000,
                'category': categories['pickleball-shoes'],
                'sku': 'DBP-PICKLE-SHOE-001',
                'stock_quantity': 20,
                'weight': 0.7,
                'status': 'published',
                'is_featured': False,
                'is_bestseller': True
            },
            {
                'name': 'DBP Basketball Shoes Pro',
                'slug': 'dbp-basketball-shoes-pro',
                'description': 'Professional basketball shoes with superior ankle support and cushioning.',
                'short_description': 'Professional basketball shoes',
                'price': 1500000,
                'sale_price': 1299000,
                'category': categories['basketball-shoes'],
                'sku': 'DBP-BASKET-SHOE-001',
                'stock_quantity': 12,
                'weight': 0.8,
                'status': 'published',
                'is_featured': True,
                'is_bestseller': False
            },
            {
                'name': 'DBP Running Shoes Marathon',
                'slug': 'dbp-running-shoes-marathon',
                'description': 'Professional running shoes designed for long-distance running with excellent cushioning.',
                'short_description': 'Professional running shoes',
                'price': 1000000,
                'sale_price': 899000,
                'category': categories['running-shoes'],
                'sku': 'DBP-RUN-SHOE-001',
                'stock_quantity': 30,
                'weight': 0.6,
                'status': 'published',
                'is_featured': False,
                'is_bestseller': True
            },
            {
                'name': 'DBP Badminton Shoes Speed',
                'slug': 'dbp-badminton-shoes-speed',
                'description': 'Professional badminton shoes with excellent grip and lightweight design.',
                'short_description': 'Professional badminton shoes',
                'price': 700000,
                'sale_price': 599000,
                'category': categories['badminton-shoes'],
                'sku': 'DBP-BAD-SHOE-001',
                'stock_quantity': 25,
                'weight': 0.5,
                'status': 'published',
                'is_featured': False,
                'is_bestseller': True
            }
        ]

        for product_data in products_data:
            product, created = Product.objects.get_or_create(
                slug=product_data['slug'],
                defaults=product_data
            )
            if created:
                self.stdout.write(f'Created product: {product.name}')
                
                # Tạo hình ảnh mẫu (placeholder)
                self.create_placeholder_image(product)

        self.stdout.write(
            self.style.SUCCESS('Sample data created successfully!')
        )

    def create_placeholder_image(self, product):
        """Tạo hình ảnh placeholder cho sản phẩm"""
        # Tạo hình ảnh placeholder đơn giản
        img = Image.new('RGB', (400, 400), color='#f0f0f0')
        
        # Lưu vào buffer
        buffer = io.BytesIO()
        img.save(buffer, format='JPEG')
        buffer.seek(0)
        
        # Tạo file từ buffer
        image_file = ContentFile(buffer.getvalue(), name=f'{product.slug}.jpg')
        
        # Lưu vào model
        product.main_image.save(f'{product.slug}.jpg', image_file, save=True)
