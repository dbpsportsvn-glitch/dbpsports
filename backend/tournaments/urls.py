# tournaments/urls.py

from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('livestream/', views.livestream_view, name='livestream'),
    path('shop/', views.shop_view, name='shop'),
    path('tournament/<int:pk>/', views.tournament_detail, name='tournament_detail'),
    path('team/<int:pk>/', views.team_detail, name='team_detail'),
    path('tournament/<int:tournament_pk>/create_team/', views.create_team, name='create_team'),
]