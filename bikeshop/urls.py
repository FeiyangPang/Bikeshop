# bikeshop/urls.py
from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.views.static import serve as media_serve

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include(("shop.urls", "shop"), namespace="shop")),
]

# Serve uploaded files from MEDIA_ROOT at /media/ even when DEBUG=False
urlpatterns += [
    re_path(r"^media/(?P<path>.*)$", media_serve, {
        "document_root": settings.MEDIA_ROOT,
        "show_indexes": False,
    }),
]
