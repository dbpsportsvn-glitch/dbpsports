"""
Context processor cho Organization Shop
Tự động thêm cart count vào tất cả các trang organization shop
"""

def organization_shop_context(request):
    """Context processor để thêm cart count vào organization shop pages"""
    context = {}
    
    # Chỉ áp dụng cho organization shop URLs
    if request.resolver_match and 'organization_shop' in request.resolver_match.namespace:
        if request.user.is_authenticated:
            try:
                # Lấy org_slug từ URL
                org_slug = request.resolver_match.kwargs.get('org_slug')
                if org_slug:
                    from organizations.models import Organization
                    from shop.organization_models import OrganizationCart
                    
                    organization = Organization.objects.get(slug=org_slug)
                    cart, created = OrganizationCart.objects.get_or_create(
                        user=request.user,
                        organization=organization
                    )
                    context['org_cart_count'] = cart.total_items
                    context['org_cart_total'] = cart.total_price
            except:
                # Nếu có lỗi, không làm fail trang
                context['org_cart_count'] = 0
                context['org_cart_total'] = 0
        else:
            context['org_cart_count'] = 0
            context['org_cart_total'] = 0
    
    return context
