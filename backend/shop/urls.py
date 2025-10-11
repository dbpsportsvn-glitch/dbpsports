from django.urls import path
from . import views

app_name = 'shop'

urlpatterns = [
    # Trang chủ shop
    path('', views.shop_home, name='home'),
    
    # Danh sách sản phẩm
    path('products/', views.product_list, name='product_list'),
    path('products/<slug:slug>/', views.product_detail, name='product_detail'),
    
    # Giỏ hàng
    path('cart/', views.cart_view, name='cart'),
    path('cart/add/', views.add_to_cart, name='add_to_cart'),
    path('cart/update/<int:item_id>/', views.update_cart_item, name='update_cart_item'),
    path('cart/remove/<int:item_id>/', views.remove_from_cart, name='remove_from_cart'),
    
    # Thanh toán và đơn hàng
    path('checkout/', views.checkout, name='checkout'),
    path('order/place/', views.place_order, name='place_order'),
    path('orders/', views.order_list, name='order_list'),
    path('orders/<int:order_id>/', views.order_detail, name='order_detail'),
    
    # Import sản phẩm (chỉ admin)
    path('import/', views.import_product_view, name='import_product'),
    path('import/preview/', views.preview_import, name='preview_import'),
]
