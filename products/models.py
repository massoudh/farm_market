from django.db import models
import uuid
from django.core.validators import MinValueValidator


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name


class Product(models.Model):

    
    seller = models.ForeignKey(
        "accounts.UserProfile",
        on_delete=models.PROTECT,
        related_name="products",
        verbose_name="فروشنده"
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name="products"

    )
    name = models.CharField(max_length=100)
    price = models.DecimalField(
        max_digits=12,
        decimal_places=0,
        validators=[MinValueValidator(1)],
        verbose_name="قیمت"
    )
    quantity = models.PositiveIntegerField(default=0)
    description = models.TextField(blank=True)
    image = models.ImageField(
        upload_to="products/",
        blank=True,
        null=True,
        verbose_name="تصویر محصول"
        )

    def __str__(self):
        return self.name

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=models.Q(price__gte=1),
                name="product_price_gte_1"
            )
        ]


class CartItem(models.Model):

    session_key = models.CharField(
        max_length=40,
        db_index=True,
        verbose_name="شناسه نشست مشتری"
    )

    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        related_name="cart_items",
        verbose_name="محصول"
    )

    quantity = models.PositiveIntegerField(
        default=1,
        validators=[MinValueValidator(1)],
        verbose_name="تعداد"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="آخرین به‌روزرسانی"
    )

class Meta:
    verbose_name = "قلم سبد خرید"
    verbose_name_plural = "اقلام سبد خرید"

    constraints = [
        models.UniqueConstraint(
            fields=["session_key", "product"],
            name="unique_cart_session_product"
        ),
        models.CheckConstraint(
            condition=models.Q(quantity__gte=1),
            name="cart_item_quantity_gte_1"
        )
    ]

    def __str__(self):
        return f"{self.product.name} - تعداد: {self.quantity}"

class Order(models.Model):

    STATUS_CHOICES = [
        ("pending", "در انتظار بررسی"),
        ("confirmed", "تأیید شده"),
        ("processing", "در حال آماده‌سازی"),
        ("shipped", "ارسال شده"),
        ("delivered", "تحویل داده شده"),
        ("cancelled", "لغو شده"),
    ]

    order_number = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False,
        verbose_name="شماره سفارش"
    )

    buyer = models.ForeignKey(
        "accounts.UserProfile",
        on_delete=models.PROTECT,
        related_name="orders",
        verbose_name="خریدار"
    )

    customer_name = models.CharField(
        max_length=200,
        verbose_name="نام تحویل‌گیرنده"
    )

    phone = models.CharField(
        max_length=20,
        verbose_name="شماره تماس"
    )

    address = models.TextField(
        verbose_name="نشانی تحویل"
    )

    total_amount = models.DecimalField(
        max_digits=15,
        decimal_places=0,
        default=0,
        verbose_name="مبلغ کل سفارش"
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="pending",
        verbose_name="وضعیت سفارش"
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="تاریخ ثبت سفارش"
    )

class Meta:
    verbose_name = "سفارش"
    verbose_name_plural = "سفارش‌ها"

    constraints = [
        models.CheckConstraint(
            condition=models.Q(
                status__in=[
                    "pending",
                    "confirmed",
                    "processing",
                    "shipped",
                    "delivered",
                    "cancelled",
                ]
            ),
            name="order_status_valid"
        )
    ]
    
    def __str__(self):
        return str(self.order_number)

class OrderStatusHistory(models.Model):

    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="status_history",
        verbose_name="سفارش"
    )

    old_status = models.CharField(
        max_length=20,
        choices=Order.STATUS_CHOICES,
        verbose_name="وضعیت قبلی"
    )

    new_status = models.CharField(
        max_length=20,
        choices=Order.STATUS_CHOICES,
        verbose_name="وضعیت جدید"
    )

    changed_by = models.CharField(
        max_length=200,
        default="system",
        verbose_name="تغییردهنده"
    )

    changed_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="زمان تغییر"
    )

    class Meta:
        verbose_name = "تاریخچه وضعیت سفارش"
        verbose_name_plural = "تاریخچه وضعیت سفارش‌ها"
        ordering = ["-changed_at"]

    def __str__(self):
        return (
            f"{self.order.order_number} - "
            f"{self.get_old_status_display()} به "
            f"{self.get_new_status_display()}"
        )

