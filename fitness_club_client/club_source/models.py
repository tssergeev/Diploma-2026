from django.db import models


class Organization(models.Model):
    name = models.CharField("Название", max_length=255)
    organization_type = models.CharField("Тип организации", max_length=80, default="fitness_club")
    city = models.CharField("Город", max_length=120, blank=True)

    def __str__(self):
        return self.name


class Member(models.Model):
    GENDER_CHOICES = [
        ("male", "Мужской"),
        ("female", "Женский"),
    ]

    local_id = models.CharField("Локальный ID", max_length=64, unique=True)
    full_name = models.CharField("ФИО", max_length=255)
    birth_date = models.DateField("Дата рождения")
    gender = models.CharField("Пол", max_length=20, choices=GENDER_CHOICES)
    phone = models.CharField("Телефон", max_length=30, blank=True)
    email = models.EmailField("Email", blank=True)
    city = models.CharField("Город", max_length=120, blank=True)
    sport_type = models.CharField("Вид активности", max_length=120, blank=True)
    training_level = models.CharField("Уровень подготовки", max_length=80, blank=True)
    organization = models.ForeignKey(
        Organization,
        verbose_name="Организация",
        on_delete=models.CASCADE,
        related_name="members",
    )
    created_at = models.DateTimeField("Дата создания", auto_now_add=True)

    def __str__(self):
        return self.full_name


class Activity(models.Model):
    INTENSITY_CHOICES = [
        ("low", "Низкая"),
        ("medium", "Средняя"),
        ("high", "Высокая"),
    ]

    member = models.ForeignKey(Member, on_delete=models.CASCADE, related_name="activities")
    activity_id = models.CharField("ID активности", max_length=64, unique=True)
    activity_date = models.DateField("Дата активности")
    activity_type = models.CharField("Тип активности", max_length=80)
    duration_minutes = models.PositiveIntegerField("Длительность, мин")
    intensity = models.CharField("Интенсивность", max_length=20, choices=INTENSITY_CHOICES)
    calories = models.PositiveIntegerField("Калории", default=0)

    class Meta:
        ordering = ["-activity_date"]

    def __str__(self):
        return f"{self.member.full_name}: {self.activity_type} {self.activity_date}"


class HealthMetric(models.Model):
    member = models.ForeignKey(Member, on_delete=models.CASCADE, related_name="metrics")
    metric_id = models.CharField("ID показателя", max_length=64, unique=True)
    metric_type = models.CharField("Тип показателя", max_length=80)
    metric_value = models.DecimalField("Значение", max_digits=8, decimal_places=2)
    unit = models.CharField("Единица измерения", max_length=30)
    measured_at = models.DateTimeField("Время измерения")

    class Meta:
        ordering = ["-measured_at"]

    def __str__(self):
        return f"{self.member.full_name}: {self.metric_type}={self.metric_value} {self.unit}"


class Consent(models.Model):
    STATUS_CHOICES = [
        ("active", "Активно"),
        ("revoked", "Отозвано"),
        ("expired", "Истекло"),
    ]

    member = models.OneToOneField(Member, on_delete=models.CASCADE, related_name="consent")
    open_to_offers = models.BooleanField("Открыт к предложениям", default=False)
    visible_data_categories = models.JSONField("Открытые категории данных", default=list)
    allowed_organization_types = models.JSONField("Разрешённые типы организаций", default=list)
    granted_at = models.DateField("Дата предоставления")
    expires_at = models.DateField("Дата истечения")
    status = models.CharField("Статус согласия", max_length=20, choices=STATUS_CHOICES, default="active")

    def __str__(self):
        return f"Согласие: {self.member.full_name} — {self.status}"
