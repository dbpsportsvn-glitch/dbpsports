import requests
from bs4 import BeautifulSoup
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
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


def crawl_product_info(url):
    """Crawl thông tin sản phẩm từ URL"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'vi-VN,vi;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        
        response = requests.get(url, headers=headers, timeout=30)
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
            clean_text = re.sub(r'[^\d,]', '', price_text)
            numbers = re.findall(r'[\d,]+', clean_text)
            for number in numbers:
                price_value = int(number.replace(',', ''))
                if 1000 <= price_value <= 100000000:  # Giá hợp lý
                    all_prices.append(price_value)
        
        if all_prices:
            # Loại bỏ giá trùng lặp và sắp xếp
            unique_prices = list(set(all_prices))
            unique_prices.sort(reverse=True)
            
            # Tìm giá khuyến mãi phù hợp (thường là giá thấp nhất hợp lý)
            if len(unique_prices) >= 2:
                price = unique_prices[0]  # Giá gốc (cao nhất)
                
                # Tìm giá khuyến mãi hợp lý (không quá thấp so với giá gốc)
                for sale_candidate in unique_prices[1:]:
                    discount_percent = ((price - sale_candidate) / price) * 100
                    if 5 <= discount_percent <= 50:  # Giảm từ 5% đến 50%
                        sale_price = sale_candidate
                        break
                
                # Nếu không tìm thấy giá khuyến mãi hợp lý, lấy giá thấp nhất
                if sale_price is None:
                    sale_price = unique_prices[-1]
            else:
                # Chỉ có 1 giá -> không khuyến mãi
                price = unique_prices[0]
                sale_price = None
        
        # Tìm mô tả
        description = None
        for selector in description_selectors:
            element = soup.select_one(selector)
            if element:
                description = element.get_text().strip()
                break
        
        # Tìm hình ảnh
        image_url = None
        for selector in image_selectors:
            element = soup.select_one(selector)
            if element:
                src = element.get('src') or element.get('data-src')
                if src:
                    if src.startswith('//'):
                        src = 'https:' + src
                    elif src.startswith('/'):
                        from urllib.parse import urljoin
                        src = urljoin(url, src)
                    image_url = src
                    break
        
        return {
            'name': name,
            'price': price,
            'sale_price': sale_price,
            'description': description,
            'image_url': image_url
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
        
        product = Product.objects.create(
            name=product_data.get('name', f'Import {import_item.id}') or f'Import {import_item.id}',
            slug=slug,
            description=product_data.get('description', '') or 'Sản phẩm được import từ website khác',
            price=price_value,
            sale_price=sale_price_value,
            category=category,
            stock_quantity=1,  # Mặc định
            sku=f'IMPORT-{import_item.id}',  # SKU tự động
            status='published'  # Sử dụng status thay vì is_active
        )
        
        # Download và lưu hình ảnh
        if product_data.get('image_url'):
            try:
                image_response = requests.get(product_data['image_url'], timeout=30)
                if image_response.status_code == 200:
                    image_name = f"import_{product.id}_{slug}.jpg"
                    image_file = ContentFile(image_response.content)
                    product.main_image.save(image_name, image_file, save=True)
            except Exception as e:
                logger.error(f"Error downloading image: {str(e)}")
        
        return product
        
    except Exception as e:
        logger.error(f"Error creating product: {str(e)}")
        return None
