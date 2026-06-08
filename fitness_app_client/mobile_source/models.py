from django.db import models


class FitnessDocument(models.Model):
    local_id = models.CharField("Локальный ID пользователя", max_length=64, unique=True)
    document = models.JSONField("JSON-документ пользователя", default=dict)
    created_at = models.DateTimeField("Дата создания", auto_now_add=True)
    updated_at = models.DateTimeField("Дата обновления", auto_now=True)

    class Meta:
        verbose_name = "JSON-документ фитнес-приложения"
        verbose_name_plural = "JSON-документы фитнес-приложения"
        ordering = ["local_id"]

    def __str__(self):
        profile = self.document.get("profile", {}) if isinstance(self.document, dict) else {}
        full_name = profile.get("fullName") or self.local_id
        return f"{self.local_id}: {full_name}"
