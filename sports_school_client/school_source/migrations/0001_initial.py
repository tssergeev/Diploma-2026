# Generated manually for the prototype project.

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="School",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=255, verbose_name="Название")),
                ("organization_type", models.CharField(default="sports_school", max_length=80, verbose_name="Тип организации")),
                ("city", models.CharField(blank=True, max_length=120, verbose_name="Город")),
                ("address", models.CharField(blank=True, max_length=255, verbose_name="Адрес")),
            ],
        ),
        migrations.CreateModel(
            name="Section",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("code", models.CharField(max_length=64, unique=True, verbose_name="Код секции")),
                ("name", models.CharField(max_length=255, verbose_name="Название секции")),
                ("sport_type", models.CharField(max_length=120, verbose_name="Вид спорта")),
                ("coach_name", models.CharField(max_length=255, verbose_name="Тренер")),
                ("age_group", models.CharField(blank=True, max_length=80, verbose_name="Возрастная группа")),
                (
                    "school",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="sections", to="school_source.school"),
                ),
            ],
        ),
        migrations.CreateModel(
            name="Student",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("local_code", models.CharField(max_length=64, unique=True, verbose_name="Локальный код ученика")),
                ("full_name", models.CharField(max_length=255, verbose_name="ФИО")),
                ("birth_year", models.PositiveIntegerField(verbose_name="Год рождения")),
                (
                    "gender_code",
                    models.CharField(choices=[("M", "Мужской"), ("F", "Женский")], max_length=1, verbose_name="Пол"),
                ),
                ("parent_phone", models.CharField(blank=True, max_length=30, verbose_name="Телефон представителя")),
                ("city", models.CharField(blank=True, max_length=120, verbose_name="Город")),
                ("skill_level", models.CharField(blank=True, max_length=80, verbose_name="Уровень подготовки")),
                ("enrollment_date", models.DateField(blank=True, null=True, verbose_name="Дата зачисления")),
                (
                    "section",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="students", to="school_source.section"),
                ),
            ],
            options={"ordering": ["full_name"]},
        ),
        migrations.CreateModel(
            name="AttendanceRecord",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("record_code", models.CharField(max_length=64, unique=True, verbose_name="Код занятия")),
                ("training_date", models.DateField(verbose_name="Дата занятия")),
                ("present", models.BooleanField(default=True, verbose_name="Присутствовал")),
                ("training_type", models.CharField(max_length=120, verbose_name="Тип занятия")),
                ("duration_minutes", models.PositiveIntegerField(default=60, verbose_name="Длительность, мин")),
                ("load_level", models.CharField(default="medium", max_length=40, verbose_name="Уровень нагрузки")),
                (
                    "student",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="attendance_records", to="school_source.student"),
                ),
            ],
            options={"ordering": ["-training_date"]},
        ),
        migrations.CreateModel(
            name="FitnessTest",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("test_code", models.CharField(max_length=64, unique=True, verbose_name="Код теста")),
                ("tested_at", models.DateField(verbose_name="Дата тестирования")),
                ("resting_pulse", models.PositiveIntegerField(blank=True, null=True, verbose_name="Пульс в покое")),
                ("height_cm", models.DecimalField(blank=True, decimal_places=2, max_digits=6, null=True, verbose_name="Рост, см")),
                ("weight_kg", models.DecimalField(blank=True, decimal_places=2, max_digits=6, null=True, verbose_name="Вес, кг")),
                ("endurance_score", models.PositiveIntegerField(blank=True, null=True, verbose_name="Оценка выносливости")),
                ("flexibility_score", models.PositiveIntegerField(blank=True, null=True, verbose_name="Оценка гибкости")),
                ("notes", models.TextField(blank=True, verbose_name="Примечание")),
                (
                    "student",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="fitness_tests", to="school_source.student"),
                ),
            ],
            options={"ordering": ["-tested_at"]},
        ),
        migrations.CreateModel(
            name="DisclosurePermission",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("can_be_found", models.BooleanField(default=False, verbose_name="Открыт к предложениям")),
                ("allowed_categories", models.JSONField(default=list, verbose_name="Открытые категории данных")),
                ("allowed_roles", models.JSONField(default=list, verbose_name="Разрешённые роли")),
                ("granted_on", models.DateField(verbose_name="Дата предоставления")),
                ("valid_until", models.DateField(verbose_name="Дата истечения")),
                (
                    "status",
                    models.CharField(
                        choices=[("active", "Активно"), ("revoked", "Отозвано"), ("expired", "Истекло")],
                        default="active",
                        max_length=20,
                        verbose_name="Статус",
                    ),
                ),
                (
                    "student",
                    models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="permission", to="school_source.student"),
                ),
            ],
        ),
    ]
