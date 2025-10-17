"""
Context processor cho cả Main Shop và Organization Shop
Tự động thêm cart count vào tất cả các trang shop
"""

def unified_shop_context(request):
    """Context processor để thêm cart count vào cả main shop và organization shop pages"""
    context = {}
    
    if request.user.is_authenticated:
        try:
            # Main Shop Cart Count
            from shop.models import Cart
            main_cart, created = Cart.objects.get_or_create(user=request.user)
            context['main_cart_count'] = main_cart.total_items
            context['main_cart_total'] = main_cart.total_price
            
            # Organization Shop Cart Count (nếu đang ở organization shop)
            if request.resolver_match and 'organization_shop' in request.resolver_match.namespace:
                from organizations.models import Organization
                from shop.organization_models import OrganizationCart
                
                org_slug = request.resolver_match.kwargs.get('org_slug')
                if org_slug:
                    organization = Organization.objects.get(slug=org_slug)
                    org_cart, created = OrganizationCart.objects.get_or_create(
                        user=request.user,
                        organization=organization
                    )
                    context['org_cart_count'] = org_cart.total_items
                    context['org_cart_total'] = org_cart.total_price
        except Exception as e:
            # Nếu có lỗi, không làm fail trang
            context['main_cart_count'] = 0
            context['main_cart_total'] = 0
            context['org_cart_count'] = 0
            context['org_cart_total'] = 0
    else:
        context['main_cart_count'] = 0
        context['main_cart_total'] = 0
        context['org_cart_count'] = 0
        context['org_cart_total'] = 0
    
    return context
