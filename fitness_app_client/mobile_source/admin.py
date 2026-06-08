from django.contrib import admin

from .models import FitnessDocument


@admin.register(FitnessDocument)
class FitnessDocumentAdmin(admin.ModelAdmin):
    list_display = ("local_id", "full_name", "updated_at")
    search_fields = ("local_id", "document")
    readonly_fields = ("created_at", "updated_at")

    def full_name(self, obj):
        return obj.document.get("profile", {}).get("fullName", "")

    full_name.short_description = "ФИО"
