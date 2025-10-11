from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q, Count, F, Sum, Avg
from django.core.paginator import Paginator
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.contrib.admin.views.decorators import staff_member_required
from django.utils import timezone
import json
from datetime import datetime, timedelta

from .models import (
    Product, Category, Cart, CartItem, Order, OrderItem, ShopBanner, ProductImport,
    PaymentMethod, BankAccount, EWalletAccount, PaymentStep, ContactInfo, PaymentPolicy,
    CustomerShippingInfo, ContactSettings
)
# NEW: Sử dụng email service mới - đơn giản và hoạt động tốt
from .email_service import send_order_emails

def payment_info(request):
    """Trang thông tin thanh toán"""
    # Lấy các phương thức thanh toán
    payment_methods = PaymentMethod.objects.filter(is_active=True).order_by('order')
    
    # Lấy các bước thanh toán
    payment_steps = PaymentStep.objects.filter(is_active=True).order_by('order')
    
    # Lấy thông tin liên hệ
    contact_infos = ContactInfo.objects.filter(is_active=True).order_by('order')
    
    # Lấy các chính sách thanh toán
    payment_policies = PaymentPolicy.objects.filter(is_active=True).order_by('order')
    
    context = {
        'payment_methods': payment_methods,
        'payment_steps': payment_steps,
        'contact_infos': contact_infos,
        'payment_policies': payment_policies,
    }
    
    return render(request, 'shop/payment_info.html', context)


