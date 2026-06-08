from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("mobile_source.urls")),
    path("", include("mobile_source.ui_urls")),
]
