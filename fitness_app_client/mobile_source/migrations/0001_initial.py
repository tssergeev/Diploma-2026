from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="FitnessDocument",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("local_id", models.CharField(max_length=64, unique=True, verbose_name="Локальный ID пользователя")),
                ("document", models.JSONField(default=dict, verbose_name="JSON-документ пользователя")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="Дата обновления")),
            ],
            options={
                "verbose_name": "JSON-документ фитнес-приложения",
                "verbose_name_plural": "JSON-документы фитнес-приложения",
                "ordering": ["local_id"],
            },
        ),
    ]
