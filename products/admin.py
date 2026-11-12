from django.contrib import admin

from .models import (
    Product,
    Category,
    CartItem,
    Order,
    OrderItem,
    OrderStatusHistory,
    Notification,
    OrderDeliveryHistory,
)
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "price", "quantity")
    search_fields = ("name",)
    list_filter = ("category",)

@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ("product", "quantity", "session_key", "updated_at")
    search_fields = ("product__name", "session_key")
    list_filter = ("updated_at",)
    readonly_fields = ("updated_at",)

class OrderStatusHistoryInline(admin.TabularInline):
    model = OrderStatusHistory
    extra = 0
    can_delete = False

    readonly_fields = (
        "old_status",
        "new_status",
        "changed_by",
        "changed_at",
    )

    def has_add_permission(self, request, obj=None):
        return False

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):

    inlines = [OrderStatusHistoryInline]
    list_display = (
        "order_number",
        "buyer",
        "customer_name",
        "total_amount",
        "status",
        "created_at",
    )

    search_fields = (
        "customer_name",
        "phone",
        "order_number",
    )

    list_filter = ("status", "created_at")

    readonly_fields = ("order_number", "created_at")

    fields = (
        "order_number",
        "buyer",
        "customer_name",
        "phone",
        "address",
        "total_amount",
        "status",
        "created_at",
    )

    def save_model(self, request, obj, form, change):

        old_status = None

        if change:
            old_order = Order.objects.get(pk=obj.pk)
            old_status = old_order.status

        super().save_model(request, obj, form, change)

        if change and old_status != obj.status:
            OrderStatusHistory.objects.create(
                order=obj,
                old_status=old_status,
                new_status=obj.status,
                changed_by=request.user.username,
            )

            Notification.objects.create(
                recipient=obj.buyer,
                order=obj,
                title="تغییر وضعیت سفارش",
                message=(
                    f"وضعیت سفارش شما از "
                    f"«{dict(Order.STATUS_CHOICES)[old_status]}» "
                    f"به «{obj.get_status_display()}» تغییر کرد."
                ),
            )

@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = (
        "order",
        "product_name",
        "unit_price",
        "quantity",
    )
    search_fields = ("product_name",)

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "recipient",
        "order",
        "is_read",
        "created_at",
    )

    list_filter = ("is_read", "created_at")

    search_fields = (
        "title",
        "message",
        "recipient__user__username",
    )

    list_editable = ("is_read",)

@admin.register(OrderDeliveryHistory)
class OrderDeliveryHistoryAdmin(admin.ModelAdmin):

    list_display = (
        "order",
        "old_customer_name",
        "new_customer_name",
        "changed_by",
        "changed_at",
    )

    search_fields = (
        "order__order_number",
        "old_customer_name",
        "new_customer_name",
        "changed_by",
    )

    list_filter = ("changed_at",)

    readonly_fields = (
        "order",
        "old_customer_name",
        "new_customer_name",
        "old_phone",
        "new_phone",
        "old_address",
        "new_address",
        "changed_by",
        "changed_at",
    )    

    