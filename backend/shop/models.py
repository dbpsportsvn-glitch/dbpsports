from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from django.utils import timezone


class Category(models.Model):
    """Danh mục sản phẩm"""
    name = models.CharField(max_length=100, verbose_name="Tên danh mục")
    slug = models.SlugField(unique=True, verbose_name="Slug")
    description = models.TextField(blank=True, verbose_name="Mô tả")
    image = models.ImageField(upload_to='shop/categories/', blank=True, null=True, verbose_name="Hình ảnh")
    is_active = models.BooleanField(default=True, verbose_name="Kích hoạt")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Danh mục"
        verbose_name_plural = "Danh mục"
        ordering = ['name']

    def __str__(self):
        return self.name


class Product(models.Model):
    """Sản phẩm"""
    STATUS_CHOICES = [
        ('draft', 'Nháp'),
        ('published', 'Đã xuất bản'),
        ('out_of_stock', 'Hết hàng'),
        ('discontinued', 'Ngừng bán'),
    ]

    name = models.CharField(max_length=200, verbose_name="Tên sản phẩm")
    slug = models.SlugField(unique=True, verbose_name="Slug")
    description = models.TextField(verbose_name="Mô tả")
    short_description = models.TextField(max_length=300, blank=True, verbose_name="Mô tả ngắn")
    
    # Thông tin giá cả
    price = models.DecimalField(max_digits=10, decimal_places=0, validators=[MinValueValidator(0)], verbose_name="Giá")
    sale_price = models.DecimalField(max_digits=10, decimal_places=0, blank=True, null=True, validators=[MinValueValidator(0)], verbose_name="Giá khuyến mãi")
    
    # Thông tin sản phẩm
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products', verbose_name="Danh mục")
    sku = models.CharField(max_length=50, unique=True, verbose_name="Mã sản phẩm")
    stock_quantity = models.PositiveIntegerField(default=0, verbose_name="Số lượng tồn kho")
    weight = models.DecimalField(max_digits=8, decimal_places=2, blank=True, null=True, verbose_name="Trọng lượng (kg)")
    
    # Hình ảnh
    main_image = models.ImageField(upload_to='shop/products/', verbose_name="Hình ảnh chính")
    
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
    
    @property
    def is_on_sale(self):
        """Kiểm tra sản phẩm có đang sale không"""
        return self.sale_price is not None and self.sale_price < self.price

    class Meta:
        verbose_name = "Sản phẩm"
        verbose_name_plural = "Sản phẩm"
        ordering = ['-created_at']

    def __str__(self):
        return self.name

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


class ProductImage(models.Model):
    """Hình ảnh phụ của sản phẩm"""
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='shop/products/gallery/')
    alt_text = models.CharField(max_length=200, blank=True)
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Hình ảnh sản phẩm"
        verbose_name_plural = "Hình ảnh sản phẩm"
        ordering = ['order']

    def __str__(self):
        return f"{self.product.name} - Image {self.order}"


class Cart(models.Model):
    """Giỏ hàng"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='carts')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Giỏ hàng"
        verbose_name_plural = "Giỏ hàng"

    def __str__(self):
        return f"Cart of {self.user.username}"

    @property
    def total_items(self):
        """Tổng số sản phẩm trong giỏ"""
        return sum(item.quantity for item in self.items.all())

    @property
    def total_price(self):
        """Tổng giá trị giỏ hàng"""
        return sum(item.total_price for item in self.items.all())


class CartItem(models.Model):
    """Sản phẩm trong giỏ hàng"""
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)])
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Sản phẩm trong giỏ"
        verbose_name_plural = "Sản phẩm trong giỏ"
        unique_together = ['cart', 'product']

    def __str__(self):
        return f"{self.product.name} x {self.quantity}"

    @property
    def total_price(self):
        """Tổng giá của sản phẩm trong giỏ"""
        return self.product.current_price * self.quantity


class Order(models.Model):
    """Đơn hàng"""
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

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
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
    shipping_fee = models.DecimalField(max_digits=10, decimal_places=0, default=0, verbose_name="Phí vận chuyển")
    total_amount = models.DecimalField(max_digits=10, decimal_places=0, verbose_name="Tổng cộng")
    
    # Trạng thái
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name="Trạng thái đơn hàng")
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending', verbose_name="Trạng thái thanh toán")
    
    # Ghi chú
    notes = models.TextField(blank=True, verbose_name="Ghi chú")
    
    # Thời gian
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Đơn hàng"
        verbose_name_plural = "Đơn hàng"
        ordering = ['-created_at']

    def __str__(self):
        return f"Order {self.order_number}"

    def save(self, *args, **kwargs):
        if not self.order_number:
            self.order_number = self.generate_order_number()
        super().save(*args, **kwargs)

    def generate_order_number(self):
        """Tạo mã đơn hàng tự động"""
        import random
        import string
        while True:
            order_number = 'ORD' + ''.join(random.choices(string.digits, k=7))
            if not Order.objects.filter(order_number=order_number).exists():
                return order_number


class OrderItem(models.Model):
    """Sản phẩm trong đơn hàng"""
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(verbose_name="Số lượng")
    price = models.DecimalField(max_digits=10, decimal_places=0, verbose_name="Giá tại thời điểm đặt hàng")

    class Meta:
        verbose_name = "Sản phẩm trong đơn hàng"
        verbose_name_plural = "Sản phẩm trong đơn hàng"

    def __str__(self):
        return f"{self.product.name} x {self.quantity}"

    @property
    def total_price(self):
        """Tổng giá của sản phẩm trong đơn hàng"""
        return self.price * self.quantity