def shop_home(request):
    """Trang chủ shop"""
    # Lấy tham số từ URL
    category = request.GET.get('category')
    type_filter = request.GET.get('type')
    sport = request.GET.get('sport')
    sale = request.GET.get('sale')
    search = request.GET.get('search')
    suggestions = request.GET.get('suggestions')
    
    # Xử lý AJAX request cho gợi ý tìm kiếm
    if suggestions and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        if search and len(search) >= 2:
            # Lấy gợi ý từ tên sản phẩm và danh mục
            product_suggestions = Product.objects.filter(
                status='published',
                name__icontains=search
            ).values_list('name', flat=True).distinct()[:5]
            
            category_suggestions = Category.objects.filter(
                is_active=True,
                name__icontains=search
            ).values_list('name', flat=True).distinct()[:3]
            
            # Kết hợp và trả về
            all_suggestions = list(product_suggestions) + list(category_suggestions)
            suggestions_list = [{'name': suggestion} for suggestion in all_suggestions[:8]]
            
            return JsonResponse({
                'success': True,
                'suggestions': suggestions_list
            })
        else:
            return JsonResponse({
                'success': False,
                'suggestions': []
            })
    
    # Base queryset
    products_queryset = Product.objects.filter(status='published')
    
    # Filter theo search
    if search:
        products_queryset = products_queryset.filter(
            Q(name__icontains=search) | 
            Q(description__icontains=search) |
            Q(category__name__icontains=search)
        )
    
    # Filter theo category
    if category == 'men':
        products_queryset = products_queryset.filter(
            category__slug__in=['football-shoes', 'basketball-shoes', 'running-shoes', 'badminton-shoes', 'polo-shirts', 't-shirts', 'jackets', 'pants']
        )
    elif category == 'women':
        products_queryset = products_queryset.filter(
            category__slug__in=['football-shoes', 'basketball-shoes', 'running-shoes', 'badminton-shoes', 'polo-shirts', 't-shirts', 'jackets', 'pants']
        )
    
    # Filter theo type
    if type_filter == 'shoes':
        products_queryset = products_queryset.filter(
            category__slug__in=['football-shoes', 'basketball-shoes', 'running-shoes', 'badminton-shoes', 'pickleball-shoes']
        )
    elif type_filter == 'clothing':
        products_queryset = products_queryset.filter(
            category__slug__in=['football-apparel', 'polo-shirts', 't-shirts', 'jackets', 'pants', 'pickleball-apparel']
        )
    
    # Filter theo sport
    if sport == 'football':
        products_queryset = products_queryset.filter(
            category__slug__in=['football-shoes', 'football-apparel', 'team-uniforms']
        )
    elif sport == 'pickleball':
        products_queryset = products_queryset.filter(
            category__slug__in=['pickleball-shoes', 'pickleball-apparel']
        )
    elif sport == 'basketball':
        products_queryset = products_queryset.filter(
            category__slug__in=['basketball-shoes']
        )
    elif sport == 'badminton':
        products_queryset = products_queryset.filter(
            category__slug__in=['badminton-shoes']
        )
    elif sport == 'running':
        products_queryset = products_queryset.filter(
            category__slug__in=['running-shoes']
        )
    
    # Filter theo sale
    if sale == 'true':
        products_queryset = products_queryset.filter(sale_price__isnull=False).exclude(sale_price__gte=F('price'))
    
    # Lấy sản phẩm nổi bật
    featured_products = Product.objects.filter(
        status='published',
        is_featured=True
    ).order_by('-created_at')[:8]
    
    # Lấy sản phẩm bán chạy
    bestseller_products = Product.objects.filter(
        status='published',
        is_bestseller=True
    ).order_by('-created_at')[:8]
    
    # Lấy sản phẩm mới nhất
    new_products = Product.objects.filter(
        status='published'
    ).order_by('-created_at')[:8]
    
    # Lấy sản phẩm bóng đá
    football_products = Product.objects.filter(
        status='published',
        category__slug__in=['football-shoes', 'football-apparel', 'team-uniforms']
    ).order_by('-created_at')[:8]
    
    # Lấy sản phẩm pickleball
    pickleball_products = Product.objects.filter(
        status='published',
        category__slug__in=['pickleball-shoes', 'pickleball-apparel']
    ).order_by('-created_at')[:8]
    
    # Lấy danh mục có sản phẩm
    categories = Category.objects.filter(
        is_active=True,
        products__status='published'
    ).distinct().annotate(
        product_count=Count('products', filter=Q(products__status='published'))
    ).order_by('name')
    
    # Nếu có filter, hiển thị sản phẩm được filter
    filtered_products = products_queryset.order_by('-created_at')[:12] if any([category, type_filter, sport, sale, search]) else None
    
    # Lấy banner
    banners = ShopBanner.objects.filter(is_active=True).order_by('order', '-created_at')
    
    # Lấy cài đặt liên hệ
    try:
        contact_settings = ContactSettings.objects.get(is_active=True)
    except ContactSettings.DoesNotExist:
        contact_settings = None
    
    context = {
        'featured_products': featured_products,
        'bestseller_products': bestseller_products,
        'new_products': new_products,
        'football_products': football_products,
        'pickleball_products': pickleball_products,
        'categories': categories,
        'filtered_products': filtered_products,
        'current_category': category,
        'current_type': type_filter,
        'current_sport': sport,
        'current_search': search,
        'current_sale': sale,
        'banners': banners,
        'contact_settings': contact_settings,
    }
    
    return render(request, 'shop/shop_home.html', context)


def product_list(request):
    """Danh sách sản phẩm"""
    products = Product.objects.filter(status='published')
    
    # Lọc theo danh mục
    category_slug = request.GET.get('category')
    if category_slug:
        category = get_object_or_404(Category, slug=category_slug, is_active=True)
        products = products.filter(category=category)
    else:
        category = None
    
    # Lọc theo từ khóa
    search = request.GET.get('search')
    if search:
        products = products.filter(
            Q(name__icontains=search) |
            Q(description__icontains=search) |
            Q(short_description__icontains=search)
        )
    
    # Sắp xếp
    sort_by = request.GET.get('sort', 'newest')
    if sort_by == 'price_low':
        products = products.order_by('price')
    elif sort_by == 'price_high':
        products = products.order_by('-price')
    elif sort_by == 'name':
        products = products.order_by('name')
    elif sort_by == 'bestseller':
        products = products.filter(is_bestseller=True).order_by('-created_at')
    else:  # newest
        products = products.order_by('-created_at')
    
    # Phân trang
    paginator = Paginator(products, 12)
    page_number = request.GET.get('page')
    products = paginator.get_page(page_number)
    
    # Lấy danh mục
    categories = Category.objects.filter(is_active=True).order_by('name')
    
    context = {
        'products': products,
        'categories': categories,
        'current_category': category,
        'search': search,
        'sort_by': sort_by,
    }
    
    return render(request, 'shop/product_list.html', context)


