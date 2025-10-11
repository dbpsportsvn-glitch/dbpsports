from django.contrib import admin
from django.utils.html import format_html
from .models import Category, Product, ProductImage, Cart, CartItem, Order, OrderItem, ShopBanner, ProductImport, ProductSize, ProductVariant


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ['created_at', 'updated_at']


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    fields = ['image', 'alt_text', 'order']


class ProductVariantInline(admin.TabularInline):
    model = ProductVariant
    extra = 0
    fields = ['size', 'sku', 'stock_quantity', 'price', 'sale_price', 'is_active']


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'current_price', 'stock_quantity', 'status', 'is_featured', 'created_at']
    list_filter = ['status', 'category', 'is_featured', 'is_bestseller', 'created_at']
    search_fields = ['name', 'description', 'sku']
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ['created_at', 'updated_at', 'published_at']
    inlines = [ProductImageInline, ProductVariantInline]
    
    fieldsets = (
        ('Thông tin cơ bản', {
            'fields': ('name', 'slug', 'category', 'sku', 'status')
        }),
        ('Mô tả', {
            'fields': ('description', 'short_description')
        }),
        ('Giá cả', {
            'fields': ('price', 'sale_price')
        }),
        ('Kho hàng', {
            'fields': ('stock_quantity', 'weight')
        }),
        ('Hình ảnh', {
            'fields': ('main_image',)
        }),
        ('Tính năng', {
            'fields': ('is_featured', 'is_bestseller')
        }),
        ('SEO', {
            'fields': ('meta_title', 'meta_description'),
            'classes': ('collapse',)
        }),
        ('Thời gian', {
            'fields': ('created_at', 'updated_at', 'published_at'),
            'classes': ('collapse',)
        }),
    )

    def current_price(self, obj):
        """Hiển thị giá hiện tại"""
        if obj.is_on_sale:
            return format_html(
                '<span style="color: #dc3545; text-decoration: line-through;">{}</span> '
                '<span style="color: #28a745; font-weight: bold;">{}</span>',
                f"{obj.price:,}đ",
                f"{obj.current_price:,}đ"
            )
        return f"{obj.current_price:,}đ"
    current_price.short_description = "Giá hiện tại"


