# organizations/urls.py
from django.urls import path
from . import views

app_name = 'organizations'

urlpatterns = [
    path('dashboard/', views.organization_dashboard, name='dashboard'),
    path('tournaments/create/', views.create_tournament, name='create_tournament'),
    path('tournaments/<int:pk>/manage/', views.manage_tournament, name='manage_tournament'),
    path('groups/<int:pk>/delete/', views.delete_group, name='delete_group'),
    path('tournaments/<int:pk>/delete/', views.delete_tournament, name='delete_tournament'),
]