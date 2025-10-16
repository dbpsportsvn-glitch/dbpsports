from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count
from django.utils import timezone
from datetime import timedelta
from .organization_models import (
    OrganizationOrder, OrganizationProduct, OrganizationCategory, 
    OrganizationCart, OrganizationCartItem, OrganizationShopSettings
)
from organizations.models import Organization


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
        total_sold=Sum('orderitem__quantity')
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
        order_count=Sum('products__orderitem__quantity')
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
    }
    
    return render(request, 'shop/organization/dashboard.html', context)
