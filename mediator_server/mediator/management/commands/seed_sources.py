from django.core.management.base import BaseCommand

from mediator.models import DataSource


class Command(BaseCommand):
    help = "Создаёт три локальных источника данных для прототипа медиатора."

    def handle(self, *args, **options):
        sources = [
            {
                "source_id": "fitness_club_client_1",
                "name": "Клиент 1 — фитнес-клуб",
                "source_type": "fitness_club",
                "base_url": "http://127.0.0.1:8001/api/",
                "users_endpoint": "members/?include_nested=true",
                "description": "Реляционный источник: члены клуба, активности, показатели здоровья, согласия.",
                "mapping_config": {
                    "member.local_id": "User.local_id",
                    "member.full_name": "User.full_name",
                    "activity.activity_date": "Activity.activity_date",
                    "health_metric.metric_type": "HealthMetric.metric_type",
                    "consent.open_to_offers": "Consent.open_to_offers",
                },
            },
            {
                "source_id": "sports_school_client_2",
                "name": "Клиент 2 — спортивная школа",
                "source_type": "sports_school",
                "base_url": "http://127.0.0.1:8002/api/",
                "users_endpoint": "export/global/",
                "description": "Источник со школьной локальной схемой: ученики, секции, посещаемость, контрольные тесты.",
                "mapping_config": {
                    "student.local_code": "User.local_id",
                    "student.birth_year": "User.age",
                    "attendance_record.training_date": "Activity.activity_date",
                    "fitness_test.resting_pulse": "HealthMetric.heart_rate_resting",
                    "permission.can_be_found": "Consent.open_to_offers",
                },
            },
            {
                "source_id": "fitness_app_client_3",
                "name": "Клиент 3 — фитнес-приложение",
                "source_type": "fitness_app",
                "base_url": "http://127.0.0.1:8003/api/",
                "users_endpoint": "users/?include_nested=true",
                "description": "Документно-ориентированный источник: профиль, активности, healthMetrics и consent внутри JSON-документа.",
                "mapping_config": {
                    "profile.fullName": "User.full_name",
                    "activities[]": "Activity",
                    "healthMetrics.hrv.value": "HealthMetric.hrv",
                    "consent.openToOffers": "Consent.open_to_offers",
                },
            },
        ]

        for source_data in sources:
            source, created = DataSource.objects.update_or_create(
                source_id=source_data["source_id"],
                defaults={
                    "name": source_data["name"],
                    "source_type": source_data["source_type"],
                    "base_url": source_data["base_url"],
                    "users_endpoint": source_data["users_endpoint"],
                    "description": source_data["description"],
                    "mapping_config": source_data["mapping_config"],
                    "status_endpoint": "status/",
                    "schema_endpoint": "schema/",
                    "timeout_seconds": 5,
                    "is_active": True,
                },
            )
            status = "создан" if created else "обновлён"
            self.stdout.write(self.style.SUCCESS(f"{source.source_id}: {status}"))
