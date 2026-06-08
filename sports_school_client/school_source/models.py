from django.db import models


class School(models.Model):
    name = models.CharField("Название", max_length=255)
    organization_type = models.CharField("Тип организации", max_length=80, default="sports_school")
    city = models.CharField("Город", max_length=120, blank=True)
    address = models.CharField("Адрес", max_length=255, blank=True)

    def __str__(self):
        return self.name


class Section(models.Model):
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name="sections")
    code = models.CharField("Код секции", max_length=64, unique=True)
    name = models.CharField("Название секции", max_length=255)
    sport_type = models.CharField("Вид спорта", max_length=120)
    coach_name = models.CharField("Тренер", max_length=255)
    age_group = models.CharField("Возрастная группа", max_length=80, blank=True)

    def __str__(self):
        return f"{self.name} — {self.coach_name}"


class Student(models.Model):
    GENDER_CHOICES = [
        ("M", "Мужской"),
        ("F", "Женский"),
    ]

    local_code = models.CharField("Локальный код ученика", max_length=64, unique=True)
    full_name = models.CharField("ФИО", max_length=255)
    birth_year = models.PositiveIntegerField("Год рождения")
    gender_code = models.CharField("Пол", max_length=1, choices=GENDER_CHOICES)
    parent_phone = models.CharField("Телефон представителя", max_length=30, blank=True)
    city = models.CharField("Город", max_length=120, blank=True)
    section = models.ForeignKey(Section, on_delete=models.CASCADE, related_name="students")
    skill_level = models.CharField("Уровень подготовки", max_length=80, blank=True)
    enrollment_date = models.DateField("Дата зачисления", null=True, blank=True)

    class Meta:
        ordering = ["full_name"]

    def __str__(self):
        return self.full_name


class AttendanceRecord(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="attendance_records")
    record_code = models.CharField("Код занятия", max_length=64, unique=True)
    training_date = models.DateField("Дата занятия")
    present = models.BooleanField("Присутствовал", default=True)
    training_type = models.CharField("Тип занятия", max_length=120)
    duration_minutes = models.PositiveIntegerField("Длительность, мин", default=60)
    load_level = models.CharField("Уровень нагрузки", max_length=40, default="medium")

    class Meta:
        ordering = ["-training_date"]

    def __str__(self):
        return f"{self.student.full_name}: {self.training_date}"


class FitnessTest(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="fitness_tests")
    test_code = models.CharField("Код теста", max_length=64, unique=True)
    tested_at = models.DateField("Дата тестирования")
    resting_pulse = models.PositiveIntegerField("Пульс в покое", null=True, blank=True)
    height_cm = models.DecimalField("Рост, см", max_digits=6, decimal_places=2, null=True, blank=True)
    weight_kg = models.DecimalField("Вес, кг", max_digits=6, decimal_places=2, null=True, blank=True)
    endurance_score = models.PositiveIntegerField("Оценка выносливости", null=True, blank=True)
    flexibility_score = models.PositiveIntegerField("Оценка гибкости", null=True, blank=True)
    notes = models.TextField("Примечание", blank=True)

    class Meta:
        ordering = ["-tested_at"]

    def __str__(self):
        return f"Тест {self.student.full_name} от {self.tested_at}"


class DisclosurePermission(models.Model):
    STATUS_CHOICES = [
        ("active", "Активно"),
        ("revoked", "Отозвано"),
        ("expired", "Истекло"),
    ]

    student = models.OneToOneField(Student, on_delete=models.CASCADE, related_name="permission")
    can_be_found = models.BooleanField("Открыт к предложениям", default=False)
    allowed_categories = models.JSONField("Открытые категории данных", default=list)
    allowed_roles = models.JSONField("Разрешённые роли", default=list)
    granted_on = models.DateField("Дата предоставления")
    valid_until = models.DateField("Дата истечения")
    status = models.CharField("Статус", max_length=20, choices=STATUS_CHOICES, default="active")

    def __str__(self):
        return f"Разрешение: {self.student.full_name} — {self.status}"
