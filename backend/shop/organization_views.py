# backend/shop/organization_views.py

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction
from django.core.paginator import Paginator
from django.db.models import Q
from django.urls import reverse
from django.utils import timezone
import json

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
    
    context = {
        'organization': organization,
        'shop_settings': shop_settings,
        'featured_products': featured_products,
        'bestseller_products': bestseller_products,
        'categories': categories,
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
    if category_slug:
        category = get_object_or_404(OrganizationCategory, slug=category_slug, organization=organization)
        products = products.filter(category=category)
    
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
        'current_category': category_slug,
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
            'cart_total': cart.total_items
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
            'cart_total': cart_item.cart.total_price
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
            return redirect('organization_shop_cart', org_slug=org_slug)
            
    except OrganizationCart.DoesNotExist:
        messages.warning(request, "Giỏ hàng trống")
        return redirect('organization_shop_cart', org_slug=org_slug)
    
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
        data = json.loads(request.body)
        
        # Lấy cart
        cart = OrganizationCart.objects.get(user=request.user, organization=organization)
        cart_items = cart.items.all()
        
        if not cart_items:
            return JsonResponse({'success': False, 'error': 'Giỏ hàng trống'})
        
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
                customer_name=data.get('customer_name', request.user.get_full_name() or request.user.username),
                customer_email=data.get('customer_email', request.user.email),
                customer_phone=data.get('customer_phone', ''),
                shipping_address=data.get('shipping_address', ''),
                shipping_city=data.get('shipping_city', ''),
                shipping_district=data.get('shipping_district', ''),
                subtotal=subtotal,
                shipping_fee=shipping_fee,
                total_amount=total_amount,
                payment_method=data.get('payment_method', 'cod'),
                notes=data.get('notes', ''),
            )
            
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
        
        return JsonResponse({
            'success': True, 
            'message': 'Đặt hàng thành công',
            'order_number': order.order_number,
            'redirect_url': reverse('organization_order_detail', kwargs={'org_slug': org_slug, 'order_id': order.id})
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
def organization_order_detail(request, org_slug, order_id):
    """Chi tiết đơn hàng Organization"""
    organization = get_object_or_404(Organization, slug=org_slug)
    order = get_object_or_404(
        OrganizationOrder, 
        id=order_id,
        organization=organization,
        user=request.user
    )
    
    context = {
        'organization': organization,
        'order': order,
    }
    
    return render(request, 'shop/organization/order_detail.html', context)


@login_required
def organization_order_list(request, org_slug):
    """Danh sách đơn hàng Organization"""
    organization = get_object_or_404(Organization, slug=org_slug)
    
    orders = OrganizationOrder.objects.filter(
        organization=organization,
        user=request.user
    ).order_by('-created_at')
    
    context = {
        'organization': organization,
        'orders': orders,
    }
    
    return render(request, 'shop/organization/order_list.html', context)
