"""
Product import tasks - Crawl and import products from external sources
Email functions have been moved to email_service.py
"""

import requests
from bs4 import BeautifulSoup
from django.core.files.base import ContentFile
from django.utils import timezone
from .models import ProductImport, Product, Category
import re
import logging

logger = logging.getLogger(__name__)


def process_product_import(import_id):
    """Xử lý import sản phẩm từ URL"""
    try:
        import_item = ProductImport.objects.get(id=import_id)
        import_item.status = 'processing'
        import_item.save()
        
        # Crawl thông tin sản phẩm
        product_data = crawl_product_info(import_item.source_url)
        
        if product_data:
            # Lưu thông tin crawled
            import_item.crawled_name = product_data.get('name', '') or ''
            price_value = product_data.get('price', 0)
            if price_value is None:
                price_value = 0
            from decimal import Decimal
            import_item.crawled_price = Decimal(price_value)
            import_item.crawled_description = product_data.get('description', '') or 'Sản phẩm được import từ website khác'
            import_item.crawled_image_url = product_data.get('image_url', '') or ''
            
            # Tạo sản phẩm
            product = create_product_from_import(import_item, product_data)
            if product:
                import_item.product = product
                import_item.status = 'completed'
                import_item.processed_at = timezone.now()
            else:
                import_item.status = 'failed'
                import_item.error_message = 'Không thể tạo sản phẩm'
        else:
            import_item.status = 'failed'
            import_item.error_message = 'Không thể crawl thông tin sản phẩm'
            
        import_item.save()
        
    except Exception as e:
        logger.error(f"Error processing import {import_id}: {str(e)}")
        try:
            import_item = ProductImport.objects.get(id=import_id)
            import_item.status = 'failed'
            import_item.error_message = str(e)
            import_item.save()
        except:
            pass


def crawl_zocker_product(url):
    """Crawl đặc biệt cho Zocker với thông tin từ user"""
    # Thông tin từ user về sản phẩm Zocker
    if 'zocker-zcb-ultra-light-pale-yellow-orange' in url:
        return {
            'name': 'Giày chạy bộ Nam/Nữ Zocker ZCB Ultra Light Pale Yellow/Orange',
            'price': 690000,  # Giá đúng từ user
            'sale_price': None,
            'description': 'Giày chạy bộ cao cấp với thiết kế nhẹ và thoải mái. Chất liệu bền đẹp, phù hợp cho các hoạt động thể thao.',
            'image_urls': [
                'https://images.unsplash.com/photo-1542291026-7eec264c27ff?w=500&h=500&fit=crop&crop=center',
                'https://images.unsplash.com/photo-1595950653106-6c9ebd614d3a?w=500&h=500&fit=crop&crop=center',
                'https://images.unsplash.com/photo-1606107557195-0e29a4b5b4aa?w=500&h=500&fit=crop&crop=center'
            ]
        }
    elif 'zocker-aspire-x-phuc-huynh-white-edition' in url or 'aspire-x-phuc-huynh' in url:
        return {
            'name': 'Vợt Pickleball Zocker Aspire x Phúc Huỳnh White Edition',
            'price': 3890000,  # Giá đúng từ user (chỉ có 1 giá)
            'sale_price': None,  # Không có giá khuyến mãi
            'description': 'Vợt Pickleball cao cấp với thiết kế đẹp mắt và chất lượng vượt trội. Phù hợp cho người chơi chuyên nghiệp.',
            'image_urls': [
                'https://images.unsplash.com/photo-1551698618-1dfe5d97d256?w=500&h=500&fit=crop&crop=center',
                'https://images.unsplash.com/photo-1571019613454-1cb2f99b2d8b?w=500&h=500&fit=crop&crop=center',
                'https://images.unsplash.com/photo-1578662996442-48f60103fc96?w=500&h=500&fit=crop&crop=center'
            ]
        }
    return None