def product_detail(request, slug):
    """Chi tiết sản phẩm"""
    product = get_object_or_404(Product.objects.prefetch_related('available_sizes'), slug=slug, status='published')
    
    # Sản phẩm liên quan (cùng danh mục)
    related_products = Product.objects.filter(
        category=product.category,
        status='published'
    ).exclude(id=product.id).order_by('-created_at')[:4]
    
    # Sản phẩm bán chạy khác
    other_bestsellers = Product.objects.filter(
        is_bestseller=True,
        status='published'
    ).exclude(id=product.id).order_by('-created_at')[:4]
    
    context = {
        'product': product,
        'related_products': related_products,
        'other_bestsellers': other_bestsellers,
    }
    
    return render(request, 'shop/product_detail.html', context)


def test_size(request, slug):
    """Test size selector"""
    product = get_object_or_404(Product.objects.prefetch_related('available_sizes'), slug=slug, status='published')
    return render(request, 'shop/test_size.html', {'product': product})


@login_required
def cart_view(request):
    """Xem giỏ hàng"""
    cart, created = Cart.objects.get_or_create(user=request.user)
    
    # Tính số tiền cần mua thêm để được miễn phí vận chuyển
    free_shipping_threshold = 500000
    remaining_amount = max(0, free_shipping_threshold - cart.total_price)
    
    context = {
        'cart': cart,
        'remaining_amount': remaining_amount,
        'free_shipping_threshold': free_shipping_threshold,
    }
    
    return render(request, 'shop/cart.html', context)


@login_required
@require_POST
def add_to_cart(request):
    """Thêm sản phẩm vào giỏ hàng"""
    try:
        data = json.loads(request.body)
        product_id = data.get('product_id')
        quantity = int(data.get('quantity', 1))
        size_id = data.get('size_id')
        
        product = get_object_or_404(Product, id=product_id, status='published')
        
        # Kiểm tra stock dựa trên size hoặc product
        if size_id:
            from .models import ProductVariant
            try:
                variant = ProductVariant.objects.get(product=product, size_id=size_id, is_active=True)
                available_stock = variant.stock_quantity
                if quantity > available_stock:
                    return JsonResponse({
                        'success': False,
                        'message': f'Chỉ còn {available_stock} sản phẩm size này trong kho'
                    })
            except ProductVariant.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'message': 'Size này không có sẵn'
                })
        else:
            if quantity > product.stock_quantity:
                return JsonResponse({
                    'success': False,
                    'message': f'Chỉ còn {product.stock_quantity} sản phẩm trong kho'
                })
        
        cart, created = Cart.objects.get_or_create(user=request.user)
        
        # Tạo hoặc cập nhật cart item với size
        size_obj = None
        if size_id:
            from .models import ProductSize
            try:
                size_obj = ProductSize.objects.get(id=size_id)
            except ProductSize.DoesNotExist:
                pass
        
        cart_item, created = CartItem.objects.get_or_create(
            cart=cart,
            product=product,
            size=size_obj,
            defaults={'quantity': quantity}
        )
        
        if not created:
            cart_item.quantity += quantity
            cart_item.save()
        
        # Tạo message với thông tin size
        size_name = ""
        if size_id:
            from .models import ProductSize
            try:
                size = ProductSize.objects.get(id=size_id)
                size_name = f" size {size.name}"
            except ProductSize.DoesNotExist:
                pass
        
        return JsonResponse({
            'success': True,
            'message': f'Đã thêm sản phẩm{size_name} vào giỏ hàng',
            'cart_count': cart.total_items
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': 'Có lỗi xảy ra khi thêm sản phẩm vào giỏ hàng'
        })


