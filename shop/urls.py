# shop/urls.py
from django.urls import path
from . import views

app_name = 'shop'

urlpatterns = [

    path("", views.product_list, name="product_list"),  # your existing list view
    path("cart/", views.cart_view, name="cart"),
    path("cart/update/", views.cart_update_api, name="cart_update_api"),
    path("cart/remove/<int:product_id>/", views.cart_remove, name="cart_remove"),
    path("checkout/", views.checkout_view, name="checkout"),
    path("success/", views.success_view, name="success"),

    # Auth
    path('signup/', views.signup_view, name='signup'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    # Drag & Drop Uploader
    path('uploader/', views.uploader_view, name='uploader'),
    path('uploader/api/create/', views.uploader_api_create, name='uploader_api_create'),
    path('uploader/api/delete/<int:pk>/', views.uploader_api_delete, name='uploader_api_delete'),  # NEW
]