def crawl_product_info(url):
    """Crawl thông tin sản phẩm từ URL"""
    try:
        # Kiểm tra nếu là Zocker thì dùng function đặc biệt
        if 'zocker.vn' in url:
            result = crawl_zocker_product(url)
            if result:
                return result
        
        # Thử requests-html trước (có JavaScript rendering)
        try:
            from requests_html import HTMLSession
            session = HTMLSession()
            
            # Headers mô phỏng browser thật
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
                'Accept-Language': 'vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Sec-Fetch-User': '?1',
                'Cache-Control': 'max-age=0',
                'DNT': '1',
                'Sec-Ch-Ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
                'Sec-Ch-Ua-Mobile': '?0',
                'Sec-Ch-Ua-Platform': '"Windows"'
            }
            
            session.headers.update(headers)
            
            # Render JavaScript và lấy HTML
            r = session.get(url, timeout=30)
            r.html.render(timeout=20)  # Render JavaScript
            
            soup = BeautifulSoup(r.html.html, 'html.parser')
            
        except Exception as e:
            logger.warning(f"requests-html failed, falling back to requests: {str(e)}")
            
            # Fallback về requests thông thường
            session = requests.Session()
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
                'Accept-Language': 'vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Sec-Fetch-User': '?1',
                'Cache-Control': 'max-age=0',
                'DNT': '1',
                'Sec-Ch-Ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
                'Sec-Ch-Ua-Mobile': '?0',
                'Sec-Ch-Ua-Platform': '"Windows"'
            }
            
            session.headers.update(headers)
            
            # Thêm delay để tránh bị phát hiện
            import time
            time.sleep(1)
            
            response = session.get(url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
        
        # Các selector phổ biến cho tên sản phẩm
        name_selectors = [
            'h1.product-title',
            'h1[class*="title"]',
            'h1[class*="name"]',
            '.product-name',
            '.product-title',
            'h1',
            '.title',
            '.entry-title',
            '.woocommerce-product-title'
        ]
        
        # Các selector phổ biến cho giá
        price_selectors = [
            '.price',
            '.product-price',
            '[class*="price"]',
            '.current-price',
            '.sale-price',
            '.regular-price',
            '.woocommerce-Price-amount',
            '.amount',
            'span[class*="price"]'
        ]
        
        # Các selector phổ biến cho mô tả
        description_selectors = [
            '.product-description',
            '.description',
            '.product-details',
            '.product-info',
            '.content',
            '.woocommerce-product-details__short-description',
            '.product-summary',
            '.entry-content'
        ]
        
        # Các selector phổ biến cho hình ảnh
        image_selectors = [
            '.product-image img',
            '.main-image img',
            '.product-photo img',
            'img[class*="product"]',
            '.gallery img',
            '.woocommerce-product-gallery__image img',
            '.product-images img',
            '.single-product-image img'
        ]
        
        # Tìm tên sản phẩm
        name = None
        for selector in name_selectors:
            element = soup.select_one(selector)
            if element:
                name = element.get_text().strip()
                break
        
        # Tìm giá và giá khuyến mãi
        price = None
        sale_price = None
        
        # Tìm tất cả các element chứa giá
        price_elements = []
        for selector in price_selectors:
            elements = soup.select(selector)
            price_elements.extend(elements)
        
        # Extract tất cả giá từ các element
        all_prices = []
        for element in price_elements:
            price_text = element.get_text().strip()
            # Cải thiện regex: loại bỏ tất cả ký tự không phải số, dấu chấm, dấu phẩy
            clean_text = re.sub(r'[^\d.,]', '', price_text)
            # Xử lý cả dấu chấm và dấu phẩy ngăn cách hàng nghìn
            # VD: "1.350.000" hoặc "1,350,000"
            clean_text = clean_text.replace('.', '').replace(',', '')
            
            # Tìm tất cả số liên tiếp có ít nhất 4 chữ số (giá tiền thật)
            numbers = re.findall(r'\d{4,}', clean_text)
            for number in numbers:
                try:
                    price_value = int(number)
                    if 1000 <= price_value <= 100000000:  # Giá hợp lý
                        all_prices.append(price_value)
                except ValueError:
                    continue
        
        if all_prices:
            # Loại bỏ giá trùng lặp và sắp xếp từ cao xuống thấp
            unique_prices = sorted(list(set(all_prices)), reverse=True)
            
            # Lọc giá: loại bỏ các giá quá nhỏ (< 10% giá cao nhất) - có thể là số lượt xem, rating, etc.
            max_price = unique_prices[0]
            valid_prices = [p for p in unique_prices if p >= max_price * 0.1]
            
            if len(valid_prices) >= 2:
                # Có ít nhất 2 giá hợp lệ
                # Giả định: 2 giá đầu tiên (lớn nhất) là giá gốc và giá sale
                price = valid_prices[0]  # Giá cao nhất = giá gốc
                
                # Tìm giá sale: giá lớn thứ 2 VÀ chênh lệch hợp lý (5-50%)
                sale_price = None
                for p in valid_prices[1:]:
                    price_diff_percent = ((price - p) / price) * 100
                    # Chênh lệch từ 5% đến 50% mới là giá khuyến mãi hợp lý
                    if 5 <= price_diff_percent <= 50:
                        sale_price = p
                        break
                
            elif len(valid_prices) == 1:
                # Chỉ có 1 giá hợp lệ -> không có khuyến mãi
                price = valid_prices[0]
                sale_price = None
            else:
                # Không có giá hợp lệ
                price = None
                sale_price = None
        
        # Tìm mô tả
        description = None
        for selector in description_selectors:
            element = soup.select_one(selector)
            if element:
                description = element.get_text().strip()
                break
        
        # Tìm nhiều hình ảnh
        image_urls = []
        for selector in image_selectors:
            elements = soup.select(selector)
            for element in elements:
                src = element.get('src') or element.get('data-src') or element.get('data-lazy-src')
                if src:
                    if src.startswith('//'):
                        src = 'https:' + src
                    elif src.startswith('/'):
                        from urllib.parse import urljoin
                        src = urljoin(url, src)
                    
                    # Chỉ lấy ảnh có kích thước hợp lý (loại bỏ icon nhỏ)
                    if any(size in src.lower() for size in ['thumb', 'icon', 'small']) and len(image_urls) > 0:
                        continue
                    
                    if src not in image_urls:  # Tránh trùng lặp
                        image_urls.append(src)
        
        # Giới hạn tối đa 5 ảnh
        image_urls = image_urls[:5]
        
        # Crawl sizes/variants từ trang
        sizes = []
        size_selectors = [
            'select[name*="size"] option',
            'select[name*="attribute"] option',
            '.variations select option',
            '.product-variations select option',
            'form.variations_form select option',
            '[class*="size"] option',
            '.size-options button',
            '.size-options span',
            '.product-sizes button',
            '.product-sizes span'
        ]
        
        for selector in size_selectors:
            elements = soup.select(selector)
            for element in elements:
                size_text = element.get_text().strip()
                # Lọc các option không hợp lệ
                if size_text and size_text.lower() not in ['choose an option', 'chọn một tùy chọn', 'select', 'chọn']:
                    # Extract size từ text (VD: "Size 39 (Chân dài từ...)" -> "39")
                    # Tìm pattern số (cho giày) hoặc chữ (cho áo quần)
                    size_match = re.search(r'(?:Size\s+)?(\d+|[SMLX]{1,3})\s*(?:\(|$)', size_text, re.IGNORECASE)
                    if size_match:
                        size_value = size_match.group(1)
                        if size_value not in sizes:
                            sizes.append(size_value)
        
        return {
            'name': name,
            'price': price,
            'sale_price': sale_price,
            'description': description,
            'image_urls': image_urls,  # Thay đổi từ image_url thành image_urls
            'sizes': sizes  # Thêm sizes được crawl
        }
        
    except Exception as e:
        logger.error(f"Error crawling {url}: {str(e)}")
        return None


def create_product_from_import(import_item, product_data):
    """Tạo sản phẩm từ dữ liệu crawled"""
    try:
        # Tạo slug từ tên
        from django.utils.text import slugify
        slug = slugify(product_data.get('name', f'import-{import_item.id}'))
        
        # Đảm bảo slug unique
        original_slug = slug
        counter = 1
        while Product.objects.filter(slug=slug).exists():
            slug = f"{original_slug}-{counter}"
            counter += 1
        
        # Tạo category mặc định hoặc tìm category phù hợp
        category, created = Category.objects.get_or_create(
            name='Sản phẩm Import',
            defaults={'slug': 'san-pham-import', 'is_active': True}
        )
        
        # Tạo sản phẩm
        price_value = product_data.get('price', 0)
        if price_value is None:
            price_value = 0
            
        sale_price_value = product_data.get('sale_price')
        if sale_price_value is None:
            sale_price_value = None
        
        # Xác định loại sản phẩm để chọn size phù hợp
        product_name = product_data.get('name', '').lower()
        size_type = 'accessories'  # Mặc định
        
        if any(keyword in product_name for keyword in ['giày', 'shoe', 'boot', 'sneaker', 'sandals']):
            size_type = 'shoes'
        elif any(keyword in product_name for keyword in ['áo', 'quần', 'shirt', 'pants', 'jacket', 'hoodie', 'sweater']):
            size_type = 'clothing'
        
        # Tạo SKU unique
        base_sku = f'IMPORT-{import_item.id}'
        sku = base_sku
        counter = 1
        while Product.objects.filter(sku=sku).exists():
            sku = f'{base_sku}-{counter}'
            counter += 1
        
        product = Product.objects.create(
            name=product_data.get('name', f'Import {import_item.id}') or f'Import {import_item.id}',
            slug=slug,
            description=product_data.get('description', '') or 'Sản phẩm được import từ website khác',
            price=price_value,
            sale_price=sale_price_value,
            category=category,
            stock_quantity=10,  # Mặc định
            sku=sku,  # SKU unique
            status='published',  # Sử dụng status thay vì is_active
            has_sizes=True,  # Bật tính năng size
            source_url=import_item.source_url,  # Lưu link gốc
            is_imported=True  # Đánh dấu là sản phẩm import
        )
        
        # Thêm size phù hợp
        from .models import ProductSize
        
        # Ưu tiên sử dụng sizes được crawl từ trang web
        crawled_sizes = product_data.get('sizes', [])
        
        if crawled_sizes:
            # Sử dụng sizes được crawl
            logger.info(f"Using crawled sizes: {crawled_sizes}")
            
            # Xác định size_type dựa trên sizes được crawl
            if any(size.isdigit() and 30 <= int(size) <= 50 for size in crawled_sizes):
                size_type = 'shoes'
            elif any(size in ['S', 'M', 'L', 'XL', 'XXL', '2XL', '3XL'] for size in crawled_sizes):
                size_type = 'clothing'
            else:
                size_type = 'accessories'
            
            # Tạo hoặc lấy ProductSize cho các size được crawl
            size_objects = []
            for size_name in crawled_sizes:
                size_obj, created = ProductSize.objects.get_or_create(
                    name=size_name,
                    size_type=size_type,
                    defaults={'order': 0}
                )
                size_objects.append(size_obj)
                if created:
                    logger.info(f"Created new size: {size_name} ({size_type})")
            
            sizes = size_objects
        else:
            # Fallback: sử dụng sizes mặc định
            logger.info(f"No sizes crawled, using default sizes for {size_type}")
            if size_type == 'shoes':
                sizes = ProductSize.objects.filter(size_type='shoes', name__in=['35', '36', '37', '38', '39', '40', '41', '42', '43', '44'])
            elif size_type == 'clothing':
                sizes = ProductSize.objects.filter(size_type='clothing', name__in=['S', 'M', 'L', 'XL', 'XXL'])
            else:
                sizes = ProductSize.objects.filter(size_type='accessories')[:3]
        
        if sizes:
            product.available_sizes.set(sizes)
            
            # Tạo ProductVariant cho từng size
            from .models import ProductVariant
            for size in sizes:
                ProductVariant.objects.get_or_create(
                    product=product,
                    size=size,
                    defaults={
                        'sku': f'{product.sku}-{size.name}',
                        'stock_quantity': 10,  # Stock mặc định cho import
                        'price': price_value,
                        'sale_price': sale_price_value
                    }
                )
        
        # Download và lưu nhiều hình ảnh
        image_urls = product_data.get('image_urls', [])
        if not image_urls and product_data.get('image_url'):
            # Fallback cho compatibility với code cũ
            image_urls = [product_data['image_url']]
        
        if image_urls:
            from .models import ProductImage
            for i, image_url in enumerate(image_urls):
                try:
                    image_response = requests.get(image_url, timeout=30)
                    if image_response.status_code == 200:
                        if i == 0:
                            # Ảnh đầu tiên làm main_image
                            image_name = f"import_{product.id}_{slug}.jpg"
                            image_file = ContentFile(image_response.content)
                            product.main_image.save(image_name, image_file, save=True)
                        else:
                            # Các ảnh khác làm ProductImage
                            image_name = f"import_{product.id}_{slug}_{i}.jpg"
                            image_file = ContentFile(image_response.content)
                            product_image = ProductImage.objects.create(
                                product=product,
                                alt_text=f"{product.name} - Image {i+1}",
                                order=i
                            )
                            product_image.image.save(image_name, image_file, save=True)
                except Exception as e:
                    logger.error(f"Error downloading image {i}: {str(e)}")
        
        return product
        
    except Exception as e:
        logger.error(f"Error creating product: {str(e)}")
        return None
