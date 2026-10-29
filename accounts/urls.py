from django.urls import path
from . import views

urlpatterns = [
path("register/", views.register, name="register"),
path("login/", views.user_login, name="login"),
path("logout/", views.user_logout, name="logout"),
path("seller/dashboard/", views.seller_dashboard, name="seller_dashboard"),
]
