from django.contrib import admin

from .models import Product, Category, CartItem

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
