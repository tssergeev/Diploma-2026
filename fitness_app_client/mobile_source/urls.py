from django.urls import path

from . import views

urlpatterns = [
    path("status/", views.status, name="status"),
    path("schema/", views.schema, name="schema"),
    path("documents/", views.documents, name="documents"),
    path("documents/<str:local_id>/", views.document_detail, name="document_detail"),
    path("users/", views.users, name="users"),
    path("users/<str:local_id>/", views.user_detail, name="user_detail"),
    path("activities/", views.activities, name="activities"),
    path("metrics/", views.metrics, name="metrics"),
    path("consents/", views.consents, name="consents"),
]
