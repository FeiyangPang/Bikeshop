# shop/urls.py
from django.urls import path
from . import views

app_name = 'shop'

urlpatterns = [
    path('', views.product_list, name='product_list'),

    # Cart
    path('cart/', views.view_cart, name='view_cart'),
    path('cart/add/<int:product_id>/', views.add_item, name='add_item'),
    path('cart/remove/<int:product_id>/', views.remove_item, name='remove_item'),
    path('cart/update/<int:product_id>/', views.update_qty, name='update_qty'),

    # Checkout
    path('checkout/', views.checkout_view, name='checkout'),
    path('success/', views.success_view, name='success'),

    # Auth
    path('signup/', views.signup_view, name='signup'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    # Drag & Drop Uploader
    path('uploader/', views.uploader_view, name='uploader'),
    path('uploader/api/create/', views.uploader_api_create, name='uploader_api_create'),
    path('uploader/api/delete/<int:pk>/', views.uploader_api_delete, name='uploader_api_delete'),  # NEW
]
