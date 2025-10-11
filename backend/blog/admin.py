from django.contrib import admin
from django.utils.html import format_html
from .models import BlogCategory, BlogPost, BlogComment, BlogTag


@admin.register(BlogCategory)
class BlogCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ['created_at', 'updated_at']


@admin.register(BlogTag)
class BlogTagAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'color_tag']
    search_fields = ['name']
    prepopulated_fields = {'slug': ('name',)}

    def color_tag(self, obj):
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 8px; border-radius: 3px;">{}</span>',
            obj.color,
            obj.color
        )
    color_tag.short_description = 'Màu'


class BlogCommentInline(admin.TabularInline):
    model = BlogComment
    extra = 0
    readonly_fields = ['created_at']


@admin.register(BlogPost)
class BlogPostAdmin(admin.ModelAdmin):
    list_display = [
        'title', 'category', 'post_type', 'status', 'author', 
        'is_featured', 'view_count', 'published_at'
    ]
    list_filter = [
        'status', 'post_type', 'category', 'is_featured', 
        'published_at', 'created_at'
    ]
    search_fields = ['title', 'excerpt', 'content']
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = [
        'view_count', 'like_count', 'created_at', 'updated_at'
    ]
    inlines = [BlogCommentInline]
    
    fieldsets = (
        ('Thông tin cơ bản', {
            'fields': ('title', 'slug', 'excerpt', 'content', 'featured_image')
        }),
        ('Phân loại', {
            'fields': ('category', 'post_type', 'tags')
        }),
        ('Tác giả và trạng thái', {
            'fields': ('author', 'status', 'is_featured')
        }),
        ('SEO', {
            'fields': ('meta_title', 'meta_description'),
            'classes': ('collapse',)
        }),
        ('Thống kê', {
            'fields': ('view_count', 'like_count'),
            'classes': ('collapse',)
        }),
        ('Thời gian', {
            'fields': ('published_at', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def save_model(self, request, obj, form, change):
        if not change:  # Tạo mới
            obj.author = request.user
        super().save_model(request, obj, form, change)


@admin.register(BlogComment)
class BlogCommentAdmin(admin.ModelAdmin):
    list_display = [
        'author_name', 'post', 'is_approved', 'created_at'
    ]
    list_filter = ['is_approved', 'created_at', 'post__category']
    search_fields = ['author_name', 'author_email', 'content']
    readonly_fields = ['created_at']
    
    actions = ['approve_comments', 'disapprove_comments']

    def approve_comments(self, request, queryset):
        queryset.update(is_approved=True)
        self.message_user(request, f'Đã duyệt {queryset.count()} bình luận.')
    approve_comments.short_description = 'Duyệt bình luận đã chọn'

    def disapprove_comments(self, request, queryset):
        queryset.update(is_approved=False)
        self.message_user(request, f'Đã hủy duyệt {queryset.count()} bình luận.')
    disapprove_comments.short_description = 'Hủy duyệt bình luận đã chọn'