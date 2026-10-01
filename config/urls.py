from django.contrib import admin
from django.urls import include, path

from api.api import api

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", api.urls),  # Swagger UI: /api/docs
    path("accounts/", include("django.contrib.auth.urls")),  # /accounts/login/, /accounts/logout/
    path("", include("web.urls")),
]
