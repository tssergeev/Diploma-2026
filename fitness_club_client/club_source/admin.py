from django.contrib import admin
from .models import Activity, Consent, HealthMetric, Member, Organization


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "organization_type", "city")
    search_fields = ("name", "city")


@admin.register(Member)
class MemberAdmin(admin.ModelAdmin):
    list_display = ("id", "local_id", "full_name", "gender", "birth_date", "city", "training_level")
    list_filter = ("gender", "city", "training_level")
    search_fields = ("local_id", "full_name", "email", "phone")


@admin.register(Activity)
class ActivityAdmin(admin.ModelAdmin):
    list_display = ("id", "activity_id", "member", "activity_date", "activity_type", "duration_minutes", "intensity")
    list_filter = ("activity_type", "intensity", "activity_date")
    search_fields = ("activity_id", "member__full_name")


@admin.register(HealthMetric)
class HealthMetricAdmin(admin.ModelAdmin):
    list_display = ("id", "metric_id", "member", "metric_type", "metric_value", "unit", "measured_at")
    list_filter = ("metric_type", "unit")
    search_fields = ("metric_id", "member__full_name")


@admin.register(Consent)
class ConsentAdmin(admin.ModelAdmin):
    list_display = ("id", "member", "open_to_offers", "status", "granted_at", "expires_at")
    list_filter = ("open_to_offers", "status")
    search_fields = ("member__full_name",)
