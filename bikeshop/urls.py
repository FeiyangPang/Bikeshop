from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include(("shop.urls", "shop"), namespace="shop")),
]

# Let Django serve user uploads (ok for small deployments)
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
