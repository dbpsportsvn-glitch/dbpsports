# backend/shop/organization_views.py

def resize_banner_image(image_field, target_width=1200, target_height=300):
    """
    Resize ảnh banner về kích thước chuẩn và nén để tối ưu
    Target size: 1200x300px (tỷ lệ 4:1)
    """
    if not image_field or not hasattr(image_field, 'read'):
        return image_field
    
    try:
        # Reset file pointer to beginning
        image_field.seek(0)
        
        # Mở ảnh với PIL
        img = Image.open(image_field)
        
        # Chuyển đổi sang RGB nếu cần (cho PNG có alpha channel)
        if img.mode in ('RGBA', 'P'):
            img = img.convert('RGB')
        
        # Resize ảnh về kích thước chuẩn với crop center để giữ tỷ lệ
        original_width, original_height = img.size
        
        # Thuật toán COVER - đảm bảo ảnh fill đầy banner hoàn toàn
        scale_width = target_width / original_width
        scale_height = target_height / original_height
        
        # Sử dụng scale lớn hơn để đảm bảo cover đầy đủ
        scale = max(scale_width, scale_height)
        
        # Tính kích thước sau resize
        new_width = int(original_width * scale)
        new_height = int(original_height * scale)
        
        # Resize ảnh
        img_resized = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        # Crop về đúng kích thước target từ center
        # Đảm bảo crop từ center để có phần ảnh đẹp nhất
        left = (new_width - target_width) // 2
        top = (new_height - target_height) // 2
        right = left + target_width
        bottom = top + target_height
        
        img_cropped = img_resized.crop((left, top, right, bottom))
        
        # Nén ảnh với quality 85%
        buffer = BytesIO()
        img_cropped.save(buffer, format='JPEG', quality=85, optimize=True)
        
        # Kiểm tra kích thước sau khi nén
        compressed_size = buffer.tell()
        target_size = 2 * 1024 * 1024  # 2MB
        
        # Nếu vẫn quá lớn, giảm quality xuống 75%
        if compressed_size > target_size:
            buffer = BytesIO()
            img_cropped.save(buffer, format='JPEG', quality=75, optimize=True)
            compressed_size = buffer.tell()
        
        # Nếu vẫn quá lớn, giảm quality xuống 65%
        if compressed_size > target_size:
            buffer = BytesIO()
            img_cropped.save(buffer, format='JPEG', quality=65, optimize=True)
        
        # Tạo file mới
        buffer.seek(0)
        file_name = f"banner_resized_{target_width}x{target_height}.jpg"
        file_content = ContentFile(buffer.getvalue(), name=file_name)
        
        return file_content
        
    except Exception as e:
        print(f"Error resizing banner image: {e}")
        # Fallback: return original image
        image_field.seek(0)
        return image_field


from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction, models
from django.core.paginator import Paginator
from django.db.models import Q, Sum, Count
from django.urls import reverse
from django.utils import timezone
from decimal import Decimal
from datetime import datetime, timedelta
import json
from PIL import Image
from io import BytesIO
from django.core.files.base import ContentFile

from organizations.models import Organization
from .organization_models import (
    OrganizationCategory, OrganizationProduct, OrganizationCart, 
    OrganizationCartItem, OrganizationOrder, OrganizationOrderItem,
    OrganizationShopSettings
)


def organization_shop_home(request, org_slug):
    """Trang chủ shop của Organization"""
    organization = get_object_or_404(Organization, slug=org_slug)
    
    # Kiểm tra shop có được kích hoạt không
    try:
        shop_settings = organization.shop_settings
        if not shop_settings.is_active:
            messages.warning(request, "Shop của ban tổ chức này hiện đang tạm ngưng hoạt động.")
            return redirect('tournament_detail', pk=organization.tournaments.first().pk)
    except OrganizationShopSettings.DoesNotExist:
        messages.warning(request, "Ban tổ chức này chưa thiết lập shop.")
        return redirect('tournament_detail', pk=organization.tournaments.first().pk)
    
    # Lấy sản phẩm nổi bật
    featured_products = OrganizationProduct.objects.filter(
        organization=organization,
        status='published',
        is_featured=True
    )[:6]
    
    # Lấy sản phẩm bán chạy
    bestseller_products = OrganizationProduct.objects.filter(
        organization=organization,
        status='published',
        is_bestseller=True
    )[:6]
    
    # Lấy danh mục
    categories = OrganizationCategory.objects.filter(
        organization=organization,
        is_active=True
    )[:8]
    
    # Thống kê shop
    total_products = OrganizationProduct.objects.filter(
        organization=organization,
        status='published'
    ).count()
    
    total_orders = OrganizationOrder.objects.filter(
        organization=organization
    ).count()
    
    total_customers = OrganizationOrder.objects.filter(
        organization=organization
    ).values('user').distinct().count()
    
    # Kiểm tra user có phải BTC member không
    is_btc_member = False
    if request.user.is_authenticated:
        is_btc_member = organization.members.filter(id=request.user.id).exists()
    
    context = {
        'organization': organization,
        'shop_settings': shop_settings,
        'featured_products': featured_products,
        'bestseller_products': bestseller_products,
        'categories': categories,
        'total_products': total_products,
        'total_orders': total_orders,
        'total_customers': total_customers,
        'is_btc_member': is_btc_member,
    }
    
    return render(request, 'shop/organization/shop_home.html', context)


