from datetime import date, timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand

from school_source.models import AttendanceRecord, DisclosurePermission, FitnessTest, School, Section, Student


class Command(BaseCommand):
    help = "Создаёт демонстрационные данные для второго клиента — спортивной школы."

    def handle(self, *args, **options):
        AttendanceRecord.objects.all().delete()
        FitnessTest.objects.all().delete()
        DisclosurePermission.objects.all().delete()
        Student.objects.all().delete()
        Section.objects.all().delete()
        School.objects.all().delete()

        school = School.objects.create(
            name="Спортивная школа Олимп",
            organization_type="sports_school",
            city="Москва",
            address="ул. Спортивная, 12",
        )

        sections = {
            "swimming": Section.objects.create(
                school=school,
                code="sec_swim_01",
                name="Плавание",
                sport_type="swimming",
                coach_name="Соколова Елена Игоревна",
                age_group="12-16",
            ),
            "athletics": Section.objects.create(
                school=school,
                code="sec_run_01",
                name="Лёгкая атлетика",
                sport_type="athletics",
                coach_name="Морозов Андрей Павлович",
                age_group="13-17",
            ),
            "basketball": Section.objects.create(
                school=school,
                code="sec_basket_01",
                name="Баскетбол",
                sport_type="basketball",
                coach_name="Никитин Роман Сергеевич",
                age_group="14-18",
            ),
        }

        students_data = [
            {
                "local_code": "ss_2001",
                "full_name": "Алексеева Дарья Михайловна",
                "birth_year": 2010,
                "gender_code": "F",
                "parent_phone": "+79990101010",
                "city": "Москва",
                "section": sections["swimming"],
                "skill_level": "intermediate",
                "can_be_found": True,
                "allowed": ["activity", "heart_rate", "weight", "endurance_score"],
            },
            {
                "local_code": "ss_2002",
                "full_name": "Григорьев Матвей Олегович",
                "birth_year": 2009,
                "gender_code": "M",
                "parent_phone": "+79990202020",
                "city": "Москва",
                "section": sections["athletics"],
                "skill_level": "advanced",
                "can_be_found": True,
                "allowed": ["activity", "heart_rate", "endurance_score", "flexibility_score"],
            },
            {
                "local_code": "ss_2003",
                "full_name": "Кириллова Полина Денисовна",
                "birth_year": 2011,
                "gender_code": "F",
                "parent_phone": "+79990303030",
                "city": "Москва",
                "section": sections["basketball"],
                "skill_level": "beginner",
                "can_be_found": False,
                "allowed": ["activity"],
            },
            {
                "local_code": "ss_2004",
                "full_name": "Медведев Артём Ильич",
                "birth_year": 2008,
                "gender_code": "M",
                "parent_phone": "+79990404040",
                "city": "Химки",
                "section": sections["swimming"],
                "skill_level": "advanced",
                "can_be_found": True,
                "allowed": ["activity", "heart_rate", "weight", "endurance_score"],
            },
            {
                "local_code": "ss_2005",
                "full_name": "Романова Софья Ильинична",
                "birth_year": 2010,
                "gender_code": "F",
                "parent_phone": "+79990505050",
                "city": "Москва",
                "section": sections["athletics"],
                "skill_level": "intermediate",
                "can_be_found": True,
                "allowed": ["activity", "heart_rate", "endurance_score"],
            },
        ]

        students = []
        for index, item in enumerate(students_data, start=1):
            student = Student.objects.create(
                local_code=item["local_code"],
                full_name=item["full_name"],
                birth_year=item["birth_year"],
                gender_code=item["gender_code"],
                parent_phone=item["parent_phone"],
                city=item["city"],
                section=item["section"],
                skill_level=item["skill_level"],
                enrollment_date=date.today() - timedelta(days=365 + index * 45),
            )
            DisclosurePermission.objects.create(
                student=student,
                can_be_found=item["can_be_found"],
                allowed_categories=item["allowed"],
                allowed_roles=["personal_trainer", "sports_club", "sports_school_representative"],
                granted_on=date.today() - timedelta(days=20),
                valid_until=date.today() + timedelta(days=160),
                status="active",
            )
            students.append(student)

        training_types_by_sport = {
            "swimming": ["pool_training", "dryland_training", "technique"],
            "athletics": ["running", "interval_training", "general_physical_training"],
            "basketball": ["team_training", "shooting_practice", "general_physical_training"],
        }
        load_levels = ["low", "medium", "high", "medium"]
        today = date.today()

        for student_index, student in enumerate(students, start=1):
            sport_types = training_types_by_sport[student.section.sport_type]
            for lesson_index in range(1, 11):
                AttendanceRecord.objects.create(
                    student=student,
                    record_code=f"att_{student.local_code}_{lesson_index}",
                    training_date=today - timedelta(days=lesson_index * 5 + student_index),
                    present=(lesson_index % 5 != 0),
                    training_type=sport_types[(lesson_index + student_index) % len(sport_types)],
                    duration_minutes=60 + (lesson_index % 3) * 15,
                    load_level=load_levels[(lesson_index + student_index) % len(load_levels)],
                )

        for student_index, student in enumerate(students, start=1):
            for test_index in range(1, 4):
                FitnessTest.objects.create(
                    student=student,
                    test_code=f"fit_{student.local_code}_{test_index}",
                    tested_at=today - timedelta(days=test_index * 30),
                    resting_pulse=58 + student_index * 2 + test_index,
                    height_cm=Decimal("150.0") + Decimal(student_index * 4 + test_index),
                    weight_kg=Decimal("45.0") + Decimal(student_index * 3 + test_index) / Decimal("2"),
                    endurance_score=70 + student_index * 3 + test_index,
                    flexibility_score=65 + student_index * 2 + test_index,
                    notes="Плановое контрольное тестирование",
                )

        self.stdout.write(self.style.SUCCESS("Демонстрационные данные второго клиента успешно созданы."))
