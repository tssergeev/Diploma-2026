from django.urls import path

from . import views

urlpatterns = [
    path("status/", views.status, name="status"),
    path("schema/", views.schema, name="schema"),
    path("schools/", views.schools, name="schools"),
    path("sections/", views.sections, name="sections"),
    path("students/", views.students, name="students"),
    path("students/<str:local_code>/", views.student_detail, name="student_detail"),
    path("attendance/", views.attendance, name="attendance"),
    path("fitness-tests/", views.fitness_tests, name="fitness_tests"),
    path("metrics/", views.metrics, name="metrics"),
    path("permissions/", views.permissions, name="permissions"),
    path("export/global/", views.global_export, name="global_export"),
]