@login_required
@require_POST
def update_cart_item(request, item_id):
    """Cập nhật số lượng sản phẩm trong giỏ hàng"""
    try:
        data = json.loads(request.body)
        quantity = int(data.get('quantity', 1))
        
        cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
        
        if quantity <= 0:
            cart_item.delete()
            return JsonResponse({
                'success': True,
                'message': 'Đã xóa sản phẩm khỏi giỏ hàng',
                'cart_count': cart_item.cart.total_items,
                'cart_total': cart_item.cart.total_price
            })
        
        if quantity > cart_item.product.stock_quantity:
            return JsonResponse({
                'success': False,
                'message': f'Chỉ còn {cart_item.product.stock_quantity} sản phẩm trong kho'
            })
        
        cart_item.quantity = quantity
        cart_item.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Đã cập nhật giỏ hàng',
            'cart_count': cart_item.cart.total_items,
            'cart_total': cart_item.cart.total_price,
            'item_total': cart_item.total_price
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': 'Có lỗi xảy ra khi cập nhật giỏ hàng'
        })


@login_required
@require_POST
def remove_from_cart(request, item_id):
    """Xóa sản phẩm khỏi giỏ hàng"""
    try:
        cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
        cart_item.delete()
        
        return JsonResponse({
            'success': True,
            'message': 'Đã xóa sản phẩm khỏi giỏ hàng',
            'cart_count': cart_item.cart.total_items,
            'cart_total': cart_item.cart.total_price
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': 'Có lỗi xảy ra khi xóa sản phẩm khỏi giỏ hàng'
        })


@login_required
def checkout(request):
    """Trang thanh toán"""
    cart = get_object_or_404(Cart, user=request.user)
    
    if cart.items.count() == 0:
        messages.warning(request, 'Giỏ hàng của bạn đang trống')
        return redirect('shop:cart')
    
    # Tính phí vận chuyển (ví dụ: miễn phí cho đơn hàng > 500k)
    shipping_fee = 0 if cart.total_price >= 500000 else 30000
    
    # Tính số tiền cần mua thêm để được miễn phí vận chuyển
    free_shipping_threshold = 500000
    remaining_amount = max(0, free_shipping_threshold - cart.total_price)
    
    # Lấy các phương thức thanh toán
    payment_methods = PaymentMethod.objects.filter(is_active=True).order_by('order')
    
    # Lấy thông tin giao hàng đã lưu (nếu có)
    shipping_info = None
    try:
        shipping_info = CustomerShippingInfo.objects.get(user=request.user)
    except CustomerShippingInfo.DoesNotExist:
        pass
    
    context = {
        'cart': cart,
        'shipping_fee': shipping_fee,
        'total_amount': cart.total_price + shipping_fee,
        'remaining_amount': remaining_amount,
        'free_shipping_threshold': free_shipping_threshold,
        'payment_methods': payment_methods,
        'shipping_info': shipping_info,  # Thông tin đã lưu
    }
    
    return render(request, 'shop/checkout.html', context)


@login_required
def order_confirm(request):
    """Trang xác nhận đơn hàng"""
    cart = get_object_or_404(Cart, user=request.user)
    
    if cart.items.count() == 0:
        messages.warning(request, 'Giỏ hàng của bạn đang trống')
        return redirect('shop:cart')
    
    # Kiểm tra tồn kho sản phẩm
    for cart_item in cart.items.all():
        if cart_item.product.stock_quantity < cart_item.quantity:
            messages.error(request, f'Sản phẩm "{cart_item.product.name}" không đủ hàng trong kho. Số lượng còn lại: {cart_item.product.stock_quantity}')
            return redirect('shop:cart')
        
        if cart_item.product.stock_quantity == 0:
            messages.error(request, f'Sản phẩm "{cart_item.product.name}" đã hết hàng')
            return redirect('shop:cart')
    
    # Tính phí vận chuyển
    shipping_fee = 0 if cart.total_price >= 500000 else 30000
    remaining_amount = max(0, 500000 - cart.total_price)
    total_amount = cart.total_price + shipping_fee
    
    context = {
        'cart': cart,
        'shipping_fee': shipping_fee,
        'total_amount': total_amount,
        'remaining_amount': remaining_amount,
    }
    
    return render(request, 'shop/order_confirm.html', context)


