# dbpsports_core/urls.py

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView
from django.http import HttpResponse, FileResponse
import os

# Import admin config để sắp xếp lại thứ tự
import dbpsports_core.admin_custom

# ✅ Service Worker View
def service_worker(request):
    """Serve service-worker.js file"""
    sw_path = os.path.join(settings.BASE_DIR, 'service-worker.js')
    if not os.path.exists(sw_path):
        return HttpResponse('Service Worker not found', status=404)
    response = FileResponse(open(sw_path, 'rb'), content_type='application/javascript')
    response['Service-Worker-Allowed'] = '/'
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    return response

# ✅ Manifest View
def manifest(request):
    """Serve manifest.json file"""
    manifest_path = os.path.join(settings.BASE_DIR, 'static', 'manifest.json')
    if not os.path.exists(manifest_path):
        return HttpResponse('Manifest not found', status=404)
    response = FileResponse(open(manifest_path, 'rb'), content_type='application/manifest+json')
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    return response

urlpatterns = [
    # ✅ PWA Files - phải ở đầu để không bị override
    path('service-worker.js', service_worker, name='service_worker'),
    path('manifest.json', manifest, name='manifest'),
    
    path('admin/', admin.site.urls),
    path('accounts/', include('allauth.urls')),
    path('users/', include('users.urls')),
    path('orgs/', include('organizations.urls')),
    path('sponsors/', include('sponsors.urls')),
    path('shop/', include('shop.urls')),
    path('blog/', include('blog.urls')),
    path('music/', include('music_player.urls')),
    path('', include('tournaments.urls')),
]

# Đảm bảo bạn có 2 khối "if settings.DEBUG" này
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)