def organization_product_list(request, org_slug):
    """Danh sách sản phẩm của Organization"""
    organization = get_object_or_404(Organization, slug=org_slug)
    
    # Kiểm tra shop có được kích hoạt không
    try:
        shop_settings = organization.shop_settings
        if not shop_settings.is_active:
            messages.warning(request, "Shop của ban tổ chức này hiện đang tạm ngưng hoạt động.")
            return redirect('tournament_detail', pk=organization.tournaments.first().pk)
    except OrganizationShopSettings.DoesNotExist:
        messages.warning(request, "Ban tổ chức này chưa thiết lập shop.")
        return redirect('tournament_detail', pk=organization.tournaments.first().pk)
    
    # Lấy tham số lọc
    category_slug = request.GET.get('category')
    search = request.GET.get('search')
    sort = request.GET.get('sort', 'newest')
    
    # Query sản phẩm
    products = OrganizationProduct.objects.filter(
        organization=organization,
        status='published'
    )
    
    # Lọc theo danh mục
    current_category = None
    if category_slug:
        current_category = get_object_or_404(OrganizationCategory, slug=category_slug, organization=organization)
        products = products.filter(category=current_category)
    
    # Tìm kiếm
    if search:
        products = products.filter(
            Q(name__icontains=search) |
            Q(description__icontains=search) |
            Q(short_description__icontains=search)
        )
    
    # Sắp xếp
    if sort == 'price_low':
        products = products.order_by('price')
    elif sort == 'price_high':
        products = products.order_by('-price')
    elif sort == 'name':
        products = products.order_by('name')
    elif sort == 'bestseller':
        products = products.filter(is_bestseller=True).order_by('-created_at')
    else:  # newest
        products = products.order_by('-created_at')
    
    # Phân trang
    paginator = Paginator(products, 12)
    page_number = request.GET.get('page')
    products = paginator.get_page(page_number)
    
    # Lấy danh mục
    categories = OrganizationCategory.objects.filter(
        organization=organization,
        is_active=True
    )
    
    context = {
        'organization': organization,
        'shop_settings': shop_settings,
        'products': products,
        'categories': categories,
        'current_category': current_category,
        'search': search,
        'sort': sort,
    }
    
    return render(request, 'shop/organization/product_list.html', context)


def organization_product_detail(request, org_slug, product_slug):
    """Chi tiết sản phẩm của Organization"""
    organization = get_object_or_404(Organization, slug=org_slug)
    product = get_object_or_404(
        OrganizationProduct, 
        slug=product_slug, 
        organization=organization,
        status='published'
    )
    
    # Kiểm tra shop có được kích hoạt không
    try:
        shop_settings = organization.shop_settings
        if not shop_settings.is_active:
            messages.warning(request, "Shop của ban tổ chức này hiện đang tạm ngưng hoạt động.")
            return redirect('tournament_detail', pk=organization.tournaments.first().pk)
    except OrganizationShopSettings.DoesNotExist:
        messages.warning(request, "Ban tổ chức này chưa thiết lập shop.")
        return redirect('tournament_detail', pk=organization.tournaments.first().pk)
    
    # Lấy sản phẩm liên quan
    related_products = OrganizationProduct.objects.filter(
        organization=organization,
        category=product.category,
        status='published'
    ).exclude(id=product.id)[:4]
    
    # Lấy variants nếu có
    variants = product.variants.all() if product.has_sizes else []
    
    context = {
        'organization': organization,
        'shop_settings': shop_settings,
        'product': product,
        'related_products': related_products,
        'variants': variants,
    }
    
    return render(request, 'shop/organization/product_detail.html', context)


@login_required
def organization_cart_view(request, org_slug):
    """Xem giỏ hàng của Organization"""
    organization = get_object_or_404(Organization, slug=org_slug)
    
    # Kiểm tra shop có được kích hoạt không
    try:
        shop_settings = organization.shop_settings
        if not shop_settings.is_active:
            messages.warning(request, "Shop của ban tổ chức này hiện đang tạm ngưng hoạt động.")
            return redirect('tournament_detail', pk=organization.tournaments.first().pk)
    except OrganizationShopSettings.DoesNotExist:
        messages.warning(request, "Ban tổ chức này chưa thiết lập shop.")
        return redirect('tournament_detail', pk=organization.tournaments.first().pk)
    
    # Lấy hoặc tạo cart
    cart, created = OrganizationCart.objects.get_or_create(
        user=request.user,
        organization=organization
    )
    
    cart_items = cart.items.all()
    
    context = {
        'organization': organization,
        'shop_settings': shop_settings,
        'cart': cart,
        'cart_items': cart_items,
        'cart_count': cart.total_items,
    }
    
    return render(request, 'shop/organization/cart.html', context)


