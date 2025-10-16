#!/usr/bin/env python
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dbpsports_core.settings')
django.setup()

from organizations.models import Organization
from shop.organization_models import (
    OrganizationCategory, OrganizationProduct, OrganizationShopSettings
)
from shop.models import ProductSize
from decimal import Decimal

def create_sample_data():
    # Get first organization
    organization = Organization.objects.first()
    if not organization:
        print("No organization found")
        return
    
    print(f"Using organization: {organization.slug}")
    
    # Create shop settings
    shop_settings, created = OrganizationShopSettings.objects.get_or_create(
        organization=organization,
        defaults={
            'shop_name': f'Shop {organization.name}',
            'shop_description': 'Official shop',
            'is_active': True,
            'shipping_fee': 30000,
            'free_shipping_threshold': 500000,
            'payment_cod': True,
            'payment_bank_transfer': True,
        }
    )
    print(f"Shop settings created: {created}")
    
    # Create ProductSize
    sizes = ['S', 'M', 'L', 'XL']
    for size_name in sizes:
        size, created = ProductSize.objects.get_or_create(
            name=size_name,
            defaults={'description': size_name}
        )
        if created:
            print(f"Created size: {size_name}")
    
    # Create categories
    categories_data = [
        {'name': 'Sports Shirts', 'slug': 'sports-shirts'},
        {'name': 'Sports Pants', 'slug': 'sports-pants'},
        {'name': 'Sports Shoes', 'slug': 'sports-shoes'},
    ]
    
    created_categories = []
    for cat_data in categories_data:
        category, created = OrganizationCategory.objects.get_or_create(
            organization=organization,
            slug=cat_data['slug'],
            defaults={
                'name': cat_data['name'],
                'description': 'Category description',
                'is_active': True,
            }
        )
        created_categories.append(category)
        if created:
            print(f"Created category: {cat_data['name']}")
    
    # Create products
    products_data = [
        {
            'name': 'Nike Dri-FIT Shirt',
            'slug': 'nike-dri-fit-shirt',
            'category_slug': 'sports-shirts',
            'price': 450000,
            'sale_price': 380000,
            'stock': 50,
            'status': 'published',
        },
        {
            'name': 'Nike Dri-FIT Shorts',
            'slug': 'nike-dri-fit-shorts',
            'category_slug': 'sports-pants',
            'price': 320000,
            'sale_price': 280000,
            'stock': 40,
            'status': 'published',
        },
        {
            'name': 'Nike Air Zoom Shoes',
            'slug': 'nike-air-zoom-shoes',
            'category_slug': 'sports-shoes',
            'price': 2500000,
            'sale_price': 2200000,
            'stock': 20,
            'status': 'published',
        },
    ]
    
    created_products = []
    for prod_data in products_data:
        # Find category
        category = next((cat for cat in created_categories if cat.slug == prod_data['category_slug']), None)
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
                'stock_quantity': prod_data['stock'],
                'sku': f"SKU-{prod_data['slug'].upper()}",
                'short_description': 'Product description',
                'description': 'Detailed product description',
                'is_bestseller': True,
                'status': prod_data['status'],
                'main_image': None,  # Will be set later
            }
        )
        created_products.append(product)
        if created:
            print(f"Created product: {prod_data['name']}")
    
    print(f"SUCCESS!")
    print(f"Organization slug: {organization.slug}")
    print(f"Categories: {len(created_categories)}")
    print(f"Products: {len(created_products)}")
    print(f"Shop URL: /shop/org/{organization.slug}/")
    print(f"Management URL: /shop/org/{organization.slug}/manage/")

if __name__ == '__main__':
    create_sample_data()