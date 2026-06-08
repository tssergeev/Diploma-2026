from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("mediator.urls")),
    path("", include("mediator.ui_urls")),
]
