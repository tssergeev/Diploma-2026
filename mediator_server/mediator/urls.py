from django.urls import path

from . import views

urlpatterns = [
    path("status/", views.status, name="status"),
    path("sources/", views.sources, name="sources"),
    path("sources/check/", views.source_check, name="source_check"),
    path("sources/<str:source_id>/", views.source_detail, name="source_detail"),
    path("sync/", views.sync, name="sync"),
    path("users/", views.users, name="users"),
    path("users/<uuid:global_id>/", views.user_detail, name="user_detail"),
    path("search/users/", views.users, name="search_users"),
    path("offers/", views.offers, name="offers"),
    path("audit/", views.audit, name="audit"),
]
