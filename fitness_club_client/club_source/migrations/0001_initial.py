# Generated for the diploma prototype fitness club client.

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Organization",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=255, verbose_name="Название")),
                ("organization_type", models.CharField(default="fitness_club", max_length=80, verbose_name="Тип организации")),
                ("city", models.CharField(blank=True, max_length=120, verbose_name="Город")),
            ],
        ),
        migrations.CreateModel(
            name="Member",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("local_id", models.CharField(max_length=64, unique=True, verbose_name="Локальный ID")),
                ("full_name", models.CharField(max_length=255, verbose_name="ФИО")),
                ("birth_date", models.DateField(verbose_name="Дата рождения")),
                ("gender", models.CharField(choices=[("male", "Мужской"), ("female", "Женский")], max_length=20, verbose_name="Пол")),
                ("phone", models.CharField(blank=True, max_length=30, verbose_name="Телефон")),
                ("email", models.EmailField(blank=True, max_length=254, verbose_name="Email")),
                ("city", models.CharField(blank=True, max_length=120, verbose_name="Город")),
                ("sport_type", models.CharField(blank=True, max_length=120, verbose_name="Вид активности")),
                ("training_level", models.CharField(blank=True, max_length=80, verbose_name="Уровень подготовки")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")),
                ("organization", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="members", to="club_source.organization", verbose_name="Организация")),
            ],
        ),
        migrations.CreateModel(
            name="Activity",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("activity_id", models.CharField(max_length=64, unique=True, verbose_name="ID активности")),
                ("activity_date", models.DateField(verbose_name="Дата активности")),
                ("activity_type", models.CharField(max_length=80, verbose_name="Тип активности")),
                ("duration_minutes", models.PositiveIntegerField(verbose_name="Длительность, мин")),
                ("intensity", models.CharField(choices=[("low", "Низкая"), ("medium", "Средняя"), ("high", "Высокая")], max_length=20, verbose_name="Интенсивность")),
                ("calories", models.PositiveIntegerField(default=0, verbose_name="Калории")),
                ("member", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="activities", to="club_source.member")),
            ],
            options={"ordering": ["-activity_date"]},
        ),
        migrations.CreateModel(
            name="Consent",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("open_to_offers", models.BooleanField(default=False, verbose_name="Открыт к предложениям")),
                ("visible_data_categories", models.JSONField(default=list, verbose_name="Открытые категории данных")),
                ("allowed_organization_types", models.JSONField(default=list, verbose_name="Разрешённые типы организаций")),
                ("granted_at", models.DateField(verbose_name="Дата предоставления")),
                ("expires_at", models.DateField(verbose_name="Дата истечения")),
                ("status", models.CharField(choices=[("active", "Активно"), ("revoked", "Отозвано"), ("expired", "Истекло")], default="active", max_length=20, verbose_name="Статус согласия")),
                ("member", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="consent", to="club_source.member")),
            ],
        ),
        migrations.CreateModel(
            name="HealthMetric",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("metric_id", models.CharField(max_length=64, unique=True, verbose_name="ID показателя")),
                ("metric_type", models.CharField(max_length=80, verbose_name="Тип показателя")),
                ("metric_value", models.DecimalField(decimal_places=2, max_digits=8, verbose_name="Значение")),
                ("unit", models.CharField(max_length=30, verbose_name="Единица измерения")),
                ("measured_at", models.DateTimeField(verbose_name="Время измерения")),
                ("member", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="metrics", to="club_source.member")),
            ],
            options={"ordering": ["-measured_at"]},
        ),
    ]
