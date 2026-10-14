"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.1/topics/http/urls/
"""

from django.contrib import admin
from django.urls import include, path, re_path
from users.views import login_view
from django.conf import settings
from django.conf.urls.static import static
from django.views.static import serve


urlpatterns = [
    path("", login_view, name="home"),

    path("users/", include("users.urls")),
    path("admin/", admin.site.urls),

    path("purchases/", include("purchase.urls")),
    path("sales/", include("sales.urls")),
    path("inventory/", include("inventory.urls")),
    path("expenses/", include("expenses.urls")),
    path("credit/", include("credit.urls")),
    path("reports/", include("reports.urls")),
    path("proforma/", include("proforma.urls")),
    path("orders/", include("orders.urls")),

    # Product photos are public (shown in the catalogue), so they are
    # served in production too. Payment proofs are deliberately NOT
    # served from /media/ - they are private and are only available
    # through the login-protected orders "payment_proof_file" view.
    re_path(
        r"^media/(?P<path>products/.*)$",
        serve,
        {"document_root": settings.MEDIA_ROOT},
    ),
]


# Serve all uploaded media files during development
if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT
    )