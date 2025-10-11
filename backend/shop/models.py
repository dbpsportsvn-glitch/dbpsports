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


class ProductSize(models.Model):
    """Size sản phẩm"""
    SIZE_TYPE_CHOICES = [
        ('shoes', 'Giày'),
        ('clothing', 'Quần áo'),
        ('accessories', 'Phụ kiện'),
    ]
    
    name = models.CharField(max_length=20, verbose_name="Tên size")
    size_type = models.CharField(max_length=20, choices=SIZE_TYPE_CHOICES, verbose_name="Loại size")
    order = models.PositiveIntegerField(default=0, verbose_name="Thứ tự")
    is_active = models.BooleanField(default=True, verbose_name="Kích hoạt")
    
    class Meta:
        verbose_name = "Size sản phẩm"
        verbose_name_plural = "Size sản phẩm"
        ordering = ['size_type', 'order', 'name']
        unique_together = ['name', 'size_type']
    
    def __str__(self):
        return f"{self.name} ({self.get_size_type_display()})"


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
    
    # Size và variant
    available_sizes = models.ManyToManyField(ProductSize, blank=True, verbose_name="Size có sẵn")
    has_sizes = models.BooleanField(default=False, verbose_name="Có nhiều size")
    
    # Hình ảnh
    main_image = models.ImageField(upload_to='shop/products/', verbose_name="Hình ảnh chính")
    
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


class ProductVariant(models.Model):
    """Biến thể sản phẩm theo size"""
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='variants', verbose_name="Sản phẩm")
    size = models.ForeignKey(ProductSize, on_delete=models.CASCADE, verbose_name="Size")
    sku = models.CharField(max_length=50, verbose_name="Mã SKU")
    stock_quantity = models.PositiveIntegerField(default=0, verbose_name="Số lượng tồn kho")
    price = models.DecimalField(max_digits=10, decimal_places=0, blank=True, null=True, validators=[MinValueValidator(0)], verbose_name="Giá riêng")
    sale_price = models.DecimalField(max_digits=10, decimal_places=0, blank=True, null=True, validators=[MinValueValidator(0)], verbose_name="Giá khuyến mãi riêng")
    is_active = models.BooleanField(default=True, verbose_name="Kích hoạt")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Biến thể sản phẩm"
        verbose_name_plural = "Biến thể sản phẩm"
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
    size = models.ForeignKey(ProductSize, on_delete=models.CASCADE, null=True, blank=True, verbose_name="Size")
    quantity = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)])
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Sản phẩm trong giỏ"
        verbose_name_plural = "Sản phẩm trong giỏ"
        unique_together = ['cart', 'product', 'size']

    def __str__(self):
        size_text = f" - {self.size.name}" if self.size else ""
        return f"{self.product.name}{size_text} x {self.quantity}"

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
    payment_proof = models.ImageField(upload_to='shop/payment_proofs/', blank=True, null=True, verbose_name="Hóa đơn chuyển khoản")
    
    # Thời gian
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Đơn hàng"
        verbose_name_plural = "Đơn hàng"
        ordering = ['-created_at']

    def __str__(self):
        return f"Order {self.order_number}"
    
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
        if self.price is not None and self.quantity is not None:
            return self.price * self.quantity
        return 0


class ShopBanner(models.Model):
    """Banner trang chủ shop"""
    title = models.CharField(max_length=200, verbose_name="Tiêu đề chính")
    subtitle = models.TextField(verbose_name="Tiêu đề phụ")
    badge_text = models.CharField(max_length=100, verbose_name="Text badge")
    button_text = models.CharField(max_length=50, verbose_name="Text nút")
    button_url = models.CharField(max_length=200, default="/shop/products/", verbose_name="URL nút")
    
    # Hình ảnh
    main_image = models.ImageField(upload_to='shop/banners/', verbose_name="Hình ảnh chính")
    
    # Sản phẩm liên kết
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Sản phẩm liên kết")
    
    # Thứ tự hiển thị
    order = models.PositiveIntegerField(default=0, verbose_name="Thứ tự")
    
    # Trạng thái
    is_active = models.BooleanField(default=True, verbose_name="Kích hoạt")
    
    # Thời gian
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Banner Shop"
        verbose_name_plural = "Banner Shop"
        ordering = ['order', '-created_at']

    def __str__(self):
        return self.title
    
    @property
    def link_url(self):
        """URL liên kết - ưu tiên sản phẩm, sau đó là button_url"""
        if self.product:
            return f"/shop/products/{self.product.slug}/"
        return self.button_url


