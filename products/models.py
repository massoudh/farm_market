from django.db import models

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
        blank=True,
        null=True,
        verbose_name="فروشنده"
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name="products"

    )
    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=12, decimal_places=0)
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
            )
        ]

    def __str__(self):
        return f"{self.product.name} - تعداد: {self.quantity}"
    