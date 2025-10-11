from django.db import models
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils.text import slugify
from django.utils import timezone

User = get_user_model()


class BlogCategory(models.Model):
    """Danh mục blog"""
    name = models.CharField(max_length=100, verbose_name="Tên danh mục")
    slug = models.SlugField(max_length=100, unique=True, verbose_name="Slug")
    description = models.TextField(blank=True, verbose_name="Mô tả")
    is_active = models.BooleanField(default=True, verbose_name="Hoạt động")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Ngày tạo")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Ngày cập nhật")

    class Meta:
        verbose_name = "Danh mục blog"
        verbose_name_plural = "Danh mục blog"
        ordering = ['name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class BlogPost(models.Model):
    """Bài viết blog"""
    POST_TYPE_CHOICES = [
        ('news', 'Tin tức'),
        ('review', 'Review sản phẩm'),
        ('guide', 'Hướng dẫn'),
        ('tips', 'Mẹo hay'),
    ]

    STATUS_CHOICES = [
        ('draft', 'Bản nháp'),
        ('published', 'Đã xuất bản'),
        ('archived', 'Lưu trữ'),
    ]

    title = models.CharField(max_length=200, verbose_name="Tiêu đề")
    slug = models.SlugField(max_length=200, unique=True, verbose_name="Slug")
    excerpt = models.TextField(max_length=500, verbose_name="Tóm tắt")
    content = models.TextField(verbose_name="Nội dung")
    featured_image = models.ImageField(
        upload_to='blog/images/', 
        blank=True, 
        null=True, 
        verbose_name="Ảnh đại diện"
    )
    
    # Phân loại
    category = models.ForeignKey(
        BlogCategory, 
        on_delete=models.CASCADE, 
        verbose_name="Danh mục"
    )
    tags = models.ManyToManyField(
        'BlogTag', 
        blank=True, 
        verbose_name="Tags"
    )
    post_type = models.CharField(
        max_length=20, 
        choices=POST_TYPE_CHOICES, 
        default='news',
        verbose_name="Loại bài viết"
    )
    
    # Tác giả và trạng thái
    author = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        verbose_name="Tác giả"
    )
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='draft',
        verbose_name="Trạng thái"
    )
    
    # SEO và hiển thị
    meta_title = models.CharField(
        max_length=200, 
        blank=True, 
        verbose_name="Meta title"
    )
    meta_description = models.TextField(
        max_length=300, 
        blank=True, 
        verbose_name="Meta description"
    )
    is_featured = models.BooleanField(default=False, verbose_name="Bài viết nổi bật")
    
    # Thống kê
    view_count = models.PositiveIntegerField(default=0, verbose_name="Lượt xem")
    like_count = models.PositiveIntegerField(default=0, verbose_name="Lượt thích")
    
    # Thời gian
    published_at = models.DateTimeField(
        blank=True, 
        null=True, 
        verbose_name="Ngày xuất bản"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Ngày tạo")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Ngày cập nhật")

    class Meta:
        verbose_name = "Bài viết blog"
        verbose_name_plural = "Bài viết blog"
        ordering = ['-published_at', '-created_at']

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        
        # Tự động set published_at khi status = published
        if self.status == 'published' and not self.published_at:
            self.published_at = timezone.now()
        
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('blog:post_detail', kwargs={'slug': self.slug})

    def increment_view_count(self):
        """Tăng số lượt xem"""
        self.view_count += 1
        self.save(update_fields=['view_count'])


class BlogComment(models.Model):
    """Bình luận blog"""
    post = models.ForeignKey(
        BlogPost, 
        on_delete=models.CASCADE, 
        related_name='comments',
        verbose_name="Bài viết"
    )
    author_name = models.CharField(max_length=100, verbose_name="Tên tác giả")
    author_email = models.EmailField(verbose_name="Email tác giả")
    content = models.TextField(verbose_name="Nội dung bình luận")
    is_approved = models.BooleanField(default=False, verbose_name="Đã duyệt")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Ngày tạo")

    class Meta:
        verbose_name = "Bình luận"
        verbose_name_plural = "Bình luận"
        ordering = ['-created_at']

    def __str__(self):
        return f"Bình luận của {self.author_name} cho {self.post.title}"


class BlogTag(models.Model):
    """Tag blog"""
    name = models.CharField(max_length=50, unique=True, verbose_name="Tên tag")
    slug = models.SlugField(max_length=50, unique=True, verbose_name="Slug")
    color = models.CharField(
        max_length=7, 
        default='#007bff', 
        verbose_name="Màu tag"
    )

    class Meta:
        verbose_name = "Tag"
        verbose_name_plural = "Tags"
        ordering = ['name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)