class ProductImport(models.Model):
    """Sản phẩm được import từ website khác"""
    STATUS_CHOICES = [
        ('pending', 'Chờ xử lý'),
        ('processing', 'Đang xử lý'),
        ('completed', 'Hoàn thành'),
        ('failed', 'Thất bại'),
    ]
    
    # Thông tin import
    source_url = models.URLField(verbose_name="URL nguồn")
    source_name = models.CharField(max_length=100, blank=True, verbose_name="Tên nguồn")
    
    # Thông tin sản phẩm được crawl
    crawled_name = models.CharField(max_length=200, blank=True, verbose_name="Tên sản phẩm")
    crawled_price = models.DecimalField(max_digits=10, decimal_places=0, null=True, blank=True, verbose_name="Giá")
    crawled_description = models.TextField(blank=True, verbose_name="Mô tả")
    crawled_image_url = models.URLField(blank=True, verbose_name="URL hình ảnh")
    
    # Sản phẩm được tạo
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Sản phẩm")
    
    # Trạng thái
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name="Trạng thái")
    error_message = models.TextField(blank=True, verbose_name="Thông báo lỗi")
    
    # Thời gian
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    processed_at = models.DateTimeField(null=True, blank=True, verbose_name="Thời gian xử lý")

    class Meta:
        verbose_name = "Import Sản phẩm"
        verbose_name_plural = "Import Sản phẩm"
        ordering = ['-created_at']

    def __str__(self):
        return f"Import: {self.source_url}"


class PaymentMethod(models.Model):
    """Phương thức thanh toán"""
    PAYMENT_TYPE_CHOICES = [
        ('bank_transfer', 'Chuyển khoản ngân hàng'),
        ('e_wallet', 'Ví điện tử'),
        ('cod', 'Thanh toán khi nhận hàng'),
    ]
    
    name = models.CharField(max_length=100, verbose_name="Tên phương thức")
    payment_type = models.CharField(max_length=20, choices=PAYMENT_TYPE_CHOICES, verbose_name="Loại thanh toán")
    description = models.TextField(blank=True, verbose_name="Mô tả")
    icon = models.CharField(max_length=50, default='fas fa-credit-card', verbose_name="Icon")
    is_active = models.BooleanField(default=True, verbose_name="Kích hoạt")
    order = models.PositiveIntegerField(default=0, verbose_name="Thứ tự")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Phương thức thanh toán"
        verbose_name_plural = "Phương thức thanh toán"
        ordering = ['order', 'name']
    
    def __str__(self):
        return self.name


class BankAccount(models.Model):
    """Tài khoản ngân hàng"""
    payment_method = models.ForeignKey(PaymentMethod, on_delete=models.CASCADE, related_name='bank_accounts', verbose_name="Phương thức thanh toán")
    bank_name = models.CharField(max_length=100, verbose_name="Tên ngân hàng")
    account_holder = models.CharField(max_length=100, verbose_name="Chủ tài khoản")
    account_number = models.CharField(max_length=50, verbose_name="Số tài khoản")
    branch = models.CharField(max_length=100, blank=True, verbose_name="Chi nhánh")
    qr_code = models.ImageField(upload_to='shop/qr_codes/', blank=True, null=True, verbose_name="QR Code")
    is_active = models.BooleanField(default=True, verbose_name="Kích hoạt")
    order = models.PositiveIntegerField(default=0, verbose_name="Thứ tự")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Tài khoản ngân hàng"
        verbose_name_plural = "Tài khoản ngân hàng"
        ordering = ['order', 'bank_name']
    
    def __str__(self):
        return f"{self.bank_name} - {self.account_number}"


class EWalletAccount(models.Model):
    """Tài khoản ví điện tử"""
    payment_method = models.ForeignKey(PaymentMethod, on_delete=models.CASCADE, related_name='ewallet_accounts', verbose_name="Phương thức thanh toán")
    wallet_name = models.CharField(max_length=100, verbose_name="Tên ví")
    account_info = models.CharField(max_length=200, verbose_name="Thông tin tài khoản")
    qr_code = models.ImageField(upload_to='shop/qr_codes/', blank=True, null=True, verbose_name="QR Code")
    is_active = models.BooleanField(default=True, verbose_name="Kích hoạt")
    order = models.PositiveIntegerField(default=0, verbose_name="Thứ tự")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Tài khoản ví điện tử"
        verbose_name_plural = "Tài khoản ví điện tử"
        ordering = ['order', 'wallet_name']
    
    def __str__(self):
        return f"{self.wallet_name} - {self.account_info}"


