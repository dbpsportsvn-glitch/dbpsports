from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from django.utils import timezone
from organizations.models import Organization


class OrganizationCategory(models.Model):
    """Danh mục sản phẩm của Organization"""
    organization = models.ForeignKey(
        Organization, 
        on_delete=models.CASCADE, 
        related_name='shop_categories',
        verbose_name="Ban tổ chức"
    )
    name = models.CharField(max_length=100, verbose_name="Tên danh mục")
    slug = models.SlugField(verbose_name="Slug")
    description = models.TextField(blank=True, verbose_name="Mô tả")
    image = models.ImageField(upload_to='org_shop/categories/', blank=True, null=True, verbose_name="Hình ảnh")
    is_active = models.BooleanField(default=True, verbose_name="Kích hoạt")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Danh mục Shop BTC"
        verbose_name_plural = "Danh mục Shop BTC"
        ordering = ['name']
        unique_together = ['organization', 'slug']  # Slug chỉ cần unique trong cùng 1 organization

    def __str__(self):
        return f"{self.organization.name} - {self.name}"


class OrganizationProduct(models.Model):
    """Sản phẩm của Organization"""
    STATUS_CHOICES = [
        ('draft', 'Nháp'),
        ('published', 'Đã xuất bản'),
        ('out_of_stock', 'Hết hàng'),
        ('discontinued', 'Ngừng bán'),
    ]

    organization = models.ForeignKey(
        Organization, 
        on_delete=models.CASCADE, 
        related_name='shop_products',
        verbose_name="Ban tổ chức"
    )
    name = models.CharField(max_length=200, verbose_name="Tên sản phẩm")
    slug = models.SlugField(verbose_name="Slug")
    description = models.TextField(verbose_name="Mô tả")
    short_description = models.TextField(max_length=300, blank=True, verbose_name="Mô tả ngắn")
    
    # Thông tin giá cả
    price = models.DecimalField(max_digits=10, decimal_places=0, validators=[MinValueValidator(0)], verbose_name="Giá")
    sale_price = models.DecimalField(max_digits=10, decimal_places=0, blank=True, null=True, validators=[MinValueValidator(0)], verbose_name="Giá khuyến mãi")
    cost_price = models.DecimalField(max_digits=10, decimal_places=0, blank=True, null=True, validators=[MinValueValidator(0)], verbose_name="Giá vốn", help_text="Giá nhập vào để tính lãi")
    
    # Thông tin sản phẩm
    category = models.ForeignKey(OrganizationCategory, on_delete=models.CASCADE, related_name='products', verbose_name="Danh mục")
    sku = models.CharField(max_length=50, verbose_name="Mã sản phẩm")
    stock_quantity = models.PositiveIntegerField(default=0, verbose_name="Số lượng tồn kho")
    weight = models.DecimalField(max_digits=8, decimal_places=2, blank=True, null=True, verbose_name="Trọng lượng (kg)")
    
    # Size và variant (tái sử dụng ProductSize từ shop global)
    available_sizes = models.ManyToManyField('shop.ProductSize', blank=True, verbose_name="Size có sẵn")
    has_sizes = models.BooleanField(default=False, verbose_name="Có nhiều size")
    
    # Hình ảnh
    main_image = models.ImageField(upload_to='org_shop/products/', verbose_name="Hình ảnh chính")
    
    # Thông tin import
    source_url = models.URLField(blank=True, null=True, verbose_name="Link gốc")
    is_imported = models.BooleanField(default=False, verbose_name="Sản phẩm import")
    
    # Trạng thái
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft', verbose_name="Trạng thái")
    is_featured = models.BooleanField(default=False, verbose_name="Sản phẩm nổi bật")
    is_bestseller = models.BooleanField(default=False, verbose_name="Bán chạy")
    
    # SEO
    meta_title = models.CharField(max_length=200, blank=True, verbose_name="Meta title")
    meta_description = models.TextField(blank=True, verbose_name="Meta description")
    
    # Thời gian
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    published_at = models.DateTimeField(blank=True, null=True, verbose_name="Ngày xuất bản")

    class Meta:
        verbose_name = "Sản phẩm Shop BTC"
        verbose_name_plural = "Sản phẩm Shop BTC"
        ordering = ['-created_at']
        unique_together = ['organization', 'slug']  # Slug chỉ cần unique trong cùng 1 organization
        unique_together = ['organization', 'sku']   # SKU chỉ cần unique trong cùng 1 organization

    def __str__(self):
        return f"{self.organization.name} - {self.name}"

    def save(self, *args, **kwargs):
        if self.status == 'published' and not self.published_at:
            self.published_at = timezone.now()
        super().save(*args, **kwargs)

    @property
    def current_price(self):
        """Giá hiện tại (ưu tiên giá khuyến mãi)"""
        return self.sale_price if self.sale_price else self.price

    @property
    def discount_percentage(self):
        """Phần trăm giảm giá"""
        if self.sale_price and self.price > self.sale_price:
            return int((self.price - self.sale_price) / self.price * 100)
        return 0

    @property
    def is_on_sale(self):
        """Có đang khuyến mãi không"""
        return self.sale_price is not None and self.sale_price < self.price

    @property
    def is_available(self):
        """Sản phẩm có sẵn không"""
        return self.status == 'published' and self.stock_quantity > 0
    
    @property
    def profit_amount(self):
        """Số tiền lãi của sản phẩm"""
        if not self.cost_price:
            return 0
        return self.current_price - self.cost_price
    
    @property
    def profit_percentage(self):
        """Phần trăm lãi của sản phẩm"""
        if not self.cost_price or self.cost_price == 0:
            return 0
        return (self.profit_amount / self.cost_price) * 100


