# bikeshop/urls.py
from django.contrib import admin
from django.urls import path, include
from django.http import HttpResponse
from django.conf import settings
from django.conf.urls.static import static
from django.views.static import serve as media_serve

def healthz(_): return HttpResponse("ok")

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include(("shop.urls", "shop"), namespace="shop")),
    path("healthz", healthz),

    # Serve user-uploaded files from the persistent disk, even with DEBUG=False
    path("media/<path:path>", media_serve, {"document_root": settings.MEDIA_ROOT}),
]

# (Keeping this as well is harmless; but the explicit route above guarantees it.)
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
