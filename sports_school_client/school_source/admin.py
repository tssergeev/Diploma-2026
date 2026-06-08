from django.contrib import admin

from .models import AttendanceRecord, DisclosurePermission, FitnessTest, School, Section, Student


@admin.register(School)
class SchoolAdmin(admin.ModelAdmin):
    list_display = ("name", "organization_type", "city")
    search_fields = ("name", "city")


@admin.register(Section)
class SectionAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "sport_type", "coach_name", "school")
    list_filter = ("sport_type", "school")
    search_fields = ("code", "name", "coach_name")


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ("local_code", "full_name", "birth_year", "gender_code", "section", "skill_level")
    list_filter = ("gender_code", "skill_level", "section")
    search_fields = ("local_code", "full_name", "parent_phone")


@admin.register(AttendanceRecord)
class AttendanceRecordAdmin(admin.ModelAdmin):
    list_display = ("record_code", "student", "training_date", "present", "training_type", "load_level")
    list_filter = ("present", "training_type", "load_level")
    search_fields = ("record_code", "student__full_name")


@admin.register(FitnessTest)
class FitnessTestAdmin(admin.ModelAdmin):
    list_display = ("test_code", "student", "tested_at", "resting_pulse", "weight_kg", "endurance_score")
    search_fields = ("test_code", "student__full_name")


@admin.register(DisclosurePermission)
class DisclosurePermissionAdmin(admin.ModelAdmin):
    list_display = ("student", "can_be_found", "status", "granted_on", "valid_until")
    list_filter = ("can_be_found", "status")
