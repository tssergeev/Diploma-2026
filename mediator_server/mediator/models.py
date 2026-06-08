import uuid

from django.db import models


class DataSource(models.Model):
    SOURCE_TYPES = [
        ("fitness_club", "Фитнес-клуб"),
        ("sports_school", "Спортивная школа"),
        ("fitness_app", "Фитнес-приложение"),
        ("generic_rest", "Универсальный REST-источник"),
    ]

    source_id = models.CharField("Код источника", max_length=120, unique=True)
    name = models.CharField("Название", max_length=255)
    source_type = models.CharField("Тип источника", max_length=40, choices=SOURCE_TYPES)
    base_url = models.URLField("Базовый URL")
    status_endpoint = models.CharField("Эндпоинт статуса", max_length=255, default="status/")
    schema_endpoint = models.CharField("Эндпоинт схемы", max_length=255, default="schema/")
    users_endpoint = models.CharField("Эндпоинт пользователей", max_length=255)
    timeout_seconds = models.PositiveIntegerField("Таймаут, сек.", default=5)
    is_active = models.BooleanField("Активен", default=True)
    description = models.TextField("Описание", blank=True)
    mapping_config = models.JSONField("Правила mapping", default=dict, blank=True)
    last_sync_at = models.DateTimeField("Последняя синхронизация", null=True, blank=True)
    last_error = models.TextField("Последняя ошибка", blank=True)
    created_at = models.DateTimeField("Создан", auto_now_add=True)
    updated_at = models.DateTimeField("Обновлён", auto_now=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "Источник данных"
        verbose_name_plural = "Источники данных"

    def __str__(self):
        return f"{self.name} ({self.source_id})"


class GlobalUserProfile(models.Model):
    global_id = models.UUIDField("Глобальный идентификатор", primary_key=True, default=uuid.uuid4, editable=False)
    full_name = models.CharField("ФИО", max_length=255)
    birth_date = models.DateField("Дата рождения", null=True, blank=True)
    age = models.PositiveIntegerField("Возраст", null=True, blank=True)
    gender = models.CharField("Пол", max_length=20, blank=True)
    phone = models.CharField("Телефон", max_length=60, blank=True)
    email = models.EmailField("Email", blank=True)
    city = models.CharField("Город", max_length=120, blank=True)
    sport_type = models.CharField("Вид спорта", max_length=120, blank=True)
    training_level = models.CharField("Уровень подготовки", max_length=120, blank=True)
    organization_name = models.CharField("Организация", max_length=255, blank=True)
    organization_type = models.CharField("Тип организации", max_length=120, blank=True)
    organization_city = models.CharField("Город организации", max_length=120, blank=True)
    open_to_offers = models.BooleanField("Открыт к предложениям", default=False)
    consent_status = models.CharField("Статус согласия", max_length=40, blank=True)
    visible_data_categories = models.JSONField("Видимые категории данных", default=list, blank=True)
    allowed_organization_types = models.JSONField("Разрешённые типы организаций", default=list, blank=True)
    source_summary = models.JSONField("Сводка источников", default=list, blank=True)
    raw_snapshot = models.JSONField("Последний снимок нормализованных данных", default=dict, blank=True)
    created_at = models.DateTimeField("Создан", auto_now_add=True)
    updated_at = models.DateTimeField("Обновлён", auto_now=True)

    class Meta:
        ordering = ["full_name"]
        verbose_name = "Глобальный профиль"
        verbose_name_plural = "Глобальные профили"

    def __str__(self):
        return f"{self.full_name} — {self.global_id}"


class SourceUserLink(models.Model):
    source = models.ForeignKey(DataSource, on_delete=models.CASCADE, related_name="user_links")
    profile = models.ForeignKey(GlobalUserProfile, on_delete=models.CASCADE, related_name="source_links")
    local_user_id = models.CharField("Локальный ID пользователя", max_length=150)
    fingerprint = models.CharField("Отпечаток для дедупликации", max_length=255, blank=True)
    raw_data = models.JSONField("Сырые данные источника", default=dict, blank=True)
    created_at = models.DateTimeField("Создан", auto_now_add=True)
    updated_at = models.DateTimeField("Обновлён", auto_now=True)

    class Meta:
        unique_together = ("source", "local_user_id")
        ordering = ["source__name", "local_user_id"]
        verbose_name = "Связь с локальной записью"
        verbose_name_plural = "Связи с локальными записями"

    def __str__(self):
        return f"{self.source.source_id}:{self.local_user_id} -> {self.profile_id}"


class ActivityRecord(models.Model):
    profile = models.ForeignKey(GlobalUserProfile, on_delete=models.CASCADE, related_name="activities")
    source = models.ForeignKey(DataSource, on_delete=models.CASCADE, related_name="activities")
    local_activity_id = models.CharField("Локальный ID активности", max_length=150, blank=True)
    activity_date = models.DateField("Дата активности", null=True, blank=True)
    activity_type = models.CharField("Тип активности", max_length=120, blank=True)
    duration_minutes = models.PositiveIntegerField("Длительность, мин.", null=True, blank=True)
    intensity = models.CharField("Интенсивность", max_length=80, blank=True)
    calories = models.PositiveIntegerField("Калории", null=True, blank=True)
    raw_data = models.JSONField("Сырые данные", default=dict, blank=True)
    created_at = models.DateTimeField("Создано", auto_now_add=True)

    class Meta:
        ordering = ["-activity_date", "activity_type"]
        verbose_name = "Активность"
        verbose_name_plural = "Активности"

    def __str__(self):
        return f"{self.profile.full_name}: {self.activity_type} {self.activity_date}"


class HealthMetricRecord(models.Model):
    profile = models.ForeignKey(GlobalUserProfile, on_delete=models.CASCADE, related_name="health_metrics")
    source = models.ForeignKey(DataSource, on_delete=models.CASCADE, related_name="health_metrics")
    local_metric_id = models.CharField("Локальный ID показателя", max_length=180, blank=True)
    metric_type = models.CharField("Тип показателя", max_length=120)
    metric_value = models.FloatField("Значение", null=True, blank=True)
    unit = models.CharField("Единица измерения", max_length=50, blank=True)
    measured_at = models.DateTimeField("Дата измерения", null=True, blank=True)
    raw_data = models.JSONField("Сырые данные", default=dict, blank=True)
    created_at = models.DateTimeField("Создано", auto_now_add=True)

    class Meta:
        ordering = ["metric_type", "-measured_at"]
        verbose_name = "Показатель здоровья"
        verbose_name_plural = "Показатели здоровья"

    def __str__(self):
        return f"{self.profile.full_name}: {self.metric_type}={self.metric_value} {self.unit}"


class ConsentRecord(models.Model):
    profile = models.ForeignKey(GlobalUserProfile, on_delete=models.CASCADE, related_name="consents")
    source = models.ForeignKey(DataSource, on_delete=models.CASCADE, related_name="consents")
    open_to_offers = models.BooleanField("Открыт к предложениям", default=False)
    status = models.CharField("Статус", max_length=40, blank=True)
    visible_data_categories = models.JSONField("Видимые категории", default=list, blank=True)
    allowed_organization_types = models.JSONField("Разрешённые типы организаций", default=list, blank=True)
    granted_at = models.DateField("Дата выдачи", null=True, blank=True)
    expires_at = models.DateField("Дата истечения", null=True, blank=True)
    raw_data = models.JSONField("Сырые данные", default=dict, blank=True)
    updated_at = models.DateTimeField("Обновлено", auto_now=True)

    class Meta:
        unique_together = ("profile", "source")
        verbose_name = "Согласие"
        verbose_name_plural = "Согласия"

    def __str__(self):
        return f"{self.profile.full_name}: {self.status}, open={self.open_to_offers}"


class Offer(models.Model):
    STATUS_CHOICES = [
        ("pending", "Ожидает ответа"),
        ("accepted", "Принято"),
        ("rejected", "Отклонено"),
    ]

    profile = models.ForeignKey(GlobalUserProfile, on_delete=models.CASCADE, related_name="offers")
    trainer_name = models.CharField("Тренер", max_length=255)
    organization_name = models.CharField("Организация тренера", max_length=255, blank=True)
    message = models.TextField("Сообщение")
    status = models.CharField("Статус", max_length=30, choices=STATUS_CHOICES, default="pending")
    created_at = models.DateTimeField("Создано", auto_now_add=True)
    updated_at = models.DateTimeField("Обновлено", auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Предложение"
        verbose_name_plural = "Предложения"

    def __str__(self):
        return f"{self.trainer_name} -> {self.profile.full_name}: {self.status}"


class AuditLog(models.Model):
    action = models.CharField("Действие", max_length=120)
    source = models.ForeignKey(DataSource, on_delete=models.SET_NULL, null=True, blank=True)
    profile = models.ForeignKey(GlobalUserProfile, on_delete=models.SET_NULL, null=True, blank=True)
    details = models.JSONField("Детали", default=dict, blank=True)
    created_at = models.DateTimeField("Дата", auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Журнал аудита"
        verbose_name_plural = "Журнал аудита"

    def __str__(self):
        return f"{self.created_at:%Y-%m-%d %H:%M:%S} — {self.action}"
