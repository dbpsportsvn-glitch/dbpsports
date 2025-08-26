# dbpsports_core/urls.py

from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('users/', include('users.urls')), # Thêm dòng này vào
    path('', include('tournaments.urls')),
]