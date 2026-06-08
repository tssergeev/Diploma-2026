from django.urls import path

from . import views

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("organizations/", views.organizations_page, name="organizations_page"),
    path("members/", views.members_page, name="members_page"),
    path("activities/", views.activities_page, name="activities_page"),
    path("metrics/", views.metrics_page, name="metrics_page"),
    path("consents/", views.consents_page, name="consents_page"),
]
