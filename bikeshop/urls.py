# bikeshop/urls.py
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.static import serve as static_serve

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include(("shop.urls", "shop"), namespace="shop")),
]

# In small projects it's fine to let Django serve media (uploads) directly.
# This works both in DEBUG and on Render (gunicorn) for demo-scale traffic.
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# (Static files are handled by WhiteNoise via STATIC_ROOT.)
