# tournaments/urls.py

from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('livestream/', views.livestream_view, name='livestream'),
    path('shop/', views.shop_view, name='shop'),
]