from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("products/<int:product_id>/", views.product_detail, name="product_detail"),
    path("cart/", views.cart_view, name="cart"),
    path(
        "cart/add/<int:product_id>/",
        views.add_to_cart,
        name="add_to_cart"
    ),
    path(
        "cart/remove/<int:product_id>/",
        views.remove_from_cart,
        name="remove_from_cart"
    ),
    path(
        "cart/update/<int:product_id>/",
        views.update_cart,
        name="update_cart"
    ),
    path(
        "seller/products/add/", 
        views.add_product, 
        name="add_product"),
    path(
        "seller/products/",
        views.my_products,
        name="my_products"
    ),

    path(
        "seller/products/<int:product_id>/edit/",
        views.edit_product,
        name="edit_product"
    ),

]
