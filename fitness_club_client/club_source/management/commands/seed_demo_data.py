from datetime import date, datetime, timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.utils import timezone

from club_source.models import Activity, Consent, HealthMetric, Member, Organization


class Command(BaseCommand):
    help = "Создаёт демонстрационные данные для первого клиента — фитнес-клуба."

    def handle(self, *args, **options):
        Activity.objects.all().delete()
        HealthMetric.objects.all().delete()
        Consent.objects.all().delete()
        Member.objects.all().delete()
        Organization.objects.all().delete()

        organization = Organization.objects.create(
            name="FitEnergy",
            organization_type="fitness_club",
            city="Москва",
        )

        members = [
            {
                "local_id": "fc_1001",
                "full_name": "Иванов Алексей Сергеевич",
                "birth_date": date(1998, 5, 14),
                "gender": "male",
                "phone": "+79991234567",
                "email": "alexey.ivanov@example.com",
                "city": "Москва",
                "sport_type": "gym_workout",
                "training_level": "intermediate",
                "open_to_offers": True,
                "visible": ["activity", "heart_rate", "hrv", "sleep"],
            },
            {
                "local_id": "fc_1002",
                "full_name": "Петрова Мария Андреевна",
                "birth_date": date(1995, 8, 21),
                "gender": "female",
                "phone": "+79990001122",
                "email": "maria.petrova@example.com",
                "city": "Москва",
                "sport_type": "cardio",
                "training_level": "advanced",
                "open_to_offers": True,
                "visible": ["activity", "heart_rate", "hrv"],
            },
            {
                "local_id": "fc_1003",
                "full_name": "Смирнов Дмитрий Олегович",
                "birth_date": date(1989, 11, 3),
                "gender": "male",
                "phone": "+79993334455",
                "email": "dmitry.smirnov@example.com",
                "city": "Москва",
                "sport_type": "strength_training",
                "training_level": "advanced",
                "open_to_offers": False,
                "visible": ["activity"],
            },
            {
                "local_id": "fc_1004",
                "full_name": "Кузнецова Анна Викторовна",
                "birth_date": date(2001, 2, 9),
                "gender": "female",
                "phone": "+79995556677",
                "email": "anna.kuznetsova@example.com",
                "city": "Москва",
                "sport_type": "functional_training",
                "training_level": "beginner",
                "open_to_offers": True,
                "visible": ["activity", "heart_rate", "weight"],
            },
            {
                "local_id": "fc_1005",
                "full_name": "Орлов Кирилл Павлович",
                "birth_date": date(1992, 6, 18),
                "gender": "male",
                "phone": "+79998887766",
                "email": "kirill.orlov@example.com",
                "city": "Москва",
                "sport_type": "crossfit",
                "training_level": "intermediate",
                "open_to_offers": True,
                "visible": ["activity", "heart_rate", "hrv", "weight"],
            },
        ]

        created_members = []
        for item in members:
            member = Member.objects.create(
                local_id=item["local_id"],
                full_name=item["full_name"],
                birth_date=item["birth_date"],
                gender=item["gender"],
                phone=item["phone"],
                email=item["email"],
                city=item["city"],
                sport_type=item["sport_type"],
                training_level=item["training_level"],
                organization=organization,
            )
            Consent.objects.create(
                member=member,
                open_to_offers=item["open_to_offers"],
                visible_data_categories=item["visible"],
                allowed_organization_types=["fitness_club", "personal_trainer"],
                granted_at=date.today() - timedelta(days=30),
                expires_at=date.today() + timedelta(days=180),
                status="active",
            )
            created_members.append(member)

        activity_types = ["gym_workout", "cardio", "strength_training", "functional_training"]
        intensities = ["medium", "high", "medium", "low"]
        today = date.today()

        for member_index, member in enumerate(created_members, start=1):
            for activity_index in range(1, 9):
                activity_type = activity_types[(member_index + activity_index) % len(activity_types)]
                Activity.objects.create(
                    member=member,
                    activity_id=f"act_{member.local_id}_{activity_index}",
                    activity_date=today - timedelta(days=activity_index * 6 + member_index),
                    activity_type=activity_type,
                    duration_minutes=45 + activity_index * 5,
                    intensity=intensities[(member_index + activity_index) % len(intensities)],
                    calories=280 + activity_index * 35,
                )

        base_datetime = timezone.make_aware(datetime.combine(today, datetime.min.time()))
        metrics = [
            ("heart_rate_resting", Decimal("62"), "bpm"),
            ("heart_rate_training_avg", Decimal("128"), "bpm"),
            ("hrv", Decimal("54"), "ms"),
            ("sleep_quality", Decimal("82"), "score"),
            ("weight", Decimal("78.4"), "kg"),
        ]

        for member_index, member in enumerate(created_members, start=1):
            for metric_index, (metric_type, value, unit) in enumerate(metrics, start=1):
                correction = Decimal(member_index * 2 + metric_index)
                HealthMetric.objects.create(
                    member=member,
                    metric_id=f"met_{member.local_id}_{metric_type}",
                    metric_type=metric_type,
                    metric_value=value + correction,
                    unit=unit,
                    measured_at=base_datetime - timedelta(days=metric_index),
                )

        self.stdout.write(self.style.SUCCESS("Демонстрационные данные первого клиента успешно созданы."))
