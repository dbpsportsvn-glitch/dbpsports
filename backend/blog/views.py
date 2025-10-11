from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.generic import ListView, DetailView
from django.contrib import messages

from .models import BlogPost, BlogCategory, BlogComment, BlogTag


class BlogListView(ListView):
    """Danh sách bài viết blog"""
    model = BlogPost
    template_name = 'blog/blog_list.html'
    context_object_name = 'posts'
    paginate_by = 9

    def get_queryset(self):
        queryset = BlogPost.objects.filter(status='published').select_related('category', 'author')
        
        # Filter theo category
        category_slug = self.request.GET.get('category')
        if category_slug:
            queryset = queryset.filter(category__slug=category_slug)
        
        # Filter theo post_type
        post_type = self.request.GET.get('type')
        if post_type:
            queryset = queryset.filter(post_type=post_type)
        
        # Filter theo tag
        tag_slug = self.request.GET.get('tag')
        if tag_slug:
            queryset = queryset.filter(tags__slug=tag_slug)
        
        # Search
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) |
                Q(excerpt__icontains=search) |
                Q(content__icontains=search)
            )
        
        return queryset.order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = BlogCategory.objects.all()
        context['tags'] = BlogTag.objects.all()
        context['featured_posts'] = BlogPost.objects.filter(
            status='published'
        ).order_by('-created_at')[:3]
        
        # Context cho filter
        context['current_category'] = self.request.GET.get('category')
        context['current_type'] = self.request.GET.get('type')
        context['current_tag'] = self.request.GET.get('tag')
        context['current_search'] = self.request.GET.get('search')
        
        return context


class BlogDetailView(DetailView):
    """Chi tiết bài viết blog"""
    model = BlogPost
    template_name = 'blog/blog_detail.html'
    context_object_name = 'post'
    slug_field = 'slug'

    def get_queryset(self):
        return BlogPost.objects.filter(status='published').select_related('category', 'author')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        post = self.get_object()
        
        # Tăng view count
        post.view_count += 1
        post.save()
        
        # Bài viết liên quan
        related_posts = BlogPost.objects.filter(
            status='published',
            category=post.category
        ).exclude(id=post.id).order_by('-created_at')[:4]
        
        # Bình luận
        comments = post.comments.all().order_by('-created_at')
        
        context.update({
            'related_posts': related_posts,
            'comments': comments,
            'comment_count': comments.count(),
        })
        
        return context


def blog_home(request):
    """Trang chủ blog"""
    # Bài viết nổi bật
    featured_posts = BlogPost.objects.filter(
        status='published'
    ).order_by('-created_at')[:6]
    
    # Bài viết mới nhất
    latest_posts = BlogPost.objects.filter(
        status='published'
    ).order_by('-created_at')[:8]
    
    # Bài viết theo loại
    news_posts = BlogPost.objects.filter(
        status='published', 
        post_type='news'
    ).order_by('-created_at')[:4]
    
    review_posts = BlogPost.objects.filter(
        status='published', 
        post_type='review'
    ).order_by('-created_at')[:4]
    
    # Danh mục và tags
    categories = BlogCategory.objects.all()
    tags = BlogTag.objects.all()
    
    context = {
        'featured_posts': featured_posts,
        'latest_posts': latest_posts,
        'news_posts': news_posts,
        'review_posts': review_posts,
        'categories': categories,
        'tags': tags,
    }
    
    return render(request, 'blog/blog_home.html', context)


@require_POST
def add_comment(request, post_slug):
    """Thêm bình luận"""
    post = get_object_or_404(BlogPost, slug=post_slug, status='published')
    
    author_name = request.POST.get('author_name', '').strip()
    author_email = request.POST.get('author_email', '').strip()
    content = request.POST.get('content', '').strip()
    
    if not all([author_name, author_email, content]):
        messages.error(request, 'Vui lòng điền đầy đủ thông tin.')
        return JsonResponse({'success': False, 'message': 'Vui lòng điền đầy đủ thông tin.'})
    
    comment = BlogComment.objects.create(
        post=post,
        author=request.user if request.user.is_authenticated else None,
        content=content
    )
    
    messages.success(request, 'Bình luận của bạn đã được gửi.')
    return JsonResponse({
        'success': True, 
        'message': 'Bình luận của bạn đã được gửi.'
    })


def blog_category(request, slug):
    """Bài viết theo danh mục"""
    category = get_object_or_404(BlogCategory, slug=slug)
    posts = BlogPost.objects.filter(
        status='published', 
        category=category
    ).order_by('-created_at')
    
    # Phân trang
    paginator = Paginator(posts, 9)
    page_number = request.GET.get('page')
    posts = paginator.get_page(page_number)
    
    context = {
        'category': category,
        'posts': posts,
        'categories': BlogCategory.objects.all(),
        'tags': BlogTag.objects.all(),
        'current_category': slug,
    }
    
    return render(request, 'blog/blog_list.html', context)


def blog_tag(request, slug):
    """Bài viết theo tag"""
    tag = get_object_or_404(BlogTag, slug=slug)
    posts = BlogPost.objects.filter(
        status='published', 
        tags=tag
    ).order_by('-created_at')
    
    # Phân trang
    paginator = Paginator(posts, 9)
    page_number = request.GET.get('page')
    posts = paginator.get_page(page_number)
    
    context = {
        'tag': tag,
        'posts': posts,
        'categories': BlogCategory.objects.all(),
        'tags': BlogTag.objects.all(),
        'current_tag': slug,
    }
    
    return render(request, 'blog/blog_list.html', context)