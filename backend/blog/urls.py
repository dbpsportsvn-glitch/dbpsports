from django.urls import path
from . import views

app_name = 'blog'

urlpatterns = [
    path('', views.blog_home, name='home'),
    path('posts/', views.BlogListView.as_view(), name='post_list'),
    path('posts/<slug:slug>/', views.BlogDetailView.as_view(), name='post_detail'),
    path('category/<slug:slug>/', views.blog_category, name='category'),
    path('tag/<slug:slug>/', views.blog_tag, name='tag'),
    path('posts/<slug:slug>/comment/', views.add_comment, name='add_comment'),
]
