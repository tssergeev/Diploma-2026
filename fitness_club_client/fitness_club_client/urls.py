from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("club_source.ui_urls")),
    path("api/", include("club_source.urls")),
]