@login_required
@require_POST
def organization_add_to_cart(request, org_slug):
    """Thêm sản phẩm vào giỏ hàng Organization"""
    organization = get_object_or_404(Organization, slug=org_slug)
    
    try:
        data = json.loads(request.body)
        product_id = data.get('product_id')
        quantity = int(data.get('quantity', 1))
        size_id = data.get('size_id')
        buy_now = data.get('buy_now', False)  # Flag for buy now functionality
        
        product = get_object_or_404(OrganizationProduct, id=product_id, organization=organization)
        
        # Kiểm tra tồn kho
        if product.has_sizes and size_id:
            variant = product.variants.filter(size_id=size_id).first()
            if not variant or variant.stock_quantity < quantity:
                return JsonResponse({'success': False, 'error': 'Không đủ hàng trong kho'})
        else:
            if product.stock_quantity < quantity:
                return JsonResponse({'success': False, 'error': 'Không đủ hàng trong kho'})
        
        # Lấy hoặc tạo cart
        cart, created = OrganizationCart.objects.get_or_create(
            user=request.user,
            organization=organization
        )
        
        # Nếu là "Mua Ngay", xóa tất cả items trong cart trước
        if buy_now:
            cart.items.all().delete()
        
        # Lấy hoặc tạo cart item
        size = None
        if size_id:
            size = get_object_or_404('shop.ProductSize', id=size_id)
        
        cart_item, created = OrganizationCartItem.objects.get_or_create(
            cart=cart,
            product=product,
            size=size,
            defaults={'quantity': quantity}
        )
        
        if not created:
            cart_item.quantity += quantity
            cart_item.save()
        
        return JsonResponse({
            'success': True, 
            'message': f'Đã thêm {product.name} vào giỏ hàng',
            'cart_total': cart.total_items,
            'buy_now': buy_now
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
@require_POST
def organization_update_cart_item(request, org_slug, item_id):
    """Cập nhật số lượng sản phẩm trong giỏ hàng"""
    organization = get_object_or_404(Organization, slug=org_slug)
    
    try:
        data = json.loads(request.body)
        quantity = int(data.get('quantity', 1))
        
        cart_item = get_object_or_404(
            OrganizationCartItem, 
            id=item_id,
            cart__user=request.user,
            cart__organization=organization
        )
        
        if quantity <= 0:
            cart_item.delete()
            return JsonResponse({'success': True, 'message': 'Đã xóa sản phẩm khỏi giỏ hàng'})
        
        # Kiểm tra tồn kho
        if cart_item.product.has_sizes and cart_item.size:
            variant = cart_item.product.variants.filter(size=cart_item.size).first()
            if variant and variant.stock_quantity < quantity:
                return JsonResponse({'success': False, 'error': 'Không đủ hàng trong kho'})
        else:
            if cart_item.product.stock_quantity < quantity:
                return JsonResponse({'success': False, 'error': 'Không đủ hàng trong kho'})
        
        cart_item.quantity = quantity
        cart_item.save()
        
        return JsonResponse({
            'success': True, 
            'message': 'Đã cập nhật số lượng',
            'item_total': cart_item.total_price,
            'cart_total': cart_item.cart.total_items,
            'cart_price': cart_item.cart.total_price
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
@require_POST
def organization_remove_from_cart(request, org_slug, item_id):
    """Xóa sản phẩm khỏi giỏ hàng"""
    organization = get_object_or_404(Organization, slug=org_slug)
    
    try:
        cart_item = get_object_or_404(
            OrganizationCartItem, 
            id=item_id,
            cart__user=request.user,
            cart__organization=organization
        )
        
        cart_item.delete()
        
        return JsonResponse({
            'success': True, 
            'message': 'Đã xóa sản phẩm khỏi giỏ hàng',
            'cart_total': cart_item.cart.total_items
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
def organization_checkout(request, org_slug):
    """Trang thanh toán Organization Shop"""
    organization = get_object_or_404(Organization, slug=org_slug)
    
    # Kiểm tra shop có được kích hoạt không
    try:
        shop_settings = organization.shop_settings
        if not shop_settings.is_active:
            messages.warning(request, "Shop của ban tổ chức này hiện đang tạm ngưng hoạt động.")
            return redirect('tournament_detail', pk=organization.tournaments.first().pk)
    except OrganizationShopSettings.DoesNotExist:
        messages.warning(request, "Ban tổ chức này chưa thiết lập shop.")
        return redirect('tournament_detail', pk=organization.tournaments.first().pk)
    
    # Lấy cart
    try:
        cart = OrganizationCart.objects.get(user=request.user, organization=organization)
        cart_items = cart.items.all()
        
        if not cart_items:
            messages.warning(request, "Giỏ hàng trống")
            return redirect('shop:organization_shop:cart', org_slug=org_slug)
            
    except OrganizationCart.DoesNotExist:
        messages.warning(request, "Giỏ hàng trống")
        return redirect('shop:organization_shop:cart', org_slug=org_slug)
    
    # Tính tổng tiền
    subtotal = cart.total_price
    shipping_fee = shop_settings.shipping_fee
    
    # Kiểm tra miễn phí ship
    if shop_settings.free_shipping_threshold and subtotal >= shop_settings.free_shipping_threshold:
        shipping_fee = 0
    
    total_amount = subtotal + shipping_fee
    
    context = {
        'organization': organization,
        'shop_settings': shop_settings,
        'cart': cart,
        'cart_items': cart_items,
        'subtotal': subtotal,
        'shipping_fee': shipping_fee,
        'total_amount': total_amount,
    }
    
    return render(request, 'shop/organization/checkout.html', context)


@login_required
@require_POST
def organization_place_order(request, org_slug):
    """Đặt hàng từ Organization Shop"""
    organization = get_object_or_404(Organization, slug=org_slug)
    
    try:
        shop_settings = organization.shop_settings
        if not shop_settings.is_active:
            return JsonResponse({'success': False, 'error': 'Shop đang tạm ngưng hoạt động'})
    except OrganizationShopSettings.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Shop chưa được thiết lập'})
    
    try:
        # Lấy cart
        cart = OrganizationCart.objects.get(user=request.user, organization=organization)
        cart_items = cart.items.all()
        
        if not cart_items:
            return JsonResponse({'success': False, 'error': 'Giỏ hàng trống'})
        
        # Validation required fields
        customer_name = request.POST.get('customer_name', '').strip()
        customer_email = request.POST.get('customer_email', '').strip()
        customer_phone = request.POST.get('customer_phone', '').strip()
        shipping_address = request.POST.get('shipping_address', '').strip()
        shipping_city = request.POST.get('shipping_city', '').strip()
        shipping_district = request.POST.get('shipping_district', '').strip()
        
        # Debug logging
        print(f"DEBUG - Received data:")
        print(f"  customer_name: '{customer_name}' (len: {len(customer_name)})")
        print(f"  customer_email: '{customer_email}'")
        print(f"  customer_phone: '{customer_phone}'")
        print(f"  shipping_address: '{shipping_address}'")
        print(f"  shipping_city: '{shipping_city}'")
        print(f"  shipping_district: '{shipping_district}'")
        print(f"  POST data: {dict(request.POST)}")
        
        if not customer_name:
            return JsonResponse({'success': False, 'error': 'Vui lòng nhập họ và tên'})
        if not customer_email:
            return JsonResponse({'success': False, 'error': 'Vui lòng nhập email'})
        if not customer_phone:
            return JsonResponse({'success': False, 'error': 'Vui lòng nhập số điện thoại'})
        if not shipping_address:
            return JsonResponse({'success': False, 'error': 'Vui lòng nhập địa chỉ'})
        if not shipping_city:
            return JsonResponse({'success': False, 'error': 'Vui lòng nhập thành phố'})
        if not shipping_district:
            return JsonResponse({'success': False, 'error': 'Vui lòng nhập quận/huyện'})
        
        # Kiểm tra tồn kho
        for cart_item in cart_items:
            if cart_item.product.has_sizes and cart_item.size:
                variant = cart_item.product.variants.filter(size=cart_item.size).first()
                if not variant or variant.stock_quantity < cart_item.quantity:
                    return JsonResponse({'success': False, 'error': f'Sản phẩm "{cart_item.product.name}" không đủ hàng trong kho'})
            else:
                if cart_item.product.stock_quantity < cart_item.quantity:
                    return JsonResponse({'success': False, 'error': f'Sản phẩm "{cart_item.product.name}" không đủ hàng trong kho'})
        
        # Tính tổng tiền
        subtotal = cart.total_price
        shipping_fee = shop_settings.shipping_fee
        
        if shop_settings.free_shipping_threshold and subtotal >= shop_settings.free_shipping_threshold:
            shipping_fee = 0
        
        total_amount = subtotal + shipping_fee
        
        # Tạo đơn hàng
        with transaction.atomic():
            order = OrganizationOrder.objects.create(
                organization=organization,
                user=request.user,
                customer_name=customer_name,
                customer_email=customer_email,
                customer_phone=customer_phone,
                shipping_address=shipping_address,
                shipping_city=shipping_city,
                shipping_district=shipping_district,
                subtotal=subtotal,
                shipping_fee=shipping_fee,
                total_amount=total_amount,
                payment_method=request.POST.get('payment_method', 'cod'),
                notes=request.POST.get('notes', ''),
            )
            
            # Xử lý payment proof upload
            if 'payment_proof' in request.FILES:
                order.payment_proof = request.FILES['payment_proof']
                order.save()
            
            # Tạo order items
            for cart_item in cart_items:
                OrganizationOrderItem.objects.create(
                    order=order,
                    product=cart_item.product,
                    quantity=cart_item.quantity,
                    price=cart_item.product.current_price
                )
                
                # Cập nhật tồn kho
                if cart_item.product.has_sizes and cart_item.size:
                    variant = cart_item.product.variants.filter(size=cart_item.size).first()
                    if variant:
                        variant.stock_quantity -= cart_item.quantity
                        variant.save()
                else:
                    cart_item.product.stock_quantity -= cart_item.quantity
                    cart_item.product.save()
            
        # Xóa cart
        cart.delete()
        
        # Gửi email thông báo - Sử dụng organization email service
        try:
            from .organization_email_service import send_org_order_emails
            send_org_order_emails(order.id)
        except Exception as email_error:
            # Log lỗi email nhưng không làm fail đơn hàng
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"[ERROR] Error sending organization emails for order {order.id}: {str(email_error)}")
            print(f"[ERROR] LOI GUI EMAIL ORGANIZATION: {str(email_error)}")
            import traceback
            traceback.print_exc()
        
        return JsonResponse({
            'success': True,
            'message': 'Đặt hàng thành công',
            'order_number': order.order_number,
            'redirect_url': f'/shop/org/{organization.slug}/orders/{order.order_number}/?success=1'
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
def organization_order_detail(request, org_slug, order_number):
    """Chi tiết đơn hàng Organization"""
    organization = get_object_or_404(Organization, slug=org_slug)
    
    # Debug logging
    print(f"DEBUG - Order Detail Request:")
    print(f"  org_slug: {org_slug}")
    print(f"  order_number: {order_number}")
    print(f"  user: {request.user}")
    print(f"  organization: {organization}")
    
    # First try to find the order
    try:
        order = OrganizationOrder.objects.get(
            order_number=order_number,
            organization=organization
        )
        print(f"  Found order: {order}")
        print(f"  Order user: {order.user}")
        print(f"  Order status: {order.status}")
        
        # Check if user has permission to view this order
        # BTC members can view all orders, customers can only view their own orders
        is_btc_member = organization.members.filter(id=request.user.id).exists()
        
        if not is_btc_member and order.user != request.user:
            print(f"  Permission denied: Order belongs to {order.user}, requested by {request.user}")
            return render(request, 'shop/organization/order_detail.html', {
                'organization': organization,
                'error': 'Bạn không có quyền xem đơn hàng này'
            })
            
    except OrganizationOrder.DoesNotExist:
        print(f"  Order not found: {order_number}")
        # Debug: List all orders for this organization
        all_orders = OrganizationOrder.objects.filter(organization=organization)
        print(f"  All orders for {organization.name}:")
        for o in all_orders:
            print(f"    - {o.order_number} (user: {o.user})")
        return render(request, 'shop/organization/order_detail.html', {
            'organization': organization,
            'error': 'Đơn hàng không tồn tại'
        })
    
    # Get shop settings for template
    try:
        shop_settings = organization.shop_settings
    except OrganizationShopSettings.DoesNotExist:
        shop_settings = None
    
    context = {
        'organization': organization,
        'shop_settings': shop_settings,
        'order': order,
    }
    
    return render(request, 'shop/organization/order_detail.html', context)


@login_required
def organization_order_list(request, org_slug):
    """Danh sách đơn hàng Organization"""
    organization = get_object_or_404(Organization, slug=org_slug)
    
    # Lấy tham số lọc
    status_filter = request.GET.get('status', '')
    
    # Query đơn hàng
    orders = OrganizationOrder.objects.filter(
        organization=organization,
        user=request.user
    )
    
    # Lọc theo trạng thái nếu có
    if status_filter:
        if status_filter == 'active':
            # Chỉ hiển thị đơn hàng chưa hủy
            orders = orders.exclude(status='cancelled')
        elif status_filter == 'cancelled':
            # Chỉ hiển thị đơn hàng đã hủy
            orders = orders.filter(status='cancelled')
        else:
            # Lọc theo trạng thái cụ thể
            orders = orders.filter(status=status_filter)
    
    # Sắp xếp: đơn hàng active trước, cancelled sau
    orders = orders.order_by(
        'status',  # cancelled sẽ ở cuối
        '-created_at'
    )
    
    # Thống kê
    total_orders = OrganizationOrder.objects.filter(
        organization=organization,
        user=request.user
    ).count()
    
    active_orders = OrganizationOrder.objects.filter(
        organization=organization,
        user=request.user
    ).exclude(status='cancelled').count()
    
    cancelled_orders = OrganizationOrder.objects.filter(
        organization=organization,
        user=request.user,
        status='cancelled'
    ).count()
    
    context = {
        'organization': organization,
        'orders': orders,
        'status_filter': status_filter,
        'total_orders': total_orders,
        'active_orders': active_orders,
        'cancelled_orders': cancelled_orders,
    }
    
    return render(request, 'shop/organization/order_list.html', context)


# ==================== SHOP MANAGEMENT VIEWS ====================

@login_required
def manage_shop(request, org_slug):
    """Trang quản lý shop của BTC"""
    organization = get_object_or_404(Organization, slug=org_slug)
    
    # Kiểm tra quyền truy cập
    if not organization.members.filter(id=request.user.id).exists():
        messages.error(request, 'Bạn không có quyền truy cập shop này')
        return redirect('organizations:dashboard')
    
    # Lấy hoặc tạo shop settings
    shop_settings, created = OrganizationShopSettings.objects.get_or_create(
        organization=organization,
        defaults={
            'shop_name': organization.name,
            'is_active': True,
            'shipping_fee': 30000,
            'free_shipping_threshold': 500000,
        }
    )
    
    # Thống kê shop
    total_products = OrganizationProduct.objects.filter(organization=organization).count()
    total_orders = OrganizationOrder.objects.filter(organization=organization).count()
    total_revenue = OrganizationOrder.objects.filter(
        organization=organization, 
        status='DELIVERED'
    ).aggregate(total=models.Sum('total_amount'))['total'] or 0
    
    # Đơn hàng gần đây
    recent_orders = OrganizationOrder.objects.filter(
        organization=organization
    ).order_by('-created_at')[:5]
    
    context = {
        'organization': organization,
        'shop_settings': shop_settings,
        'total_products': total_products,
        'total_orders': total_orders,
        'total_revenue': total_revenue,
        'recent_orders': recent_orders,
        'is_btc_member': True,  # User đã được kiểm tra quyền ở trên
    }
    
    return render(request, 'shop/organization/manage_shop.html', context)


@login_required
def manage_products(request, org_slug):
    """Quản lý sản phẩm"""
    organization = get_object_or_404(Organization, slug=org_slug)
    
    # Kiểm tra quyền truy cập
    if not organization.members.filter(id=request.user.id).exists():
        messages.error(request, 'Bạn không có quyền truy cập shop này')
        return redirect('organizations:dashboard')
    
    # Xử lý POST request (thêm sản phẩm)
    if request.method == 'POST':
        name = request.POST.get('name')
        category_id = request.POST.get('category')
        price = request.POST.get('price')
        sale_price = request.POST.get('sale_price', '')
        stock_quantity = request.POST.get('stock_quantity', 0)
        short_description = request.POST.get('short_description', '')
        description = request.POST.get('description', '')
        status = request.POST.get('status', 'draft')
        is_bestseller = request.POST.get('is_bestseller') == 'on'
        
        if not name or not category_id or not price:
            messages.error(request, 'Tên sản phẩm, danh mục và giá là bắt buộc')
        else:
            try:
                category = OrganizationCategory.objects.get(id=category_id, organization=organization)
                
                # Tạo slug từ tên sản phẩm
                from django.utils.text import slugify
                base_slug = slugify(name)
                slug = base_slug
                counter = 1
                while OrganizationProduct.objects.filter(organization=organization, slug=slug).exists():
                    slug = f"{base_slug}-{counter}"
                    counter += 1
                
                # Tạo SKU
                sku = f"SKU-{slug.upper()}"
                
                # Xử lý file upload
                main_image = request.FILES.get('image')
                
                product = OrganizationProduct.objects.create(
                    organization=organization,
                    name=name,
                    slug=slug,
                    category=category,
                    price=Decimal(price),
                    sale_price=Decimal(sale_price) if sale_price else None,
                    stock_quantity=int(stock_quantity),
                    sku=sku,
                    short_description=short_description,
                    description=description,
                    status=status,
                    is_bestseller=is_bestseller,
                    main_image=main_image,
                )
                messages.success(request, f'Đã tạo sản phẩm "{name}" thành công')
                return redirect('shop:organization_shop:manage_products', org_slug=org_slug)
            except OrganizationCategory.DoesNotExist:
                messages.error(request, 'Danh mục không tồn tại')
            except Exception as e:
                messages.error(request, f'Lỗi khi tạo sản phẩm: {str(e)}')
    
    # Lọc và tìm kiếm
    search = request.GET.get('search', '')
    category_id = request.GET.get('category', '')
    status = request.GET.get('status', '')
    
    products = OrganizationProduct.objects.filter(organization=organization)
    
    if search:
        products = products.filter(
            Q(name__icontains=search) | Q(description__icontains=search)
        )
    
    if category_id:
        products = products.filter(category_id=category_id)
    
    if status:
        if status == 'published':
            products = products.filter(status='published')
        elif status == 'draft':
            products = products.filter(status='draft')
        elif status == 'archived':
            products = products.filter(status='archived')
    
    # Phân trang
    paginator = Paginator(products.order_by('-created_at'), 20)
    page_number = request.GET.get('page')
    products = paginator.get_page(page_number)
    
    # Danh mục cho filter
    categories = OrganizationCategory.objects.filter(organization=organization)
    
    # Thống kê
    total_products = OrganizationProduct.objects.filter(organization=organization).count()
    published_products = OrganizationProduct.objects.filter(organization=organization, status='published').count()
    draft_products = OrganizationProduct.objects.filter(organization=organization, status='draft').count()
    total_categories = categories.count()
    
    context = {
        'organization': organization,
        'products': products,
        'categories': categories,
        'search': search,
        'category_id': category_id,
        'status': status,
        'total_products': total_products,
        'published_products': published_products,
        'draft_products': draft_products,
        'total_categories': total_categories,
        'is_btc_member': True,  # User đã được kiểm tra quyền ở trên
    }
    
    return render(request, 'shop/organization/manage_products.html', context)


@login_required
def manage_orders(request, org_slug):
    """Quản lý đơn hàng"""
    organization = get_object_or_404(Organization, slug=org_slug)
    
    # Kiểm tra quyền truy cập
    if not organization.members.filter(id=request.user.id).exists():
        messages.error(request, 'Bạn không có quyền truy cập shop này')
        return redirect('organizations:dashboard')
    
    # Xử lý POST request (cập nhật trạng thái đơn hàng)
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            action = data.get('action')
            order_id = data.get('order_id')
            
            order = get_object_or_404(OrganizationOrder, id=order_id, organization=organization)
            
            if action == 'update_status':
                new_status = data.get('status')
                if new_status in ['processing', 'shipped', 'delivered', 'cancelled']:
                    order.status = new_status
                    order.save()
                    return JsonResponse({'success': True, 'message': f'Đã cập nhật trạng thái đơn hàng thành {new_status}'})
                    
            elif action == 'confirm_payment':
                if order.payment_status == 'pending':
                    order.payment_status = 'paid'
                    order.save()
                    return JsonResponse({'success': True, 'message': 'Đã xác nhận thanh toán'})
                    
            elif action == 'cancel_order':
                reason = data.get('reason', '')
                order.status = 'cancelled'
                # Cập nhật trạng thái thanh toán khi hủy đơn hàng
                if order.payment_status == 'pending':
                    order.payment_status = 'failed'
                order.notes = f"{order.notes}\n[Hủy đơn hàng] {reason}" if order.notes else f"[Hủy đơn hàng] {reason}"
                order.save()
                return JsonResponse({'success': True, 'message': 'Đã hủy đơn hàng'})
                
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    # Lọc đơn hàng
    status = request.GET.get('status', '')
    search = request.GET.get('search', '')
    
    orders = OrganizationOrder.objects.filter(organization=organization)
    
    if status:
        orders = orders.filter(status=status)
    
    if search:
        orders = orders.filter(
            Q(order_number__icontains=search) |
            Q(customer_name__icontains=search) |
            Q(customer_phone__icontains=search)
        )
    
    # Phân trang
    paginator = Paginator(orders.order_by('-created_at'), 20)
    page_number = request.GET.get('page')
    orders = paginator.get_page(page_number)
    
    # Thống kê
    total_orders = OrganizationOrder.objects.filter(organization=organization).count()
    pending_orders = OrganizationOrder.objects.filter(organization=organization, status='pending').count()
    delivered_orders = OrganizationOrder.objects.filter(organization=organization, status='delivered').count()
    total_revenue = OrganizationOrder.objects.filter(
        organization=organization, 
        payment_status='paid'
    ).aggregate(total=models.Sum('total_amount'))['total'] or 0
    
    context = {
        'organization': organization,
        'orders': orders,
        'status': status,
        'search': search,
        'total_orders': total_orders,
        'pending_orders': pending_orders,
        'delivered_orders': delivered_orders,
        'total_revenue': total_revenue,
        'is_btc_member': True,  # User đã được kiểm tra quyền ở trên
    }
    
    return render(request, 'shop/organization/manage_orders.html', context)


@login_required
def manage_categories(request, org_slug):
    """Quản lý danh mục"""
    organization = get_object_or_404(Organization, slug=org_slug)
    
    # Kiểm tra quyền truy cập
    if not organization.members.filter(id=request.user.id).exists():
        messages.error(request, 'Bạn không có quyền truy cập shop này')
        return redirect('organizations:dashboard')
    
    # Xử lý POST request (thêm danh mục)
    if request.method == 'POST':
        name = request.POST.get('name')
        slug = request.POST.get('slug')
        description = request.POST.get('description', '')
        is_active = request.POST.get('is_active') == 'on'
        
        if not name or not slug:
            messages.error(request, 'Tên danh mục và slug là bắt buộc')
        else:
            try:
                # Kiểm tra slug unique trong organization
                if OrganizationCategory.objects.filter(organization=organization, slug=slug).exists():
                    messages.error(request, 'Slug đã tồn tại trong organization này')
                else:
                    # Xử lý file upload
                    image = request.FILES.get('image')
                    
                    category = OrganizationCategory.objects.create(
                        organization=organization,
                        name=name,
                        slug=slug,
                        description=description,
                        is_active=is_active,
                        image=image
                    )
                    messages.success(request, f'Đã tạo danh mục "{name}" thành công')
                    return redirect('shop:organization_shop:manage_categories', org_slug=org_slug)
            except Exception as e:
                messages.error(request, f'Lỗi khi tạo danh mục: {str(e)}')
    
    categories = OrganizationCategory.objects.filter(organization=organization).order_by('name')
    
    # Thống kê
    total_categories = categories.count()
    active_categories = categories.filter(is_active=True).count()
    total_products = OrganizationProduct.objects.filter(organization=organization).count()
    
    context = {
        'organization': organization,
        'categories': categories,
        'total_categories': total_categories,
        'active_categories': active_categories,
        'total_products': total_products,
        'is_btc_member': True,  # User đã được kiểm tra quyền ở trên
    }
    
    return render(request, 'shop/organization/manage_categories.html', context)


@csrf_exempt
@login_required
def shop_settings(request, org_slug):
    """Cài đặt shop - CSRF exempt tạm thời để fix lỗi"""
    organization = get_object_or_404(Organization, slug=org_slug)
    
    # Kiểm tra quyền truy cập
    if not organization.members.filter(id=request.user.id).exists():
        messages.error(request, 'Bạn không có quyền truy cập shop này')
        return redirect('organizations:dashboard')
    
    # Lấy hoặc tạo shop settings
    shop_settings, created = OrganizationShopSettings.objects.get_or_create(
        organization=organization,
        defaults={
            'shop_name': organization.name,
            'is_active': True,
            'shipping_fee': 30000,
            'free_shipping_threshold': 500000,
        }
    )
    
    if request.method == 'POST':
        try:
            # Debug CSRF
            print(f"DEBUG CSRF - Token from form: {request.POST.get('csrfmiddlewaretoken', 'NOT_FOUND')}")
            print(f"DEBUG CSRF - Session CSRF: {request.session.get('csrf_token', 'NOT_FOUND')}")
            
            # Cập nhật thông tin cơ bản
            shop_settings.shop_name = request.POST.get('shop_name', organization.name)
            shop_settings.shop_description = request.POST.get('shop_description', '')
            shop_settings.contact_phone = request.POST.get('contact_phone', '')
            shop_settings.contact_email = request.POST.get('contact_email', '')
            shop_settings.contact_address = request.POST.get('contact_address', '')
            
            # Cập nhật thông tin ngân hàng
            shop_settings.bank_name = request.POST.get('bank_name', '')
            shop_settings.bank_account_number = request.POST.get('bank_account_number', '')
            shop_settings.bank_account_name = request.POST.get('bank_account_name', '')
            
            # Cập nhật cài đặt giao hàng
            shop_settings.shipping_fee = Decimal(request.POST.get('shipping_fee', 0))
            free_shipping = request.POST.get('free_shipping_threshold', '')
            shop_settings.free_shipping_threshold = Decimal(free_shipping) if free_shipping else None
            
            # Cập nhật trạng thái
            shop_settings.is_active = request.POST.get('is_active') == 'on'
            
            # Upload files nếu có
            if 'shop_logo' in request.FILES:
                shop_settings.shop_logo = request.FILES['shop_logo']
            
            if 'payment_qr_code' in request.FILES:
                shop_settings.payment_qr_code = request.FILES['payment_qr_code']
            
            shop_settings.save()
            messages.success(request, 'Cài đặt shop đã được cập nhật thành công')
            return redirect('shop:organization_shop:shop_settings', org_slug=organization.slug)
            
        except Exception as e:
            print(f"DEBUG - Error in shop_settings POST: {e}")
            messages.error(request, f'Có lỗi xảy ra: {str(e)}')
    
    context = {
        'organization': organization,
        'shop_settings': shop_settings,
        'is_btc_member': True,  # User đã được kiểm tra quyền ở trên
    }
    
    return render(request, 'shop/organization/shop_settings.html', context)


@login_required
def simple_banner_upload(request, org_slug):
    """Upload banner cho Organization Shop với image compression"""
    organization = get_object_or_404(Organization, slug=org_slug)
    
    # Kiểm tra quyền truy cập
    if not organization.members.filter(id=request.user.id).exists():
        messages.error(request, 'Bạn không có quyền truy cập shop này')
        return redirect('organizations:dashboard')
    
    if request.method == 'POST':
        try:
            # Lấy hoặc tạo shop settings
            shop_settings, created = OrganizationShopSettings.objects.get_or_create(
                organization=organization,
                defaults={
                    'shop_name': organization.name,
                    'is_active': True,
                    'shipping_fee': 30000,
                    'free_shipping_threshold': 500000,
                }
            )
            
            # Upload banner
            if 'shop_banner' in request.FILES:
                file = request.FILES['shop_banner']
                
                # Validate file type
                allowed_types = ['image/jpeg', 'image/jpg', 'image/png', 'image/webp']
                if file.content_type not in allowed_types:
                    messages.error(request, "Chỉ chấp nhận file ảnh (JPG, PNG, WebP).")
                    return redirect('shop:organization_shop:simple_banner_upload', org_slug=org_slug)
                
                # Kiểm tra kích thước file (max 5MB)
                if file.size > 5 * 1024 * 1024:
                    messages.error(request, 'File quá lớn. Kích thước tối đa 5MB')
                    return redirect('shop:organization_shop:simple_banner_upload', org_slug=org_slug)
                
                # Tự động resize và nén ảnh banner
                try:
                    resized_image = resize_banner_image(file)
                    shop_settings.shop_banner = resized_image
                    shop_settings.save()
                    messages.success(request, f'Banner "{file.name}" đã được upload, resize và tự động nén thành công!')
                except Exception as resize_error:
                    # Fallback: lưu ảnh gốc nếu không resize được
                    shop_settings.shop_banner = file
                    shop_settings.save()
                    messages.success(request, f'Banner "{file.name}" đã được upload thành công!')
            else:
                messages.error(request, 'Không có file banner được upload')
                
        except Exception as e:
            messages.error(request, f'Lỗi upload banner: {str(e)}')
    
    context = {
        'organization': organization,
    }
    return render(request, 'shop/organization/simple_banner_upload.html', context)


# ==================== EDIT & DELETE VIEWS ====================

@login_required
def edit_product(request, org_slug, product_id):
    """Chỉnh sửa sản phẩm"""
    organization = get_object_or_404(Organization, slug=org_slug)
    
    # Kiểm tra quyền truy cập
    if not organization.members.filter(id=request.user.id).exists():
        messages.error(request, 'Bạn không có quyền truy cập shop này')
        return redirect('organizations:dashboard')
    
    product = get_object_or_404(OrganizationProduct, id=product_id, organization=organization)
    
    if request.method == 'POST':
        name = request.POST.get('name')
        category_id = request.POST.get('category')
        price = request.POST.get('price')
        sale_price = request.POST.get('sale_price', '')
        stock_quantity = request.POST.get('stock_quantity', 0)
        short_description = request.POST.get('short_description', '')
        description = request.POST.get('description', '')
        status = request.POST.get('status', 'draft')
        is_bestseller = request.POST.get('is_bestseller') == 'on'
        
        if not name or not category_id or not price:
            messages.error(request, 'Tên sản phẩm, danh mục và giá là bắt buộc')
        else:
            try:
                category = OrganizationCategory.objects.get(id=category_id, organization=organization)
                
                # Cập nhật thông tin sản phẩm
                product.name = name
                product.category = category
                product.price = Decimal(price)
                product.sale_price = Decimal(sale_price) if sale_price else None
                product.stock_quantity = int(stock_quantity)
                product.short_description = short_description
                product.description = description
                product.status = status
                product.is_bestseller = is_bestseller
                
                # Xử lý file upload mới (nếu có)
                new_image = request.FILES.get('image')
                if new_image:
                    product.main_image = new_image
                
                product.save()
                messages.success(request, f'Đã cập nhật sản phẩm "{name}" thành công')
                return redirect('shop:organization_shop:manage_products', org_slug=org_slug)
            except OrganizationCategory.DoesNotExist:
                messages.error(request, 'Danh mục không tồn tại')
            except Exception as e:
                messages.error(request, f'Lỗi khi cập nhật sản phẩm: {str(e)}')
    
    # Lấy danh mục cho dropdown
    categories = OrganizationCategory.objects.filter(organization=organization)
    
    context = {
        'organization': organization,
        'product': product,
        'categories': categories,
    }
    
    return render(request, 'shop/organization/edit_product.html', context)


@login_required
def delete_product(request, org_slug, product_id):
    """Xóa sản phẩm"""
    organization = get_object_or_404(Organization, slug=org_slug)
    
    # Kiểm tra quyền truy cập
    if not organization.members.filter(id=request.user.id).exists():
        messages.error(request, 'Bạn không có quyền truy cập shop này')
        return redirect('organizations:dashboard')
    
    product = get_object_or_404(OrganizationProduct, id=product_id, organization=organization)
    
    if request.method == 'POST':
        product_name = product.name
        product.delete()
        messages.success(request, f'Đã xóa sản phẩm "{product_name}" thành công')
        return redirect('shop:organization_shop:manage_products', org_slug=org_slug)
    
    context = {
        'organization': organization,
        'product': product,
    }
    
    return render(request, 'shop/organization/delete_product.html', context)


@login_required
def edit_category(request, org_slug, category_id):
    """Chỉnh sửa danh mục"""
    organization = get_object_or_404(Organization, slug=org_slug)
    
    # Kiểm tra quyền truy cập
    if not organization.members.filter(id=request.user.id).exists():
        messages.error(request, 'Bạn không có quyền truy cập shop này')
        return redirect('organizations:dashboard')
    
    category = get_object_or_404(OrganizationCategory, id=category_id, organization=organization)
    
    if request.method == 'POST':
        name = request.POST.get('name')
        slug = request.POST.get('slug')
        description = request.POST.get('description', '')
        is_active = request.POST.get('is_active') == 'on'
        
        if not name or not slug:
            messages.error(request, 'Tên danh mục và slug là bắt buộc')
        else:
            try:
                # Kiểm tra slug unique (trừ danh mục hiện tại)
                if OrganizationCategory.objects.filter(organization=organization, slug=slug).exclude(id=category_id).exists():
                    messages.error(request, 'Slug đã tồn tại trong organization này')
                else:
                    # Cập nhật thông tin danh mục
                    category.name = name
                    category.slug = slug
                    category.description = description
                    category.is_active = is_active
                    
                    # Xử lý file upload mới (nếu có)
                    new_image = request.FILES.get('image')
                    if new_image:
                        category.image = new_image
                    
                    category.save()
                    messages.success(request, f'Đã cập nhật danh mục "{name}" thành công')
                    return redirect('shop:organization_shop:manage_categories', org_slug=org_slug)
            except Exception as e:
                messages.error(request, f'Lỗi khi cập nhật danh mục: {str(e)}')
    
    context = {
        'organization': organization,
        'category': category,
    }
    
    return render(request, 'shop/organization/edit_category.html', context)


@login_required
def delete_category(request, org_slug, category_id):
    """Xóa danh mục"""
    organization = get_object_or_404(Organization, slug=org_slug)
    
    # Kiểm tra quyền truy cập
    if not organization.members.filter(id=request.user.id).exists():
        messages.error(request, 'Bạn không có quyền truy cập shop này')
        return redirect('organizations:dashboard')
    
    category = get_object_or_404(OrganizationCategory, id=category_id, organization=organization)
    
    if request.method == 'POST':
        category_name = category.name
        product_count = category.products.count()
        
        if product_count > 0:
            messages.error(request, f'Không thể xóa danh mục "{category_name}" vì còn {product_count} sản phẩm. Hãy chuyển các sản phẩm sang danh mục khác trước.')
            return redirect('shop:organization_shop:manage_categories', org_slug=org_slug)
        
        category.delete()
        messages.success(request, f'Đã xóa danh mục "{category_name}" thành công')
        return redirect('shop:organization_shop:manage_categories', org_slug=org_slug)
    
    context = {
        'organization': organization,
        'category': category,
    }
    
    return render(request, 'shop/organization/delete_category.html', context)


@login_required
def organization_shop_dashboard(request, org_slug):
    """Dashboard quản lý shop của Organization"""
    organization = get_object_or_404(Organization, slug=org_slug)
    
    # Kiểm tra quyền truy cập
    if not organization.members.filter(id=request.user.id).exists():
        return render(request, 'shop/organization/access_denied.html', {
            'organization': organization
        })
    
    # Thống kê tổng quan
    today = timezone.now().date()
    this_month = today.replace(day=1)
    last_month = (this_month - timedelta(days=1)).replace(day=1)
    
    # Đơn hàng
    total_orders = OrganizationOrder.objects.filter(organization=organization).count()
    pending_orders = OrganizationOrder.objects.filter(
        organization=organization, status='pending'
    ).count()
    processing_orders = OrganizationOrder.objects.filter(
        organization=organization, status='processing'
    ).count()
    completed_orders = OrganizationOrder.objects.filter(
        organization=organization, status='delivered'
    ).count()
    
    # Doanh thu
    total_revenue = OrganizationOrder.objects.filter(
        organization=organization,
        payment_status='paid'
    ).aggregate(total=Sum('total_amount'))['total'] or 0
    
    monthly_revenue = OrganizationOrder.objects.filter(
        organization=organization,
        payment_status='paid',
        created_at__gte=this_month
    ).aggregate(total=Sum('total_amount'))['total'] or 0
    
    # Sản phẩm
    total_products = OrganizationProduct.objects.filter(organization=organization).count()
    out_of_stock = OrganizationProduct.objects.filter(
        organization=organization, stock_quantity=0
    ).count()
    low_stock = OrganizationProduct.objects.filter(
        organization=organization, 
        stock_quantity__lte=10, 
        stock_quantity__gt=0
    ).count()
    
    # Đơn hàng gần đây
    recent_orders = OrganizationOrder.objects.filter(
        organization=organization
    ).select_related('user').order_by('-created_at')[:10]
    
    # Sản phẩm bán chạy
    bestseller_products = OrganizationProduct.objects.filter(
        organization=organization
    ).annotate(
        total_sold=Sum('organizationorderitem__quantity')
    ).order_by('-total_sold')[:5]
    
    # Thống kê theo tháng (7 tháng gần nhất)
    monthly_stats = []
    for i in range(7):
        month_date = today.replace(day=1) - timedelta(days=30*i)
        next_month = (month_date + timedelta(days=32)).replace(day=1)
        
        month_orders = OrganizationOrder.objects.filter(
            organization=organization,
            created_at__gte=month_date,
            created_at__lt=next_month
        ).count()
        
        month_revenue = OrganizationOrder.objects.filter(
            organization=organization,
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
    payment_stats = OrganizationOrder.objects.filter(
        organization=organization
    ).values('payment_status').annotate(
        count=Count('id'),
        total=Sum('total_amount')
    ).order_by('payment_status')
    
    # Top categories
    top_categories = OrganizationCategory.objects.filter(
        organization=organization
    ).annotate(
        product_count=Count('products'),
        order_count=Sum('products__organizationorderitem__quantity')
    ).order_by('-order_count')[:5]
    
    # Shop settings
    shop_settings, created = OrganizationShopSettings.objects.get_or_create(
        organization=organization
    )
    
    context = {
        'organization': organization,
        'shop_settings': shop_settings,
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
        'is_btc_member': True,  # User đã được kiểm tra quyền ở trên
    }
    
    return render(request, 'shop/organization/dashboard.html', context)