@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ['product', 'alt_text', 'order', 'created_at']
    list_filter = ['created_at']
    search_fields = ['product__name', 'alt_text']


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ['user', 'total_items', 'total_price', 'created_at']
    list_filter = ['created_at']
    search_fields = ['user__username', 'user__email']
    readonly_fields = ['created_at', 'updated_at']

    def total_items(self, obj):
        return obj.total_items
    total_items.short_description = "Số sản phẩm"

    def total_price(self, obj):
        return f"{obj.total_price:,}đ"
    total_price.short_description = "Tổng tiền"


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ['cart', 'product', 'quantity', 'total_price', 'added_at']
    list_filter = ['added_at']
    search_fields = ['cart__user__username', 'product__name']


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ['total_price']


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['order_number', 'customer_name', 'status', 'payment_status', 'total_amount', 'created_at']
    list_filter = ['status', 'payment_status', 'created_at']
    search_fields = ['order_number', 'customer_name', 'customer_email', 'customer_phone']
    readonly_fields = ['order_number', 'created_at', 'updated_at']
    inlines = [OrderItemInline]
    
    fieldsets = (
        ('Thông tin đơn hàng', {
            'fields': ('order_number', 'user', 'status', 'payment_status')
        }),
        ('Thông tin khách hàng', {
            'fields': ('customer_name', 'customer_email', 'customer_phone')
        }),
        ('Địa chỉ giao hàng', {
            'fields': ('shipping_address', 'shipping_city', 'shipping_district')
        }),
        ('Thông tin thanh toán', {
            'fields': ('subtotal', 'shipping_fee', 'total_amount')
        }),
        ('Ghi chú', {
            'fields': ('notes',)
        }),
        ('Thời gian', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def total_amount(self, obj):
        return f"{obj.total_amount:,}đ"
    total_amount.short_description = "Tổng tiền"


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ['order', 'product', 'quantity', 'price', 'total_price']
    list_filter = ['order__created_at']
    search_fields = ['order__order_number', 'product__name']


@admin.register(ShopBanner)
class ShopBannerAdmin(admin.ModelAdmin):
    list_display = ['title', 'product', 'order', 'badge_text', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['title', 'subtitle', 'badge_text', 'product__name']
    readonly_fields = ['created_at', 'updated_at']
    list_editable = ['order', 'is_active']
    
    fieldsets = (
        ('Thông tin cơ bản', {
            'fields': ('title', 'subtitle', 'order', 'is_active')
        }),
        ('Badge và Nút', {
            'fields': ('badge_text', 'button_text', 'button_url')
        }),
        ('Sản phẩm liên kết', {
            'fields': ('product',),
            'description': 'Nếu chọn sản phẩm, click vào ảnh sẽ dẫn đến trang sản phẩm'
        }),
        ('Hình ảnh', {
            'fields': ('main_image',)
        }),
        ('Thời gian', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        """Chỉ hiển thị banner đầu tiên nếu có nhiều banner"""
        qs = super().get_queryset(request)
        return qs


@admin.register(ProductImport)
class ProductImportAdmin(admin.ModelAdmin):
    list_display = ['source_url', 'crawled_name', 'status', 'created_at', 'processed_at']
    list_filter = ['status', 'created_at']
    search_fields = ['source_url', 'crawled_name', 'source_name']
    readonly_fields = ['created_at', 'updated_at', 'processed_at']
    
    fieldsets = (
        ('Thông tin Import', {
            'fields': ('source_url', 'source_name', 'status')
        }),
        ('Thông tin Crawled', {
            'fields': ('crawled_name', 'crawled_price', 'crawled_description', 'crawled_image_url'),
            'classes': ('collapse',)
        }),
        ('Sản phẩm được tạo', {
            'fields': ('product',),
            'classes': ('collapse',)
        }),
        ('Lỗi', {
            'fields': ('error_message',),
            'classes': ('collapse',)
        }),
        ('Thời gian', {
            'fields': ('created_at', 'updated_at', 'processed_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['process_imports']
    
    def process_imports(self, request, queryset):
        """Xử lý các import được chọn"""
        from .tasks import process_product_import
        processed_count = 0
        for import_item in queryset:
            if import_item.status in ['pending', 'processing']:
                try:
                    # Reset status to pending if it's stuck in processing
                    if import_item.status == 'processing':
                        import_item.status = 'pending'
                        import_item.save()
                    
                    process_product_import(import_item.id)
                    processed_count += 1
                except Exception as e:
                    self.message_user(request, f"Lỗi khi xử lý import {import_item.id}: {str(e)}", level='ERROR')
        self.message_user(request, f"Đã xử lý {processed_count} import thành công")
    process_imports.short_description = "Xử lý các import được chọn"


@admin.register(ProductSize)
class ProductSizeAdmin(admin.ModelAdmin):
    list_display = ['name', 'size_type', 'order', 'is_active']
    list_filter = ['size_type', 'is_active']
    search_fields = ['name']
    ordering = ['size_type', 'order', 'name']


class ProductVariantInline(admin.TabularInline):
    model = ProductVariant
    extra = 0
    fields = ['size', 'sku', 'stock_quantity', 'price', 'sale_price', 'is_active']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(ProductVariant)
class ProductVariantAdmin(admin.ModelAdmin):
    list_display = ['product', 'size', 'sku', 'stock_quantity', 'effective_price', 'is_active']
    list_filter = ['is_active', 'size__size_type']
    search_fields = ['product__name', 'sku', 'size__name']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Thông tin cơ bản', {
            'fields': ('product', 'size', 'sku', 'is_active')
        }),
        ('Giá và tồn kho', {
            'fields': ('stock_quantity', 'price', 'sale_price')
        }),
        ('Thời gian', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
