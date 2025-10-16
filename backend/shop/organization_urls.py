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
    path('<slug:org_slug>/orders/<int:order_id>/', organization_views.organization_order_detail, name='order_detail'),
]
