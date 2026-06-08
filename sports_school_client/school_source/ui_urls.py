from django.urls import path

from . import views

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("schools/", views.schools_page, name="schools_page"),
    path("sections/", views.sections_page, name="sections_page"),
    path("students/", views.students_page, name="students_page"),
    path("attendance/", views.attendance_page, name="attendance_page"),
    path("fitness-tests/", views.fitness_tests_page, name="fitness_tests_page"),
    path("permissions/", views.permissions_page, name="permissions_page"),
]
