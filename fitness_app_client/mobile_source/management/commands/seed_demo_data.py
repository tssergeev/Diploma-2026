from django.core.management.base import BaseCommand

from mobile_source.models import FitnessDocument


class Command(BaseCommand):
    help = "Заполняет третий клиент тестовыми JSON-документами фитнес-приложения"

    def handle(self, *args, **options):
        FitnessDocument.objects.all().delete()

        documents = [
            {
                "userId": "app_3001",
                "profile": {
                    "fullName": "Иванова Мария Андреевна",
                    "birthDate": "1996-04-18",
                    "gender": "female",
                    "phone": "+79991110001",
                    "email": "maria.ivanova@example.com",
                    "city": "Москва",
                    "sportType": "functional_training",
                    "trainingLevel": "advanced",
                },
                "organization": {
                    "orgId": "fitapp_01",
                    "name": "PulseTrack Mobile",
                    "type": "fitness_app",
                    "city": "Москва",
                },
                "activities": [
                    {
                        "activityId": "mob_act_9001",
                        "date": "2026-04-24",
                        "type": "functional_training",
                        "durationMin": 70,
                        "intensity": "high",
                        "calories": 590,
                    },
                    {
                        "activityId": "mob_act_9002",
                        "date": "2026-05-02",
                        "type": "cardio",
                        "durationMin": 45,
                        "intensity": "medium",
                        "calories": 410,
                    },
                    {
                        "activityId": "mob_act_9003",
                        "date": "2026-05-07",
                        "type": "gym_workout",
                        "durationMin": 80,
                        "intensity": "high",
                        "calories": 640,
                    },
                ],
                "healthMetrics": {
                    "heartRate": {
                        "resting": 58,
                        "avgTraining": 132,
                        "measuredAt": "2026-05-08T08:20:00",
                    },
                    "hrv": {
                        "value": 61,
                        "unit": "ms",
                        "measuredAt": "2026-05-08T08:20:00",
                    },
                    "sleep": {
                        "durationHours": 7.6,
                        "qualityScore": 86,
                        "measuredAt": "2026-05-08T07:30:00",
                    },
                    "weight": {
                        "value": 62.4,
                        "unit": "kg",
                        "measuredAt": "2026-05-07",
                    },
                    "stress": {
                        "score": 24,
                        "measuredAt": "2026-05-08T08:20:00",
                    },
                    "vo2max": {
                        "value": 47,
                        "unit": "ml/kg/min",
                        "measuredAt": "2026-05-01",
                    },
                },
                "consent": {
                    "openToOffers": True,
                    "visibleDataCategories": ["activity", "heart_rate", "hrv", "sleep"],
                    "allowedOrganizationTypes": ["fitness_club", "personal_trainer"],
                    "grantedAt": "2026-03-01",
                    "expiresAt": "2026-09-01",
                    "status": "active",
                },
                "sourceMeta": {
                    "sourceSystem": "mobile_fitness_app",
                    "schemaVersion": "1.2",
                    "device": "smart_watch",
                },
            },
            {
                "userId": "app_3002",
                "profile": {
                    "fullName": "Смирнов Алексей Павлович",
                    "birthDate": "1991-10-03",
                    "gender": "male",
                    "phone": "+79991110002",
                    "email": "alexey.smirnov@example.com",
                    "city": "Санкт-Петербург",
                    "sportType": "running",
                    "trainingLevel": "intermediate",
                },
                "organization": {
                    "orgId": "fitapp_01",
                    "name": "PulseTrack Mobile",
                    "type": "fitness_app",
                    "city": "Санкт-Петербург",
                },
                "activities": [
                    {
                        "activityId": "mob_act_9011",
                        "date": "2026-04-18",
                        "type": "running",
                        "durationMin": 52,
                        "intensity": "medium",
                        "calories": 520,
                    },
                    {
                        "activityId": "mob_act_9012",
                        "date": "2026-04-26",
                        "type": "running",
                        "durationMin": 60,
                        "intensity": "medium",
                        "calories": 610,
                    },
                    {
                        "activityId": "mob_act_9013",
                        "date": "2026-05-06",
                        "type": "cardio",
                        "durationMin": 35,
                        "intensity": "low",
                        "calories": 260,
                    },
                ],
                "healthMetrics": {
                    "heartRate": {
                        "resting": 64,
                        "avgTraining": 124,
                        "measuredAt": "2026-05-07T09:00:00",
                    },
                    "hrv": {
                        "value": 49,
                        "unit": "ms",
                        "measuredAt": "2026-05-07T09:00:00",
                    },
                    "sleep": {
                        "durationHours": 6.9,
                        "qualityScore": 74,
                        "measuredAt": "2026-05-07T07:40:00",
                    },
                    "weight": {
                        "value": 78.1,
                        "unit": "kg",
                        "measuredAt": "2026-05-06",
                    },
                    "vo2max": {
                        "value": 43,
                        "unit": "ml/kg/min",
                        "measuredAt": "2026-05-01",
                    },
                },
                "consent": {
                    "openToOffers": True,
                    "visibleDataCategories": ["activity", "hrv", "heart_rate"],
                    "allowedOrganizationTypes": ["fitness_club", "sports_school", "personal_trainer"],
                    "grantedAt": "2026-02-15",
                    "expiresAt": "2026-08-15",
                    "status": "active",
                },
                "sourceMeta": {
                    "sourceSystem": "mobile_fitness_app",
                    "schemaVersion": "1.2",
                    "device": "phone_and_watch",
                },
            },
            {
                "userId": "app_3003",
                "profile": {
                    "fullName": "Кузнецова Елена Игоревна",
                    "birthDate": "2000-07-22",
                    "gender": "female",
                    "phone": "+79991110003",
                    "email": "elena.kuznetsova@example.com",
                    "city": "Москва",
                    "sportType": "yoga",
                    "trainingLevel": "beginner",
                },
                "organization": {
                    "orgId": "fitapp_02",
                    "name": "Wellness Cloud",
                    "type": "fitness_app",
                    "city": "Москва",
                },
                "activities": [
                    {
                        "activityId": "mob_act_9021",
                        "date": "2026-04-29",
                        "type": "yoga",
                        "durationMin": 55,
                        "intensity": "low",
                        "calories": 180,
                    },
                    {
                        "activityId": "mob_act_9022",
                        "date": "2026-05-04",
                        "type": "stretching",
                        "durationMin": 35,
                        "intensity": "low",
                        "calories": 110,
                    },
                ],
                "healthMetrics": {
                    "heartRate": {
                        "resting": 66,
                        "avgTraining": 105,
                        "measuredAt": "2026-05-05T08:50:00",
                    },
                    "hrv": {
                        "value": 56,
                        "unit": "ms",
                        "measuredAt": "2026-05-05T08:50:00",
                    },
                    "sleep": {
                        "durationHours": 8.1,
                        "qualityScore": 90,
                        "measuredAt": "2026-05-05T07:10:00",
                    },
                    "weight": {
                        "value": 57.8,
                        "unit": "kg",
                        "measuredAt": "2026-05-04",
                    },
                    "stress": {
                        "score": 18,
                        "measuredAt": "2026-05-05T08:50:00",
                    },
                },
                "consent": {
                    "openToOffers": False,
                    "visibleDataCategories": ["activity"],
                    "allowedOrganizationTypes": [],
                    "grantedAt": "2026-01-20",
                    "expiresAt": "2026-07-20",
                    "status": "active",
                },
                "sourceMeta": {
                    "sourceSystem": "wellness_mobile_app",
                    "schemaVersion": "2.0",
                    "device": "smart_watch",
                },
            },
            {
                "userId": "app_3004",
                "profile": {
                    "fullName": "Петров Дмитрий Сергеевич",
                    "birthDate": "1988-12-11",
                    "gender": "male",
                    "phone": "+79991110004",
                    "email": "dmitry.petrov@example.com",
                    "city": "Казань",
                    "sportType": "strength_training",
                    "trainingLevel": "advanced",
                },
                "organization": {
                    "orgId": "fitapp_03",
                    "name": "GymSync Wearable",
                    "type": "wearable_platform",
                    "city": "Казань",
                },
                "activities": [
                    {
                        "activityId": "mob_act_9031",
                        "date": "2026-03-20",
                        "type": "gym_workout",
                        "durationMin": 90,
                        "intensity": "high",
                        "calories": 710,
                    },
                    {
                        "activityId": "mob_act_9032",
                        "date": "2026-04-08",
                        "type": "gym_workout",
                        "durationMin": 85,
                        "intensity": "high",
                        "calories": 680,
                    },
                    {
                        "activityId": "mob_act_9033",
                        "date": "2026-04-28",
                        "type": "cardio",
                        "durationMin": 30,
                        "intensity": "medium",
                        "calories": 300,
                    },
                    {
                        "activityId": "mob_act_9034",
                        "date": "2026-05-09",
                        "type": "gym_workout",
                        "durationMin": 95,
                        "intensity": "high",
                        "calories": 760,
                    },
                ],
                "healthMetrics": {
                    "heartRate": {
                        "resting": 60,
                        "avgTraining": 138,
                        "measuredAt": "2026-05-10T07:55:00",
                    },
                    "hrv": {
                        "value": 53,
                        "unit": "ms",
                        "measuredAt": "2026-05-10T07:55:00",
                    },
                    "sleep": {
                        "durationHours": 7.0,
                        "qualityScore": 78,
                        "measuredAt": "2026-05-10T07:00:00",
                    },
                    "weight": {
                        "value": 86.5,
                        "unit": "kg",
                        "measuredAt": "2026-05-09",
                    },
                    "stress": {
                        "score": 31,
                        "measuredAt": "2026-05-10T07:55:00",
                    },
                    "vo2max": {
                        "value": 46,
                        "unit": "ml/kg/min",
                        "measuredAt": "2026-05-02",
                    },
                },
                "consent": {
                    "openToOffers": True,
                    "visibleDataCategories": ["activity", "heart_rate", "hrv", "weight"],
                    "allowedOrganizationTypes": ["fitness_club", "personal_trainer"],
                    "grantedAt": "2026-04-01",
                    "expiresAt": "2026-10-01",
                    "status": "active",
                },
                "sourceMeta": {
                    "sourceSystem": "wearable_platform",
                    "schemaVersion": "1.0",
                    "device": "wearable_band",
                },
            },
            {
                "userId": "app_3005",
                "profile": {
                    "fullName": "Орлова Анна Викторовна",
                    "birthDate": "1999-02-08",
                    "gender": "female",
                    "phone": "+79991110005",
                    "email": "anna.orlova@example.com",
                    "city": "Москва",
                    "sportType": "cardio",
                    "trainingLevel": "intermediate",
                },
                "organization": {
                    "orgId": "fitapp_03",
                    "name": "GymSync Wearable",
                    "type": "wearable_platform",
                    "city": "Москва",
                },
                "activities": [
                    {
                        "activityId": "mob_act_9041",
                        "date": "2026-02-14",
                        "type": "cardio",
                        "durationMin": 42,
                        "intensity": "medium",
                        "calories": 390,
                    },
                    {
                        "activityId": "mob_act_9042",
                        "date": "2026-03-19",
                        "type": "cardio",
                        "durationMin": 38,
                        "intensity": "medium",
                        "calories": 350,
                    },
                ],
                "healthMetrics": {
                    "heartRate": {
                        "resting": 70,
                        "avgTraining": 126,
                        "measuredAt": "2026-03-20T09:10:00",
                    },
                    "hrv": {
                        "value": 42,
                        "unit": "ms",
                        "measuredAt": "2026-03-20T09:10:00",
                    },
                    "sleep": {
                        "durationHours": 6.4,
                        "qualityScore": 68,
                        "measuredAt": "2026-03-20T07:15:00",
                    },
                    "weight": {
                        "value": 64.9,
                        "unit": "kg",
                        "measuredAt": "2026-03-19",
                    },
                    "stress": {
                        "score": 45,
                        "measuredAt": "2026-03-20T09:10:00",
                    },
                },
                "consent": {
                    "openToOffers": True,
                    "visibleDataCategories": ["activity", "heart_rate"],
                    "allowedOrganizationTypes": ["fitness_club"],
                    "grantedAt": "2025-10-01",
                    "expiresAt": "2026-04-01",
                    "status": "expired",
                },
                "sourceMeta": {
                    "sourceSystem": "wearable_platform",
                    "schemaVersion": "1.0",
                    "device": "wearable_band",
                },
            },
        ]

        for document in documents:
            FitnessDocument.objects.create(local_id=document["userId"], document=document)

        self.stdout.write(self.style.SUCCESS(f"Создано JSON-документов: {len(documents)}"))
