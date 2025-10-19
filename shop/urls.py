from django.urls import path
from . import views

app_name = "shop"

urlpatterns = [
    # Your product list view must exist in views.py
    path("", views.product_list, name="product_list"),

    path("cart/", views.cart_view, name="cart"),
    path("cart/update/", views.cart_update_api, name="cart_update_api"),
    path("cart/remove/<int:product_id>/", views.cart_remove, name="cart_remove"),

    path("checkout/", views.checkout_view, name="checkout"),
    path("success/", views.success_view, name="success"),
]
