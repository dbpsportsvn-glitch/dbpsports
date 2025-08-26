# dbpsports_core/urls.py

from django.contrib import admin
from django.urls import path, include  # Thêm "include" vào đây

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('tournaments.urls')), # Thêm dòng này vào
]