from django.urls import path

from . import ui_views

urlpatterns = [
    path("", ui_views.dashboard, name="dashboard"),
    path("sync/", ui_views.sync_all_view, name="ui_sync_all"),
    path("sources/<str:source_id>/sync/", ui_views.sync_source_view, name="ui_sync_source"),
    path("clients/", ui_views.clients_stats, name="clients_stats"),
    path("clients/<str:source_id>/", ui_views.client_detail, name="client_detail"),
    path("people/", ui_views.people_stats, name="people_stats"),
    path("people/<uuid:global_id>/", ui_views.person_detail, name="person_detail"),
]