class OrganizationProductVariant(models.Model):
    """Biến thể sản phẩm theo size của Organization"""
    product = models.ForeignKey(OrganizationProduct, on_delete=models.CASCADE, related_name='variants', verbose_name="Sản phẩm")
    size = models.ForeignKey('shop.ProductSize', on_delete=models.CASCADE, verbose_name="Size")
    sku = models.CharField(max_length=50, verbose_name="Mã SKU")
    stock_quantity = models.PositiveIntegerField(default=0, verbose_name="Số lượng tồn kho")
    price = models.DecimalField(max_digits=10, decimal_places=0, blank=True, null=True, validators=[MinValueValidator(0)], verbose_name="Giá riêng")
    sale_price = models.DecimalField(max_digits=10, decimal_places=0, blank=True, null=True, validators=[MinValueValidator(0)], verbose_name="Giá khuyến mãi riêng")
    is_active = models.BooleanField(default=True, verbose_name="Kích hoạt")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Biến thể sản phẩm Shop BTC"
        verbose_name_plural = "Biến thể sản phẩm Shop BTC"
        unique_together = ['product', 'size']
        ordering = ['product', 'size__order', 'size__name']
    
    def __str__(self):
        return f"{self.product.name} - {self.size.name}"
    
    @property
    def effective_price(self):
        """Giá hiệu quả (ưu tiên giá riêng, sau đó giá sản phẩm)"""
        if self.price:
            return self.price
        return self.product.price
    
    @property
    def effective_sale_price(self):
        """Giá khuyến mãi hiệu quả"""
        if self.sale_price:
            return self.sale_price
        return self.product.sale_price
    
    @property
    def is_on_sale(self):
        """Có đang khuyến mãi không"""
        sale_price = self.effective_sale_price
        if sale_price and sale_price < self.effective_price:
            return True
        return False


class OrganizationProductImage(models.Model):
    """Hình ảnh phụ của sản phẩm Organization"""
    product = models.ForeignKey(OrganizationProduct, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='org_shop/products/gallery/')
    alt_text = models.CharField(max_length=200, blank=True)
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Hình ảnh sản phẩm Shop BTC"
        verbose_name_plural = "Hình ảnh sản phẩm Shop BTC"
        ordering = ['order']

    def __str__(self):
        return f"{self.product.name} - Image {self.order}"


