from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import (
    Category, Product, ProductImage, Cart, CartItem, Order, OrderItem, 
    ShopBanner, ProductImport, ProductSize, ProductVariant,
    PaymentMethod, BankAccount, EWalletAccount, PaymentStep, ContactInfo, PaymentPolicy
)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    def changelist_view(self, request, extra_context=None):
        """Thêm link dashboard vào changelist"""
        extra_context = extra_context or {}
        extra_context['dashboard_url'] = reverse('shop:admin_dashboard')
        return super().changelist_view(request, extra_context)
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
    def changelist_view(self, request, extra_context=None):
        """Thêm link dashboard vào changelist"""
        extra_context = extra_context or {}
        extra_context['dashboard_url'] = reverse('shop:admin_dashboard')
        return super().changelist_view(request, extra_context)
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
    def changelist_view(self, request, extra_context=None):
        """Thêm link dashboard vào changelist"""
        extra_context = extra_context or {}
        extra_context['dashboard_url'] = reverse('shop:admin_dashboard')
        return super().changelist_view(request, extra_context)
    list_display = ['order_number', 'customer_name', 'colored_status', 'colored_payment_status', 'total_amount', 'payment_proof_status', 'payment_proof_info', 'created_at']
    list_filter = ['status', 'payment_status', 'created_at', 'shipping_city']
    search_fields = ['order_number', 'customer_name', 'customer_email', 'customer_phone']
    readonly_fields = ['order_number', 'payment_proof_link', 'created_at', 'updated_at']
    inlines = [OrderItemInline]
    list_per_page = 25
    date_hierarchy = 'created_at'
    actions = ['mark_as_processing', 'mark_as_shipped', 'mark_as_delivered', 'mark_as_cancelled', 'mark_payment_paid']
    
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
            'fields': ('subtotal', 'shipping_fee', 'total_amount', 'payment_proof_link', 'payment_proof')
        }),
        ('Ghi chú', {
            'fields': ('notes',)
        }),
        ('Thời gian', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def colored_status(self, obj):
        """Hiển thị trạng thái đơn hàng với màu sắc"""
        status_colors = {
            'pending': '#f59e0b',      # Vàng - Chờ xử lý
            'processing': '#0ea5e9',    # Xanh dương - Đang xử lý
            'shipped': '#16a34a',       # Xanh lá - Đã giao hàng
            'delivered': '#16a34a',     # Xanh lá - Đã nhận hàng
            'cancelled': '#dc2626',     # Đỏ - Đã hủy
        }
        
        status_texts = {
            'pending': 'Chờ xử lý',
            'processing': 'Đang xử lý',
            'shipped': 'Đã giao hàng',
            'delivered': 'Đã nhận hàng',
            'cancelled': 'Đã hủy',
        }
        
        color = status_colors.get(obj.status, '#6b7280')
        text = status_texts.get(obj.status, obj.status)
        
        return format_html(
            '<span style="color: {}; font-weight: bold; padding: 4px 8px; border-radius: 4px; background: {}20;">{}</span>',
            color, color, text
        )
    colored_status.short_description = "Trạng thái"
    colored_status.admin_order_field = 'status'
    
    def colored_payment_status(self, obj):
        """Hiển thị trạng thái thanh toán với màu sắc"""
        payment_colors = {
            'pending': '#f59e0b',      # Vàng - Chờ thanh toán
            'paid': '#16a34a',         # Xanh lá - Đã thanh toán
            'failed': '#dc2626',       # Đỏ - Thanh toán thất bại
            'refunded': '#6b7280',     # Xám - Đã hoàn tiền
        }
        
        payment_texts = {
            'pending': 'Chờ thanh toán',
            'paid': 'Đã thanh toán',
            'failed': 'Thanh toán thất bại',
            'refunded': 'Đã hoàn tiền',
        }
        
        color = payment_colors.get(obj.payment_status, '#6b7280')
        text = payment_texts.get(obj.payment_status, obj.payment_status)
        
        return format_html(
            '<span style="color: {}; font-weight: bold; padding: 4px 8px; border-radius: 4px; background: {}20;">{}</span>',
            color, color, text
        )
    colored_payment_status.short_description = "Thanh toán"
    colored_payment_status.admin_order_field = 'payment_status'
    
    def payment_proof_status(self, obj):
        """Hiển thị trạng thái hóa đơn chuyển khoản"""
        if obj.payment_proof:
            import os
            file_name = os.path.basename(obj.payment_proof.name)
            return format_html(
                '<a href="{}" target="_blank" download="{}" style="color: #16a34a; font-weight: bold; text-decoration: none;">✓ Đã upload</a>',
                obj.payment_proof.url,
                file_name
            )
        elif obj.payment_status == 'paid':
            return format_html(
                '<span style="color: #16a34a; font-weight: bold;">✓ Đã thanh toán</span>'
            )
        elif obj.status == 'cancelled':
            return format_html(
                '<span style="color: #6b7280;">- Đã hủy</span>'
            )
        else:
            return format_html(
                '<span style="color: #f59e0b; font-weight: bold;">⚠ Chưa có</span>'
            )
    payment_proof_status.short_description = "Hóa đơn"
    
    def payment_proof_info(self, obj):
        """Hiển thị thông tin file hóa đơn"""
        if obj.payment_proof:
            import os
            file_name = os.path.basename(obj.payment_proof.name)
            file_size = obj.payment_proof.size if hasattr(obj.payment_proof, 'size') else 0
            
            # Format file size
            if file_size > 1024 * 1024:  # MB
                size_str = f"{file_size / (1024 * 1024):.1f} MB"
            elif file_size > 1024:  # KB
                size_str = f"{file_size / 1024:.1f} KB"
            else:
                size_str = f"{file_size} bytes"
            
            return format_html(
                '<div style="font-size: 0.85rem;">'
                '<div style="color: #374151; font-weight: 500;">{}</div>'
                '<div style="color: #6b7280;">{}</div>'
                '</div>',
                file_name,
                size_str
            )
        return '-'
    payment_proof_info.short_description = "File Info"
    
    def payment_proof_link(self, obj):
        """Hiển thị link download hóa đơn"""
        if obj.payment_proof:
            import os
            file_name = os.path.basename(obj.payment_proof.name)
            return format_html(
                '<div style="padding: 0.5rem; background: #f3f4f6; border-radius: 4px;">'
                '<a href="{}" target="_blank" download="{}" style="color: #dc2626; font-weight: 600; text-decoration: none; margin-right: 1rem; padding: 0.25rem 0.5rem; background: #fef2f2; border-radius: 3px; border: 1px solid #fecaca;">'
                '<i class="fas fa-download"></i> Tải xuống</a>'
                '<a href="{}" target="_blank" style="color: #0ea5e9; font-weight: 600; text-decoration: none; padding: 0.25rem 0.5rem; background: #eff6ff; border-radius: 3px; border: 1px solid #bfdbfe;">'
                '<i class="fas fa-eye"></i> Xem</a>'
                '<div style="font-size: 0.8rem; color: #6b7280; margin-top: 0.25rem;">{}</div>'
                '</div>',
                obj.payment_proof.url,
                file_name,
                obj.payment_proof.url,
                file_name
            )
        return format_html('<span style="color: #6b7280;">Không có file</span>')
    payment_proof_link.short_description = "Download Hóa Đơn"
    payment_proof_link.allow_tags = True
    
    def total_amount(self, obj):
        """Hiển thị tổng tiền với định dạng đẹp"""
        return format_html(
            '<span style="font-weight: bold; color: #16a34a;">{}đ</span>',
            f"{obj.total_amount:,}"
        )
    total_amount.short_description = "Tổng tiền"
    total_amount.admin_order_field = 'total_amount'
    
    def get_queryset(self, request):
        """Tối ưu query"""
        return super().get_queryset(request).select_related('user').prefetch_related('items__product')
    
    def changelist_view(self, request, extra_context=None):
        """Thêm thống kê vào trang danh sách"""
        extra_context = extra_context or {}
        
        # Thống kê đơn hàng
        total_orders = Order.objects.count()
        pending_orders = Order.objects.filter(status='pending').count()
        processing_orders = Order.objects.filter(status='processing').count()
        shipped_orders = Order.objects.filter(status='shipped').count()
        delivered_orders = Order.objects.filter(status='delivered').count()
        cancelled_orders = Order.objects.filter(status='cancelled').count()
        
        # Thống kê thanh toán
        pending_payment = Order.objects.filter(payment_status='pending').count()
        paid_orders = Order.objects.filter(payment_status='paid').count()
        
        extra_context.update({
            'total_orders': total_orders,
            'pending_orders': pending_orders,
            'processing_orders': processing_orders,
            'shipped_orders': shipped_orders,
            'delivered_orders': delivered_orders,
            'cancelled_orders': cancelled_orders,
            'pending_payment': pending_payment,
            'paid_orders': paid_orders,
        })
        
        return super().changelist_view(request, extra_context)
    
    def mark_as_processing(self, request, queryset):
        """Đánh dấu đơn hàng đang xử lý"""
        updated = queryset.filter(status='pending').update(status='processing')
        self.message_user(request, f'Đã cập nhật {updated} đơn hàng thành "Đang xử lý"')
    mark_as_processing.short_description = "Đánh dấu đang xử lý"
    
    def mark_as_shipped(self, request, queryset):
        """Đánh dấu đơn hàng đã giao"""
        updated = queryset.filter(status='processing').update(status='shipped')
        self.message_user(request, f'Đã cập nhật {updated} đơn hàng thành "Đã giao hàng"')
    mark_as_shipped.short_description = "Đánh dấu đã giao hàng"
    
    def mark_as_delivered(self, request, queryset):
        """Đánh dấu đơn hàng đã nhận"""
        updated = queryset.filter(status='shipped').update(status='delivered')
        self.message_user(request, f'Đã cập nhật {updated} đơn hàng thành "Đã nhận hàng"')
    mark_as_delivered.short_description = "Đánh dấu đã nhận hàng"
    
    def mark_as_cancelled(self, request, queryset):
        """Đánh dấu đơn hàng đã hủy"""
        updated = queryset.filter(status__in=['pending', 'processing']).update(status='cancelled')
        self.message_user(request, f'Đã hủy {updated} đơn hàng')
    mark_as_cancelled.short_description = "Hủy đơn hàng"
    
    def mark_payment_paid(self, request, queryset):
        """Đánh dấu đã thanh toán"""
        updated = queryset.filter(payment_status='pending').update(payment_status='paid')
        self.message_user(request, f'Đã cập nhật {updated} đơn hàng thành "Đã thanh toán"')
    mark_payment_paid.short_description = "Đánh dấu đã thanh toán"


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    def changelist_view(self, request, extra_context=None):
        """Thêm link dashboard vào changelist"""
        extra_context = extra_context or {}
        extra_context['dashboard_url'] = reverse('shop:admin_dashboard')
        return super().changelist_view(request, extra_context)
    list_display = ['order_link', 'product', 'quantity', 'price', 'total_price']
    list_filter = ['order__created_at', 'order__status']
    search_fields = ['order__order_number', 'product__name']
    
    def order_link(self, obj):
        """Hiển thị link đến đơn hàng với màu sắc"""
        status_colors = {
            'pending': '#f59e0b',
            'processing': '#0ea5e9',
            'shipped': '#16a34a',
            'delivered': '#16a34a',
            'cancelled': '#dc2626',
        }
        
        color = status_colors.get(obj.order.status, '#6b7280')
        return format_html(
            '<a href="/admin/shop/order/{}/change/" style="color: {}; font-weight: bold;">#{}</a>',
            obj.order.id, color, obj.order.order_number
        )
    order_link.short_description = "Đơn hàng"
    order_link.admin_order_field = 'order__order_number'
    
    def total_price(self, obj):
        """Hiển thị tổng tiền với màu sắc"""
        total = obj.total_price or 0
        return format_html(
            '<span style="font-weight: bold; color: #16a34a;">{}đ</span>',
            f"{total:,}"
        )
    total_price.short_description = "Tổng tiền"


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


# Payment Admin Classes
class BankAccountInline(admin.TabularInline):
    model = BankAccount
    extra = 0
    fields = ['bank_name', 'account_holder', 'account_number', 'branch', 'qr_code', 'order', 'is_active']


class EWalletAccountInline(admin.TabularInline):
    model = EWalletAccount
    extra = 0
    fields = ['wallet_name', 'account_info', 'qr_code', 'order', 'is_active']


@admin.register(PaymentMethod)
class PaymentMethodAdmin(admin.ModelAdmin):
    def changelist_view(self, request, extra_context=None):
        """Thêm link dashboard vào changelist"""
        extra_context = extra_context or {}
        extra_context['dashboard_url'] = reverse('shop:admin_dashboard')
        return super().changelist_view(request, extra_context)
    list_display = ['name', 'payment_type', 'order', 'is_active', 'created_at']
    list_filter = ['payment_type', 'is_active', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'updated_at']
    list_editable = ['order', 'is_active']
    inlines = [BankAccountInline, EWalletAccountInline]
    
    fieldsets = (
        ('Thông tin cơ bản', {
            'fields': ('name', 'payment_type', 'description', 'icon')
        }),
        ('Hiển thị', {
            'fields': ('order', 'is_active')
        }),
        ('Thời gian', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(BankAccount)
class BankAccountAdmin(admin.ModelAdmin):
    list_display = ['bank_name', 'account_holder', 'account_number', 'payment_method', 'order', 'is_active']
    list_filter = ['payment_method', 'is_active', 'created_at']
    search_fields = ['bank_name', 'account_holder', 'account_number']
    readonly_fields = ['created_at', 'updated_at']
    list_editable = ['order', 'is_active']
    
    fieldsets = (
        ('Thông tin tài khoản', {
            'fields': ('payment_method', 'bank_name', 'account_holder', 'account_number', 'branch')
        }),
        ('QR Code', {
            'fields': ('qr_code',)
        }),
        ('Hiển thị', {
            'fields': ('order', 'is_active')
        }),
        ('Thời gian', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(EWalletAccount)
class EWalletAccountAdmin(admin.ModelAdmin):
    list_display = ['wallet_name', 'account_info', 'payment_method', 'order', 'is_active']
    list_filter = ['payment_method', 'is_active', 'created_at']
    search_fields = ['wallet_name', 'account_info']
    readonly_fields = ['created_at', 'updated_at']
    list_editable = ['order', 'is_active']
    
    fieldsets = (
        ('Thông tin ví điện tử', {
            'fields': ('payment_method', 'wallet_name', 'account_info', 'qr_code')
        }),
        ('Hiển thị', {
            'fields': ('order', 'is_active')
        }),
        ('Thời gian', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(PaymentStep)
class PaymentStepAdmin(admin.ModelAdmin):
    list_display = ['title', 'order', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['title', 'description']
    readonly_fields = ['created_at', 'updated_at']
    list_editable = ['order', 'is_active']
    
    fieldsets = (
        ('Thông tin bước', {
            'fields': ('title', 'description')
        }),
        ('Hiển thị', {
            'fields': ('order', 'is_active')
        }),
        ('Thời gian', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(ContactInfo)
class ContactInfoAdmin(admin.ModelAdmin):
    list_display = ['name', 'contact_type', 'value', 'order', 'is_active']
    list_filter = ['contact_type', 'is_active', 'created_at']
    search_fields = ['name', 'value', 'description']
    readonly_fields = ['created_at', 'updated_at']
    list_editable = ['order', 'is_active']
    
    fieldsets = (
        ('Thông tin liên hệ', {
            'fields': ('contact_type', 'name', 'value', 'description', 'icon')
        }),
        ('Hiển thị', {
            'fields': ('order', 'is_active')
        }),
        ('Thời gian', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(PaymentPolicy)
class PaymentPolicyAdmin(admin.ModelAdmin):
    list_display = ['title', 'policy_type', 'order', 'is_active', 'created_at']
    list_filter = ['policy_type', 'is_active', 'created_at']
    search_fields = ['title', 'content']
    readonly_fields = ['created_at', 'updated_at']
    list_editable = ['order', 'is_active']
    
    fieldsets = (
        ('Thông tin chính sách', {
            'fields': ('title', 'content', 'policy_type', 'icon')
        }),
        ('Hiển thị', {
            'fields': ('order', 'is_active')
        }),
        ('Thời gian', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
