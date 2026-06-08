from django.urls import path
from . import views

urlpatterns = [
    path("status/", views.status, name="status"),
    path("schema/", views.schema, name="schema"),
    path("organizations/", views.organizations, name="organizations"),
    path("members/", views.members, name="members"),
    path("members/<str:local_id>/", views.member_detail, name="member_detail"),
    path("activities/", views.activities, name="activities"),
    path("metrics/", views.metrics, name="metrics"),
    path("consents/", views.consents, name="consents"),
]
