"""
Custom middleware for DBP Sports
"""

class PermissionsPolicyMiddleware:
    """
    Middleware để thêm Permissions Policy header
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        
        # Thêm Permissions Policy header cho admin pages
        if request.path.startswith('/admin/'):
            response['Permissions-Policy'] = 'unload=self, camera=(), microphone=(), geolocation=()'
        
        return response