class OrganizationCart(models.Model):
    """Giỏ hàng của Organization"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='org_carts')
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='carts')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Giỏ hàng Shop BTC"
        verbose_name_plural = "Giỏ hàng Shop BTC"
        unique_together = ['user', 'organization']  # Mỗi user chỉ có 1 cart per organization

    def __str__(self):
        return f"Cart of {self.user.username} for {self.organization.name}"

    @property
    def total_items(self):
        """Tổng số sản phẩm trong giỏ"""
        return sum(item.quantity for item in self.items.all())

    @property
    def total_price(self):
        """Tổng giá trị giỏ hàng"""
        return sum(item.total_price for item in self.items.all())


class OrganizationCartItem(models.Model):
    """Sản phẩm trong giỏ hàng Organization"""
    cart = models.ForeignKey(OrganizationCart, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(OrganizationProduct, on_delete=models.CASCADE)
    size = models.ForeignKey('shop.ProductSize', on_delete=models.CASCADE, null=True, blank=True, verbose_name="Size")
    quantity = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)])
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Sản phẩm trong giỏ Shop BTC"
        verbose_name_plural = "Sản phẩm trong giỏ Shop BTC"
        unique_together = ['cart', 'product', 'size']

    def __str__(self):
        size_text = f" - {self.size.name}" if self.size else ""
        return f"{self.product.name}{size_text} x {self.quantity}"

    @property
    def total_price(self):
        """Tổng giá của sản phẩm trong giỏ"""
        return self.product.current_price * self.quantity


class OrganizationOrder(models.Model):
    """Đơn hàng của Organization"""
    STATUS_CHOICES = [
        ('pending', 'Chờ xử lý'),
        ('processing', 'Đang xử lý'),
        ('shipped', 'Đã gửi hàng'),
        ('delivered', 'Đã giao hàng'),
        ('cancelled', 'Đã hủy'),
    ]

    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Chờ thanh toán'),
        ('paid', 'Đã thanh toán'),
        ('failed', 'Thanh toán thất bại'),
        ('refunded', 'Đã hoàn tiền'),
    ]

    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='shop_orders', verbose_name="Ban tổ chức")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='org_orders')
    order_number = models.CharField(max_length=20, unique=True, verbose_name="Mã đơn hàng")
    
    # Thông tin khách hàng
    customer_name = models.CharField(max_length=100, verbose_name="Tên khách hàng")
    customer_email = models.EmailField(verbose_name="Email")
    customer_phone = models.CharField(max_length=20, verbose_name="Số điện thoại")
    
    # Địa chỉ giao hàng
    shipping_address = models.TextField(verbose_name="Địa chỉ giao hàng")
    shipping_city = models.CharField(max_length=100, verbose_name="Thành phố")
    shipping_district = models.CharField(max_length=100, verbose_name="Quận/Huyện")
    
    # Thông tin đơn hàng
    subtotal = models.DecimalField(max_digits=10, decimal_places=0, verbose_name="Tổng tiền hàng")
    discount_amount = models.DecimalField(max_digits=10, decimal_places=0, default=0, verbose_name="Số tiền giảm giá")
    shipping_fee = models.DecimalField(max_digits=10, decimal_places=0, default=0, verbose_name="Phí vận chuyển")
    total_amount = models.DecimalField(max_digits=10, decimal_places=0, verbose_name="Tổng cộng")
    
    # Trạng thái
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name="Trạng thái đơn hàng")
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending', verbose_name="Trạng thái thanh toán")
    
    # Phương thức thanh toán
    PAYMENT_METHOD_CHOICES = [
        ('cod', 'Thanh toán khi nhận hàng (COD)'),
        ('bank_transfer', 'Chuyển khoản ngân hàng'),
        ('e_wallet', 'Ví điện tử'),
    ]
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, default='cod', verbose_name="Phương thức thanh toán")
    
    # Ghi chú
    notes = models.TextField(blank=True, verbose_name="Ghi chú")
    
    # Payment proof
    payment_proof = models.ImageField(upload_to='org_shop/payment_proofs/', blank=True, null=True, verbose_name="Hóa đơn chuyển khoản")
    
    # Thời gian
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Đơn hàng Shop BTC"
        verbose_name_plural = "Đơn hàng Shop BTC"
        ordering = ['-created_at']

    def __str__(self):
        return f"Order {self.order_number} - {self.organization.name}"
    
    def get_payment_method_display(self):
        """Lấy tên hiển thị của phương thức thanh toán"""
        return dict(self.PAYMENT_METHOD_CHOICES).get(self.payment_method, self.payment_method)

    def save(self, *args, **kwargs):
        if not self.order_number:
            self.order_number = self.generate_order_number()
        super().save(*args, **kwargs)

    def generate_order_number(self):
        """Tạo mã đơn hàng tự động"""
        import random
        import string
        while True:
            order_number = f'ORG{self.organization.id:03d}' + ''.join(random.choices(string.digits, k=6))
            if not OrganizationOrder.objects.filter(order_number=order_number).exists():
                return order_number


class OrganizationOrderItem(models.Model):
    """Sản phẩm trong đơn hàng Organization"""
    order = models.ForeignKey(OrganizationOrder, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(OrganizationProduct, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(verbose_name="Số lượng")
    price = models.DecimalField(max_digits=10, decimal_places=0, verbose_name="Giá tại thời điểm đặt hàng")

    class Meta:
        verbose_name = "Sản phẩm trong đơn hàng Shop BTC"
        verbose_name_plural = "Sản phẩm trong đơn hàng Shop BTC"

    def __str__(self):
        return f"{self.product.name} x {self.quantity}"

    @property
    def total_price(self):
        """Tổng giá của sản phẩm trong đơn hàng"""
        if self.price is not None and self.quantity is not None:
            return self.price * self.quantity
        return 0


class OrganizationShopSettings(models.Model):
    """Cài đặt shop của Organization"""
    organization = models.OneToOneField(Organization, on_delete=models.CASCADE, related_name='shop_settings', verbose_name="Ban tổ chức")
    
    # Thông tin shop
    shop_name = models.CharField(max_length=200, verbose_name="Tên shop", help_text="Tên hiển thị của shop")
    shop_description = models.TextField(blank=True, verbose_name="Mô tả shop")
    shop_logo = models.ImageField(upload_to='org_shop/logos/', blank=True, null=True, verbose_name="Logo shop")
    shop_banner = models.ImageField(upload_to='org_shop/banners/', blank=True, null=True, verbose_name="Banner shop", help_text="Banner hiển thị trên đầu trang shop")
    
    # Thông tin liên hệ
    contact_phone = models.CharField(max_length=20, blank=True, verbose_name="Số điện thoại")
    contact_email = models.EmailField(blank=True, verbose_name="Email")
    contact_address = models.TextField(blank=True, verbose_name="Địa chỉ")
    
    # Cài đặt thanh toán
    bank_name = models.CharField(max_length=100, blank=True, verbose_name="Tên ngân hàng")
    bank_account_number = models.CharField(max_length=50, blank=True, verbose_name="Số tài khoản")
    bank_account_name = models.CharField(max_length=100, blank=True, verbose_name="Tên chủ tài khoản")
    payment_qr_code = models.ImageField(upload_to='org_shop/qr_codes/', blank=True, null=True, verbose_name="QR Code thanh toán")
    
    # Cài đặt giao hàng
    shipping_fee = models.DecimalField(max_digits=10, decimal_places=0, default=0, verbose_name="Phí vận chuyển mặc định")
    free_shipping_threshold = models.DecimalField(max_digits=10, decimal_places=0, blank=True, null=True, verbose_name="Ngưỡng miễn phí ship")
    
    # Trạng thái
    is_active = models.BooleanField(default=True, verbose_name="Kích hoạt shop")
    
    # Shop Lock System
    shop_locked = models.BooleanField(default=True, verbose_name="Khoá Shop BTC", help_text="Shop BTC bị khoá mặc định và cần Admin phê duyệt để mở")
    shop_lock_reason = models.TextField(blank=True, verbose_name="Lý do khoá shop", help_text="Ghi chú từ Admin về lý do khoá shop")
    shop_unlock_requested = models.BooleanField(default=False, verbose_name="BTC đã yêu cầu mở khoá", help_text="BTC đã gửi yêu cầu mở khoá shop")
    shop_unlock_request_date = models.DateTimeField(blank=True, null=True, verbose_name="Ngày yêu cầu mở khoá")
    shop_unlock_request_message = models.TextField(blank=True, verbose_name="Lời nhắn từ BTC", help_text="Lời nhắn từ BTC khi yêu cầu mở khoá shop")
    
    # Thời gian
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Cài đặt Shop BTC"
        verbose_name_plural = "Cài đặt Shop BTC"

    def __str__(self):
        return f"Cài đặt shop của {self.organization.name}"
