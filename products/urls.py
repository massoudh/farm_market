from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("products/<int:product_id>/", views.product_detail, name="product_detail"),
    path("cart/", views.cart_view, name="cart"),
    path("checkout/", views.checkout, name="checkout"),
    path("my-orders/", views.my_orders, name="my_orders"),

    path(
        "my-notifications/",
        views.my_notifications,
        name="my_notifications"
    ),

    
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
    
    path(
        "seller/products/<int:product_id>/delete/",
        views.delete_product,
        name="delete_product"
    ),
    
    path(
        "orders/<uuid:order_number>/",
        views.order_detail,
        name="order_detail"
    ),    

    path(
        "orders/<uuid:order_number>/edit-delivery/",
        views.edit_order_delivery,
        name="edit_order_delivery"
    ),

    path(
        "seller-orders/",
        views.seller_orders,
        name="seller_orders"
    ),

    path(
        "seller-orders/update-item/<int:item_id>/",
        views.update_seller_order_item_status,
        name="update_seller_order_item_status"
    ),

    path(
        "my-notifications/<int:notification_id>/read/",
        views.mark_notification_read,
        name="mark_notification_read"
    ),


]
