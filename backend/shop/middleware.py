"""
Middleware để disable cache cho các API endpoints trong production
"""

class DisableCacheMiddleware:
    """
    Middleware để disable cache cho các API endpoints
    """
    
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        
        # Disable cache cho các API endpoints
        if request.path.startswith('/shop/') and (
            'add_to_cart' in request.path or 
            'update_cart' in request.path or
            'remove_from_cart' in request.path or
            'cart' in request.path
        ):
            response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
            response['Pragma'] = 'no-cache'
            response['Expires'] = '0'
            response['Last-Modified'] = ''
            response['ETag'] = ''
        
        return response
