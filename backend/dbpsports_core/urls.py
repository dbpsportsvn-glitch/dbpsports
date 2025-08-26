# dbpsports_core/urls.py

from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('users/', include('users.urls')),
    # Sửa dòng dưới đây
    path('', include('tournaments.urls')), # Dòng này sẽ quản lý tất cả các URL của app tournaments
]