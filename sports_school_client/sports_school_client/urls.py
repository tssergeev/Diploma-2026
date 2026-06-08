from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("school_source.urls")),
    path("", include("school_source.ui_urls")),
]
