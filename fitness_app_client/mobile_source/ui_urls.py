from django.urls import path

from . import views

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("documents/", views.documents_page, name="documents_page"),
    path("profiles/", views.profiles_page, name="profiles_page"),
    path("activities/", views.activities_page, name="activities_page"),
    path("metrics/", views.metrics_page, name="metrics_page"),
    path("consents/", views.consents_page, name="consents_page"),
]
