# bikeshop/urls.py
from django.contrib import admin
from django.urls import path, include
from django.http import HttpResponse
from django.conf import settings
from django.conf.urls.static import static

def healthz(_request):
    return HttpResponse("ok")

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include(("shop.urls", "shop"), namespace="shop")),
    path("healthz", healthz),   # Render health check
]

# Serve uploaded media (fine for small sites behind gunicorn)
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
