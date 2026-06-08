from django.contrib import admin

from .models import (
    ActivityRecord,
    AuditLog,
    ConsentRecord,
    DataSource,
    GlobalUserProfile,
    HealthMetricRecord,
    Offer,
    SourceUserLink,
)


@admin.register(DataSource)
class DataSourceAdmin(admin.ModelAdmin):
    list_display = ("name", "source_id", "source_type", "base_url", "is_active", "last_sync_at")
    list_filter = ("source_type", "is_active")
    search_fields = ("name", "source_id", "base_url")


class SourceUserLinkInline(admin.TabularInline):
    model = SourceUserLink
    extra = 0
    readonly_fields = ("source", "local_user_id", "fingerprint", "created_at", "updated_at")
    can_delete = False


class ActivityInline(admin.TabularInline):
    model = ActivityRecord
    extra = 0
    readonly_fields = ("source", "activity_date", "activity_type", "duration_minutes", "intensity")
    can_delete = False


class HealthMetricInline(admin.TabularInline):
    model = HealthMetricRecord
    extra = 0
    readonly_fields = ("source", "metric_type", "metric_value", "unit", "measured_at")
    can_delete = False


@admin.register(GlobalUserProfile)
class GlobalUserProfileAdmin(admin.ModelAdmin):
    list_display = ("full_name", "age", "gender", "city", "sport_type", "training_level", "open_to_offers", "consent_status")
    list_filter = ("gender", "city", "sport_type", "training_level", "open_to_offers", "consent_status")
    search_fields = ("full_name", "phone", "email", "city")
    inlines = (SourceUserLinkInline, ActivityInline, HealthMetricInline)


@admin.register(SourceUserLink)
class SourceUserLinkAdmin(admin.ModelAdmin):
    list_display = ("source", "local_user_id", "profile", "updated_at")
    list_filter = ("source",)
    search_fields = ("local_user_id", "profile__full_name")


@admin.register(ActivityRecord)
class ActivityRecordAdmin(admin.ModelAdmin):
    list_display = ("profile", "source", "activity_date", "activity_type", "duration_minutes", "intensity")
    list_filter = ("source", "activity_type", "intensity")
    search_fields = ("profile__full_name", "activity_type")


@admin.register(HealthMetricRecord)
class HealthMetricRecordAdmin(admin.ModelAdmin):
    list_display = ("profile", "source", "metric_type", "metric_value", "unit", "measured_at")
    list_filter = ("source", "metric_type", "unit")
    search_fields = ("profile__full_name", "metric_type")


@admin.register(ConsentRecord)
class ConsentRecordAdmin(admin.ModelAdmin):
    list_display = ("profile", "source", "open_to_offers", "status", "granted_at", "expires_at")
    list_filter = ("source", "open_to_offers", "status")
    search_fields = ("profile__full_name",)


@admin.register(Offer)
class OfferAdmin(admin.ModelAdmin):
    list_display = ("profile", "trainer_name", "organization_name", "status", "created_at")
    list_filter = ("status",)
    search_fields = ("profile__full_name", "trainer_name", "organization_name")


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ("created_at", "action", "source", "profile")
    list_filter = ("action", "source")
    search_fields = ("action", "profile__full_name")