@login_required
@require_POST
def place_order(request):
    """Đặt hàng"""
    try:
        cart = get_object_or_404(Cart, user=request.user)
        
        if cart.items.count() == 0:
            messages.error(request, 'Giỏ hàng của bạn đang trống')
            return redirect('shop:cart')
        
        # Kiểm tra tồn kho sản phẩm
        for cart_item in cart.items.all():
            if cart_item.product.stock_quantity < cart_item.quantity:
                messages.error(request, f'Sản phẩm "{cart_item.product.name}" không đủ hàng trong kho. Số lượng còn lại: {cart_item.product.stock_quantity}')
                return redirect('shop:cart')
            
            if cart_item.product.stock_quantity == 0:
                messages.error(request, f'Sản phẩm "{cart_item.product.name}" đã hết hàng')
                return redirect('shop:cart')
        
        # Lấy thông tin từ form
        customer_name = request.POST.get('customer_name')
        customer_email = request.POST.get('customer_email')
        customer_phone = request.POST.get('customer_phone')
        shipping_address = request.POST.get('shipping_address')
        shipping_city = request.POST.get('shipping_city')
        shipping_district = request.POST.get('shipping_district')
        payment_method = request.POST.get('payment_method', 'cod')
        notes = request.POST.get('notes', '')
        payment_proof = request.FILES.get('payment_proof')
        
        # Validation
        if not customer_name or not customer_name.strip():
            messages.error(request, 'Vui lòng nhập họ và tên')
            return redirect('shop:checkout')
        
        if not customer_phone or not customer_phone.strip():
            messages.error(request, 'Vui lòng nhập số điện thoại')
            return redirect('shop:checkout')
        
        if not customer_email or not customer_email.strip():
            messages.error(request, 'Vui lòng nhập email')
            return redirect('shop:checkout')
        
        if not shipping_address or not shipping_address.strip():
            messages.error(request, 'Vui lòng nhập địa chỉ chi tiết')
            return redirect('shop:checkout')
        
        if not shipping_city or not shipping_city.strip():
            messages.error(request, 'Vui lòng chọn tỉnh/thành phố')
            return redirect('shop:checkout')
        
        if not shipping_district or not shipping_district.strip():
            messages.error(request, 'Vui lòng nhập quận/huyện')
            return redirect('shop:checkout')
        
        # Tính phí vận chuyển
        shipping_fee = 0 if cart.total_price >= 500000 else 30000
        total_amount = cart.total_price + shipping_fee
        
        # Tạo đơn hàng
        order = Order.objects.create(
            user=request.user,
            customer_name=customer_name,
            customer_email=customer_email,
            customer_phone=customer_phone,
            shipping_address=shipping_address,
            shipping_city=shipping_city,
            shipping_district=shipping_district,
            payment_method=payment_method,
            subtotal=cart.total_price,
            shipping_fee=shipping_fee,
            total_amount=total_amount,
            notes=notes,
            payment_proof=payment_proof
        )
        
        # Tạo các sản phẩm trong đơn hàng
        for cart_item in cart.items.all():
            OrderItem.objects.create(
                order=order,
                product=cart_item.product,
                quantity=cart_item.quantity,
                price=cart_item.product.current_price
            )
            
            # Cập nhật số lượng tồn kho
            cart_item.product.stock_quantity -= cart_item.quantity
            cart_item.product.save()
        
        # Lưu thông tin giao hàng để dùng lại lần sau
        CustomerShippingInfo.objects.update_or_create(
            user=request.user,
            defaults={
                'full_name': customer_name,
                'phone': customer_phone,
                'address': shipping_address,
                'city': shipping_city,
                'district': shipping_district,
            }
        )
        
        # Xóa giỏ hàng
        cart.items.all().delete()
        
        # Gửi email thông báo - Sử dụng email service mới
        try:
            send_order_emails(order.id)
        except Exception as email_error:
            # Log lỗi email nhưng không làm fail đơn hàng
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"[ERROR] Error sending emails for order {order.id}: {str(email_error)}")
            print(f"[ERROR] LOI GUI EMAIL: {str(email_error)}")
            import traceback
            traceback.print_exc()
        
        messages.success(request, f'Đặt hàng thành công! Mã đơn hàng: {order.order_number}')
        return redirect('shop:order_detail', order_id=order.id)
        
    except Exception as e:
        messages.error(request, 'Có lỗi xảy ra khi đặt hàng. Vui lòng thử lại.')
        return redirect('shop:checkout')


