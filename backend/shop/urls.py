from django.urls import path, include
from . import views

app_name = 'shop'

urlpatterns = [
    # Trang chủ shop
    path('', views.shop_home, name='home'),
    
    # Thông tin thanh toán
    path('payment-info/', views.payment_info, name='payment_info'),
    
    # Danh sách sản phẩm
    path('products/', views.product_list, name='product_list'),
    path('products/<slug:slug>/', views.product_detail, name='product_detail'),
    path('test-size/<slug:slug>/', views.test_size, name='test_size'),
    
    # Giỏ hàng
    path('cart/', views.cart_view, name='cart'),
    path('cart/add/', views.add_to_cart, name='add_to_cart'),
    path('cart/api/', views.cart_api, name='cart_api'),
    path('cart/clear/', views.clear_cart, name='clear_cart'),
    path('cart/update/<int:item_id>/', views.update_cart_item, name='update_cart_item'),
    path('cart/remove/<int:item_id>/', views.remove_from_cart, name='remove_from_cart'),
    
    # API sản phẩm
    path('api/product/<int:product_id>/', views.product_info_api, name='product_info_api'),
    
    # Thanh toán và đơn hàng
    path('checkout/', views.checkout, name='checkout'),
    path('order/confirm/', views.order_confirm, name='order_confirm'),
    path('order/place/', views.place_order, name='place_order'),
    path('orders/', views.order_list, name='order_list'),
    path('orders/<int:order_id>/', views.order_detail, name='order_detail'),
    path('orders/<int:order_id>/cancel/', views.cancel_order, name='cancel_order'),
    path('orders/<int:order_id>/reorder/', views.reorder, name='reorder'),
    
    # Import sản phẩm (chỉ admin)
    path('import/', views.import_product_view, name='import_product'),
    path('import/preview/', views.preview_import, name='preview_import'),
    
    # Admin dashboard (chỉ admin)
    path('admin/dashboard/', views.shop_dashboard, name='admin_dashboard'),
    
    # Organization Shop URLs
    path('org/', include('shop.organization_urls', namespace='organization_shop')),
]
