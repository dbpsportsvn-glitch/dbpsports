# backend/shop/organization_urls.py

from django.urls import path
from . import organization_views

app_name = 'organization_shop'

urlpatterns = [
    # Trang chủ shop của Organization
    path('<slug:org_slug>/', organization_views.organization_shop_home, name='shop_home'),
    
    # Danh sách sản phẩm
    path('<slug:org_slug>/products/', organization_views.organization_product_list, name='product_list'),
    path('<slug:org_slug>/products/<slug:product_slug>/', organization_views.organization_product_detail, name='product_detail'),
    
    # Giỏ hàng
    path('<slug:org_slug>/cart/', organization_views.organization_cart_view, name='cart'),
    path('<slug:org_slug>/cart/add/', organization_views.organization_add_to_cart, name='add_to_cart'),
    path('<slug:org_slug>/cart/update/<int:item_id>/', organization_views.organization_update_cart_item, name='update_cart_item'),
    path('<slug:org_slug>/cart/remove/<int:item_id>/', organization_views.organization_remove_from_cart, name='remove_from_cart'),
    
    # Thanh toán và đơn hàng
    path('<slug:org_slug>/checkout/', organization_views.organization_checkout, name='checkout'),
    path('<slug:org_slug>/order/place/', organization_views.organization_place_order, name='place_order'),
    path('<slug:org_slug>/orders/', organization_views.organization_order_list, name='order_list'),
    path('<slug:org_slug>/orders/<str:order_number>/', organization_views.organization_order_detail, name='order_detail'),
    
    # Dashboard
    path('<slug:org_slug>/dashboard/', organization_views.organization_shop_dashboard, name='dashboard'),
    
    # Management URLs
    path('<slug:org_slug>/manage/', organization_views.manage_shop, name='manage_shop'),
    path('<slug:org_slug>/manage/products/', organization_views.manage_products, name='manage_products'),
    path('<slug:org_slug>/manage/products/edit/<int:product_id>/', organization_views.edit_product, name='edit_product'),
    path('<slug:org_slug>/manage/products/delete/<int:product_id>/', organization_views.delete_product, name='delete_product'),
    path('<slug:org_slug>/manage/orders/', organization_views.manage_orders, name='manage_orders'),
    path('<slug:org_slug>/manage/categories/', organization_views.manage_categories, name='manage_categories'),
    path('<slug:org_slug>/manage/categories/edit/<int:category_id>/', organization_views.edit_category, name='edit_category'),
    path('<slug:org_slug>/manage/categories/delete/<int:category_id>/', organization_views.delete_category, name='delete_category'),
    path('<slug:org_slug>/manage/settings/', organization_views.shop_settings, name='shop_settings'),
    
    # Banner upload
    path('<slug:org_slug>/upload-banner/', organization_views.simple_banner_upload, name='simple_banner_upload'),
]