@login_required
def order_detail(request, order_id):
    """Chi tiết đơn hàng"""
    order = get_object_or_404(Order, id=order_id, user=request.user)
    
    context = {
        'order': order,
    }
    
    return render(request, 'shop/order_detail.html', context)


@login_required
def order_list(request):
    """Danh sách đơn hàng"""
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    
    # Phân trang
    paginator = Paginator(orders, 10)
    page_number = request.GET.get('page')
    orders = paginator.get_page(page_number)
    
    context = {
        'orders': orders,
    }
    
    return render(request, 'shop/order_list.html', context)


@login_required
@require_POST
def cancel_order(request, order_id):
    """Hủy đơn hàng"""
    try:
        order = get_object_or_404(Order, id=order_id, user=request.user)
        
        # Chỉ cho phép hủy đơn hàng đang chờ xử lý
        if order.status != 'pending':
            return JsonResponse({
                'success': False,
                'message': 'Chỉ có thể hủy đơn hàng đang chờ xử lý'
            })
        
        # Cập nhật trạng thái đơn hàng
        order.status = 'cancelled'
        order.save()
        
        # Hoàn lại số lượng tồn kho
        for item in order.items.all():
            item.product.stock_quantity += item.quantity
            item.product.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Đã hủy đơn hàng thành công'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': 'Có lỗi xảy ra khi hủy đơn hàng'
        })


@login_required
@require_POST
def reorder(request, order_id):
    """Đặt lại đơn hàng"""
    try:
        order = get_object_or_404(Order, id=order_id, user=request.user)
        
        # Lấy hoặc tạo giỏ hàng
        cart, created = Cart.objects.get_or_create(user=request.user)
        
        # Thêm các sản phẩm từ đơn hàng vào giỏ hàng
        added_items = 0
        for item in order.items.all():
            # Kiểm tra tồn kho
            if item.product.stock_quantity >= item.quantity:
                cart_item, created = CartItem.objects.get_or_create(
                    cart=cart,
                    product=item.product,
                    defaults={'quantity': item.quantity}
                )
                if not created:
                    cart_item.quantity += item.quantity
                    cart_item.save()
                added_items += 1
        
        if added_items > 0:
            return JsonResponse({
                'success': True,
                'message': f'Đã thêm {added_items} sản phẩm vào giỏ hàng'
            })
        else:
            return JsonResponse({
                'success': False,
                'message': 'Không thể đặt lại vì sản phẩm không còn đủ hàng'
            })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': 'Có lỗi xảy ra khi đặt lại đơn hàng'
        })


@staff_member_required
def import_product_view(request):
    """View để import sản phẩm từ URL"""
    if request.method == 'POST':
        url = request.POST.get('url')
        source_name = request.POST.get('source_name', '')
        
        if url:
            # Tạo ProductImport record
            import_item = ProductImport.objects.create(
                source_url=url,
                source_name=source_name,
                status='pending'
            )
            
            # Xử lý import ngay lập tức
            from .tasks import process_product_import
            try:
                process_product_import(import_item.id)
                import_item.refresh_from_db()
                
                if import_item.status == 'completed':
                    messages.success(request, f'Đã import sản phẩm thành công từ {url}')
                else:
                    messages.error(request, f'Lỗi khi import sản phẩm: {import_item.error_message}')
                    
                return redirect('admin:shop_productimport_changelist')
            except Exception as e:
                messages.error(request, f'Lỗi khi import sản phẩm: {str(e)}')
        else:
            messages.error(request, 'Vui lòng nhập URL sản phẩm')
    
    return render(request, 'shop/import_product.html')