class Notification(models.Model):

    recipient = models.ForeignKey(
        "accounts.UserProfile",
        on_delete=models.CASCADE,
        related_name="notifications",
        verbose_name="دریافت‌کننده"
    )

    order = models.ForeignKey(
        Order,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="notifications",
        verbose_name="سفارش مرتبط"
    )

    title = models.CharField(
        max_length=200,
        verbose_name="عنوان اعلان"
    )

    message = models.TextField(
        verbose_name="متن اعلان"
    )

    is_read = models.BooleanField(
        default=False,
        verbose_name="خوانده شده"
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="تاریخ ایجاد"
    )

    class Meta:
        verbose_name = "اعلان"
        verbose_name_plural = "اعلان‌ها"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.title} - {self.recipient.user.username}"

class OrderDeliveryHistory(models.Model):

    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="delivery_history",
        verbose_name="سفارش"
    )

    old_customer_name = models.CharField(
        max_length=200,
        verbose_name="نام قبلی"
    )

    new_customer_name = models.CharField(
        max_length=200,
        verbose_name="نام جدید"
    )

    old_phone = models.CharField(
        max_length=20,
        verbose_name="شماره تلفن قبلی"
    )

    new_phone = models.CharField(
        max_length=20,
        verbose_name="شماره تلفن جدید"
    )

    old_address = models.TextField(
        verbose_name="نشانی قبلی"
    )

    new_address = models.TextField(
        verbose_name="نشانی جدید"
    )

    changed_by = models.CharField(
        max_length=200,
        verbose_name="ویرایش‌کننده"
    )

    changed_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="زمان ویرایش"
    )

    class Meta:
        verbose_name = "تاریخچه اطلاعات تحویل"
        verbose_name_plural = "تاریخچه اطلاعات تحویل"

        ordering = ["-changed_at"]

    def __str__(self):
        return f"تاریخچه تحویل سفارش {self.order.order_number}"

class OrderItem(models.Model):

    ITEM_STATUS_CHOICES = [
        ("pending", "در انتظار آماده‌سازی"),
        ("preparing", "در حال آماده‌سازی"),
        ("ready", "آماده ارسال"),
        ("shipped", "ارسال شده"),
    ]
        
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="items",
        verbose_name="سفارش"
    )

    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        verbose_name="محصول"
    )

    product_name = models.CharField(
        max_length=100,
        verbose_name="نام محصول در زمان سفارش"
    )

    unit_price = models.DecimalField(
        max_digits=12,
        decimal_places=0,
        validators=[MinValueValidator(1)],
        verbose_name="قیمت واحد در زمان سفارش"
    )
    quantity = models.PositiveIntegerField(
        validators=[MinValueValidator(1)],
        verbose_name="تعداد"
    )
    status = models.CharField(
        max_length=20,
        choices=ITEM_STATUS_CHOICES,
        default="pending",
        verbose_name="وضعیت آماده‌سازی و ارسال"
    )

class Meta:
    verbose_name = "قلم سفارش"
    verbose_name_plural = "اقلام سفارش"

    constraints = [
        models.CheckConstraint(
            condition=models.Q(quantity__gte=1),
            name="order_item_quantity_gte_1"
        ),
        models.CheckConstraint(
            condition=models.Q(unit_price__gte=1),
            name="order_item_unit_price_gte_1"
        ),
        models.CheckConstraint(
            condition=models.Q(
                status__in=[
                    "pending",
                    "preparing",
                    "ready",
                    "shipped",
                ]
            ),
            name="order_item_status_valid"
        )
    ]

    def __str__(self):
        return f"{self.product_name} - {self.quantity}"

    @property
    def subtotal(self):
        return self.unit_price * self.quantity
    

    