class PaymentStep(models.Model):
    """Bước trong quy trình thanh toán"""
    title = models.CharField(max_length=200, verbose_name="Tiêu đề")
    description = models.TextField(verbose_name="Mô tả")
    order = models.PositiveIntegerField(default=0, verbose_name="Thứ tự")
    is_active = models.BooleanField(default=True, verbose_name="Kích hoạt")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Bước thanh toán"
        verbose_name_plural = "Bước thanh toán"
        ordering = ['order']
    
    def __str__(self):
        return f"{self.order}. {self.title}"


class ContactInfo(models.Model):
    """Thông tin liên hệ hỗ trợ"""
    CONTACT_TYPE_CHOICES = [
        ('phone', 'Điện thoại'),
        ('email', 'Email'),
        ('messenger', 'Facebook Messenger'),
        ('zalo', 'Zalo'),
        ('other', 'Khác'),
    ]
    
    contact_type = models.CharField(max_length=20, choices=CONTACT_TYPE_CHOICES, verbose_name="Loại liên hệ")
    name = models.CharField(max_length=100, verbose_name="Tên")
    value = models.CharField(max_length=200, verbose_name="Giá trị")
    description = models.CharField(max_length=200, blank=True, verbose_name="Mô tả")
    icon = models.CharField(max_length=50, default='fas fa-phone', verbose_name="Icon")
    is_active = models.BooleanField(default=True, verbose_name="Kích hoạt")
    order = models.PositiveIntegerField(default=0, verbose_name="Thứ tự")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Thông tin liên hệ"
        verbose_name_plural = "Thông tin liên hệ"
        ordering = ['order', 'contact_type']
    
    def __str__(self):
        return f"{self.name} - {self.value}"


class PaymentPolicy(models.Model):
    """Chính sách thanh toán"""
    POLICY_TYPE_CHOICES = [
        ('warning', 'Lưu ý quan trọng'),
        ('success', 'Chính sách đổi trả'),
        ('info', 'Thông tin khác'),
    ]
    
    title = models.CharField(max_length=200, verbose_name="Tiêu đề")
    content = models.TextField(verbose_name="Nội dung")
    policy_type = models.CharField(max_length=20, choices=POLICY_TYPE_CHOICES, verbose_name="Loại chính sách")
    icon = models.CharField(max_length=50, default='fas fa-info-circle', verbose_name="Icon")
    is_active = models.BooleanField(default=True, verbose_name="Kích hoạt")
    order = models.PositiveIntegerField(default=0, verbose_name="Thứ tự")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Chính sách thanh toán"
        verbose_name_plural = "Chính sách thanh toán"
        ordering = ['order', 'policy_type']
    
    def __str__(self):
        return self.title


class CustomerShippingInfo(models.Model):
    """Thông tin giao hàng của khách (lưu để dùng lại)"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='shipping_info', verbose_name="Người dùng")
    
    # Thông tin mặc định
    full_name = models.CharField(max_length=100, verbose_name="Họ và tên")
    phone = models.CharField(max_length=20, verbose_name="Số điện thoại")
    address = models.TextField(verbose_name="Địa chỉ chi tiết")
    city = models.CharField(max_length=100, verbose_name="Tỉnh/Thành phố")
    district = models.CharField(max_length=100, verbose_name="Quận/Huyện")
    
    # Metadata
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Cập nhật lần cuối")
    
    class Meta:
        verbose_name = "Thông tin giao hàng"
        verbose_name_plural = "Thông tin giao hàng"
    
    def __str__(self):
        return f"Thông tin giao hàng của {self.user.username}"


class ContactSettings(models.Model):
    """Cài đặt thông tin liên hệ"""
    phone_number = models.CharField(max_length=20, verbose_name="Số điện thoại", help_text="Ví dụ: 0123456789")
    zalo_link = models.CharField(max_length=200, verbose_name="Link Zalo", help_text="Ví dụ: https://zalo.me/0123456789")
    messenger_link = models.CharField(max_length=200, verbose_name="Link Messenger", help_text="Ví dụ: https://m.me/dbpsports")
    is_active = models.BooleanField(default=True, verbose_name="Kích hoạt popup liên hệ")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Ngày tạo")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Ngày cập nhật")

    class Meta:
        verbose_name = "Cài đặt liên hệ"
        verbose_name_plural = "Cài đặt liên hệ"

    def __str__(self):
        return f"Cài đặt liên hệ - {self.phone_number}"

    def save(self, *args, **kwargs):
        # Chỉ cho phép 1 record duy nhất
        if not self.pk and ContactSettings.objects.exists():
            # Nếu đã có record, cập nhật record đó thay vì tạo mới
            existing = ContactSettings.objects.first()
            existing.phone_number = self.phone_number
            existing.zalo_link = self.zalo_link
            existing.messenger_link = self.messenger_link
            existing.is_active = self.is_active
            return existing.save(*args, **kwargs)
        return super().save(*args, **kwargs)