@staff_member_required
def preview_import(request):
    """Preview thông tin sản phẩm trước khi import"""
    url = request.GET.get('url')
    if not url:
        return JsonResponse({'error': 'URL không được để trống'}, status=400)
    
    from .tasks import crawl_product_info
    product_data = crawl_product_info(url)
    
    if product_data:
        return JsonResponse({
            'success': True,
            'data': product_data
        })
    else:
        return JsonResponse({
            'success': False,
            'error': 'Không thể crawl thông tin sản phẩm'
        })


@staff_member_required
def shop_dashboard(request):
    """Dashboard quản lý shop"""
    
    # Thống kê tổng quan
    today = timezone.now().date()
    this_month = today.replace(day=1)
    last_month = (this_month - timedelta(days=1)).replace(day=1)
    
    # Đơn hàng
    total_orders = Order.objects.count()
    pending_orders = Order.objects.filter(status='pending').count()
    processing_orders = Order.objects.filter(status='processing').count()
    completed_orders = Order.objects.filter(status='delivered').count()
    
    # Doanh thu
    total_revenue = Order.objects.filter(
        payment_status='paid'
    ).aggregate(total=Sum('total_amount'))['total'] or 0
    
    monthly_revenue = Order.objects.filter(
        payment_status='paid',
        created_at__gte=this_month
    ).aggregate(total=Sum('total_amount'))['total'] or 0
    
    # Sản phẩm
    total_products = Product.objects.count()
    out_of_stock = Product.objects.filter(stock_quantity=0).count()
    low_stock = Product.objects.filter(stock_quantity__lte=10, stock_quantity__gt=0).count()
    
    # Đơn hàng gần đây
    recent_orders = Order.objects.select_related('user').order_by('-created_at')[:10]
    
    # Sản phẩm bán chạy
    bestseller_products = Product.objects.annotate(
        total_sold=Sum('orderitem__quantity')
    ).order_by('-total_sold')[:5]
    
    # Thống kê theo tháng (7 tháng gần nhất)
    monthly_stats = []
    for i in range(7):
        month_date = today.replace(day=1) - timedelta(days=30*i)
        next_month = (month_date + timedelta(days=32)).replace(day=1)
        
        month_orders = Order.objects.filter(
            created_at__gte=month_date,
            created_at__lt=next_month
        ).count()
        
        month_revenue = Order.objects.filter(
            created_at__gte=month_date,
            created_at__lt=next_month,
            payment_status='paid'
        ).aggregate(total=Sum('total_amount'))['total'] or 0
        
        monthly_stats.append({
            'month': month_date.strftime('%m/%Y'),
            'orders': month_orders,
            'revenue': month_revenue
        })
    
    monthly_stats.reverse()  # Từ cũ đến mới
    
    # Thống kê theo trạng thái thanh toán
    payment_stats = Order.objects.values('payment_status').annotate(
        count=Count('id'),
        total=Sum('total_amount')
    ).order_by('payment_status')
    
    # Top categories
    top_categories = Category.objects.annotate(
        product_count=Count('products'),
        order_count=Sum('products__orderitem__quantity')
    ).order_by('-order_count')[:5]
    
    context = {
        'total_orders': total_orders,
        'pending_orders': pending_orders,
        'processing_orders': processing_orders,
        'completed_orders': completed_orders,
        'total_revenue': total_revenue,
        'monthly_revenue': monthly_revenue,
        'total_products': total_products,
        'out_of_stock': out_of_stock,
        'low_stock': low_stock,
        'recent_orders': recent_orders,
        'bestseller_products': bestseller_products,
        'monthly_stats': monthly_stats,
        'payment_stats': payment_stats,
        'top_categories': top_categories,
    }
    
    return render(request, 'shop/admin/dashboard.html', context)
