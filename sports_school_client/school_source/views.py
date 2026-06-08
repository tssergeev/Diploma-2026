from datetime import date, timedelta
from decimal import Decimal, InvalidOperation

from django.contrib import messages
from django.db.models import Count, Q
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.views.decorators.http import require_GET

from .forms import (
    AttendanceRecordForm,
    DisclosurePermissionForm,
    FitnessTestForm,
    SchoolForm,
    SectionForm,
    StudentForm,
)
from .models import AttendanceRecord, DisclosurePermission, FitnessTest, School, Section, Student


SOURCE_ID = "sports_school_client_2"


def _parse_bool(value):
    if value is None:
        return None
    return str(value).lower() in {"1", "true", "yes", "да"}


def _parse_int(value, default=None):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _parse_decimal(value):
    try:
        return Decimal(str(value))
    except (TypeError, InvalidOperation):
        return None


def _iso_date(value):
    return value.isoformat() if value else None


def _age_from_year(birth_year):
    return date.today().year - birth_year


def _normalize_gender(value):
    if value == "M":
        return "male"
    if value == "F":
        return "female"
    return "unknown"


def school_to_dict(school):
    return {
        "school_id": school.id,
        "organization_name": school.name,
        "organization_type": school.organization_type,
        "city": school.city,
        "address": school.address,
    }


def section_to_dict(section):
    return {
        "section_id": section.id,
        "section_code": section.code,
        "section_name": section.name,
        "sport_type": section.sport_type,
        "coach_name": section.coach_name,
        "age_group": section.age_group,
        "school": school_to_dict(section.school),
    }


def attendance_to_dict(record):
    return {
        "activity_id": record.record_code,
        "local_user_id": record.student.local_code,
        "activity_date": _iso_date(record.training_date),
        "activity_type": record.training_type,
        "present": record.present,
        "duration_minutes": record.duration_minutes,
        "intensity": record.load_level,
    }


def fitness_test_to_metrics(test):
    metric_rows = []
    metric_map = [
        ("heart_rate_resting", test.resting_pulse, "bpm"),
        ("height", test.height_cm, "cm"),
        ("weight", test.weight_kg, "kg"),
        ("endurance_score", test.endurance_score, "score"),
        ("flexibility_score", test.flexibility_score, "score"),
    ]
    for metric_type, value, unit in metric_map:
        if value is None:
            continue
        metric_rows.append(
            {
                "metric_id": f"{test.test_code}_{metric_type}",
                "local_user_id": test.student.local_code,
                "metric_type": metric_type,
                "metric_value": float(value),
                "unit": unit,
                "measured_at": _iso_date(test.tested_at),
                "source_test_code": test.test_code,
            }
        )
    return metric_rows


def fitness_test_to_dict(test):
    return {
        "test_code": test.test_code,
        "local_user_id": test.student.local_code,
        "tested_at": _iso_date(test.tested_at),
        "resting_pulse": test.resting_pulse,
        "height_cm": float(test.height_cm) if test.height_cm is not None else None,
        "weight_kg": float(test.weight_kg) if test.weight_kg is not None else None,
        "endurance_score": test.endurance_score,
        "flexibility_score": test.flexibility_score,
        "notes": test.notes,
        "global_metrics": fitness_test_to_metrics(test),
    }


def permission_to_dict(permission):
    return {
        "local_user_id": permission.student.local_code,
        "open_to_offers": permission.can_be_found,
        "visible_data_categories": permission.allowed_categories,
        "allowed_organization_types": permission.allowed_roles,
        "granted_at": _iso_date(permission.granted_on),
        "expires_at": _iso_date(permission.valid_until),
        "status": permission.status,
    }


def student_to_dict(student, include_nested=False):
    data = {
        "source": SOURCE_ID,
        "local_user_id": student.local_code,
        "full_name": student.full_name,
        "birth_year": student.birth_year,
        "age": _age_from_year(student.birth_year),
        "gender_source_value": student.gender_code,
        "gender": _normalize_gender(student.gender_code),
        "phone": student.parent_phone,
        "city": student.city,
        "sport_type": student.section.sport_type,
        "training_level": student.skill_level,
        "enrollment_date": _iso_date(student.enrollment_date),
        "organization": school_to_dict(student.section.school),
        "section": section_to_dict(student.section),
        "consent": permission_to_dict(student.permission) if hasattr(student, "permission") else None,
    }

    if include_nested:
        data["activities"] = [attendance_to_dict(item) for item in student.attendance_records.all()]
        data["fitness_tests"] = [fitness_test_to_dict(item) for item in student.fitness_tests.all()]
        data["health_metrics"] = []
        for test in student.fitness_tests.all():
            data["health_metrics"].extend(fitness_test_to_metrics(test))

    return data


@require_GET
def status(request):
    return JsonResponse(
        {
            "service": SOURCE_ID,
            "role": "local_data_source",
            "description": "Второй клиент: источник данных детско-юношеской спортивной школы для сервера-медиатора",
            "database": "sqlite",
            "schools": School.objects.count(),
            "sections": Section.objects.count(),
            "students": Student.objects.count(),
            "attendance_records": AttendanceRecord.objects.count(),
            "fitness_tests": FitnessTest.objects.count(),
            "permissions": DisclosurePermission.objects.count(),
        },
        json_dumps_params={"ensure_ascii": False, "indent": 2},
    )


@require_GET
def schema(request):
    return JsonResponse(
        {
            "source_id": SOURCE_ID,
            "source_type": "relational_database_with_legacy_school_schema",
            "description": "Локальная схема отличается от глобальной: дата рождения хранится как год, пол кодируется M/F, показатели здоровья собраны в таблице контрольных тестов.",
            "local_entities": {
                "student": [
                    "local_code",
                    "full_name",
                    "birth_year",
                    "gender_code",
                    "parent_phone",
                    "city",
                    "section_id",
                    "skill_level",
                ],
                "attendance_record": [
                    "record_code",
                    "student_id",
                    "training_date",
                    "present",
                    "training_type",
                    "duration_minutes",
                    "load_level",
                ],
                "fitness_test": [
                    "test_code",
                    "student_id",
                    "tested_at",
                    "resting_pulse",
                    "height_cm",
                    "weight_kg",
                    "endurance_score",
                    "flexibility_score",
                ],
                "disclosure_permission": [
                    "student_id",
                    "can_be_found",
                    "allowed_categories",
                    "allowed_roles",
                    "granted_on",
                    "valid_until",
                    "status",
                ],
            },
            "mapping_to_global_schema": {
                "student.local_code": "User.local_id",
                "student.full_name": "User.full_name",
                "student.birth_year": "User.birth_date / User.age calculated approximately",
                "student.gender_code": "User.gender after normalization: M/F -> male/female",
                "student.parent_phone": "User.phone",
                "section.sport_type": "User.sport_type",
                "attendance_record.training_date": "Activity.activity_date",
                "attendance_record.training_type": "Activity.activity_type",
                "attendance_record.load_level": "Activity.intensity",
                "fitness_test.resting_pulse": "HealthMetric.heart_rate_resting",
                "fitness_test.weight_kg": "HealthMetric.weight",
                "fitness_test.endurance_score": "HealthMetric.endurance_score",
                "disclosure_permission.can_be_found": "Consent.open_to_offers",
                "disclosure_permission.status": "Consent.status",
            },
        },
        json_dumps_params={"ensure_ascii": False, "indent": 2},
    )


@require_GET
def schools(request):
    data = [school_to_dict(item) for item in School.objects.all()]
    return JsonResponse({"count": len(data), "results": data}, json_dumps_params={"ensure_ascii": False, "indent": 2})


@require_GET
def sections(request):
    queryset = Section.objects.select_related("school").all()
    sport_type = request.GET.get("sport_type")
    if sport_type:
        queryset = queryset.filter(sport_type=sport_type)
    data = [section_to_dict(item) for item in queryset]
    return JsonResponse({"count": len(data), "results": data}, json_dumps_params={"ensure_ascii": False, "indent": 2})


@require_GET
def students(request):
    queryset = Student.objects.select_related("section", "section__school", "permission").prefetch_related(
        "attendance_records", "fitness_tests"
    )

    gender = request.GET.get("gender")
    city = request.GET.get("city")
    sport_type = request.GET.get("sport_type")
    skill_level = request.GET.get("skill_level")
    training_type = request.GET.get("activity_type")
    open_to_offers = _parse_bool(request.GET.get("open_to_offers"))
    min_age = _parse_int(request.GET.get("min_age"))
    max_age = _parse_int(request.GET.get("max_age"))
    min_attendance = _parse_int(request.GET.get("min_attendance"))
    period_days = _parse_int(request.GET.get("period_days"), 90)
    min_endurance = _parse_int(request.GET.get("min_endurance"))
    min_weight = _parse_decimal(request.GET.get("min_weight"))
    max_weight = _parse_decimal(request.GET.get("max_weight"))

    if gender in {"male", "female"}:
        queryset = queryset.filter(gender_code="M" if gender == "male" else "F")
    elif gender in {"M", "F"}:
        queryset = queryset.filter(gender_code=gender)
    if city:
        queryset = queryset.filter(city__iexact=city)
    if sport_type:
        queryset = queryset.filter(section__sport_type=sport_type)
    if skill_level:
        queryset = queryset.filter(skill_level__iexact=skill_level)
    if open_to_offers is not None:
        queryset = queryset.filter(permission__can_be_found=open_to_offers, permission__status="active")

    current_year = date.today().year
    if min_age is not None:
        queryset = queryset.filter(birth_year__lte=current_year - min_age)
    if max_age is not None:
        queryset = queryset.filter(birth_year__gte=current_year - max_age)

    if training_type:
        queryset = queryset.filter(attendance_records__training_type=training_type)

    if min_attendance is not None:
        start_date = date.today() - timedelta(days=period_days)
        attendance_filter = Q(attendance_records__training_date__gte=start_date, attendance_records__present=True)
        if training_type:
            attendance_filter &= Q(attendance_records__training_type=training_type)
        queryset = queryset.annotate(attendance_count=Count("attendance_records", filter=attendance_filter)).filter(
            attendance_count__gte=min_attendance
        )

    if min_endurance is not None:
        queryset = queryset.filter(fitness_tests__endurance_score__gte=min_endurance)
    if min_weight is not None:
        queryset = queryset.filter(fitness_tests__weight_kg__gte=min_weight)
    if max_weight is not None:
        queryset = queryset.filter(fitness_tests__weight_kg__lte=max_weight)

    include_nested = _parse_bool(request.GET.get("include_nested")) or False
    queryset = queryset.distinct().order_by("full_name")
    data = [student_to_dict(item, include_nested=include_nested) for item in queryset]

    return JsonResponse(
        {
            "count": len(data),
            "filters": request.GET.dict(),
            "results": data,
        },
        json_dumps_params={"ensure_ascii": False, "indent": 2},
    )


@require_GET
def student_detail(request, local_code):
    try:
        student = Student.objects.select_related("section", "section__school", "permission").prefetch_related(
            "attendance_records", "fitness_tests"
        ).get(local_code=local_code)
    except Student.DoesNotExist:
        return JsonResponse({"detail": "Ученик не найден"}, status=404, json_dumps_params={"ensure_ascii": False})

    return JsonResponse(student_to_dict(student, include_nested=True), json_dumps_params={"ensure_ascii": False, "indent": 2})


@require_GET
def attendance(request):
    queryset = AttendanceRecord.objects.select_related("student").all()
    local_user_id = request.GET.get("local_user_id")
    training_type = request.GET.get("activity_type")
    date_from = request.GET.get("date_from")
    date_to = request.GET.get("date_to")
    present = _parse_bool(request.GET.get("present"))

    if local_user_id:
        queryset = queryset.filter(student__local_code=local_user_id)
    if training_type:
        queryset = queryset.filter(training_type=training_type)
    if date_from:
        queryset = queryset.filter(training_date__gte=date_from)
    if date_to:
        queryset = queryset.filter(training_date__lte=date_to)
    if present is not None:
        queryset = queryset.filter(present=present)

    data = [attendance_to_dict(item) for item in queryset]
    return JsonResponse({"count": len(data), "results": data}, json_dumps_params={"ensure_ascii": False, "indent": 2})


@require_GET
def fitness_tests(request):
    queryset = FitnessTest.objects.select_related("student").all()
    local_user_id = request.GET.get("local_user_id")
    date_from = request.GET.get("date_from")
    date_to = request.GET.get("date_to")

    if local_user_id:
        queryset = queryset.filter(student__local_code=local_user_id)
    if date_from:
        queryset = queryset.filter(tested_at__gte=date_from)
    if date_to:
        queryset = queryset.filter(tested_at__lte=date_to)

    data = [fitness_test_to_dict(item) for item in queryset]
    return JsonResponse({"count": len(data), "results": data}, json_dumps_params={"ensure_ascii": False, "indent": 2})


@require_GET
def metrics(request):
    queryset = FitnessTest.objects.select_related("student").all()
    local_user_id = request.GET.get("local_user_id")
    metric_type = request.GET.get("metric_type")

    if local_user_id:
        queryset = queryset.filter(student__local_code=local_user_id)

    rows = []
    for test in queryset:
        for metric in fitness_test_to_metrics(test):
            if metric_type and metric["metric_type"] != metric_type:
                continue
            rows.append(metric)

    return JsonResponse({"count": len(rows), "results": rows}, json_dumps_params={"ensure_ascii": False, "indent": 2})


@require_GET
def permissions(request):
    queryset = DisclosurePermission.objects.select_related("student").all()
    status_value = request.GET.get("status")
    open_to_offers = _parse_bool(request.GET.get("open_to_offers"))

    if status_value:
        queryset = queryset.filter(status=status_value)
    if open_to_offers is not None:
        queryset = queryset.filter(can_be_found=open_to_offers)

    data = [permission_to_dict(item) for item in queryset]
    return JsonResponse({"count": len(data), "results": data}, json_dumps_params={"ensure_ascii": False, "indent": 2})


@require_GET
def global_export(request):
    students_qs = Student.objects.select_related("section", "section__school", "permission").prefetch_related(
        "attendance_records", "fitness_tests"
    )
    data = [student_to_dict(item, include_nested=True) for item in students_qs]
    return JsonResponse(
        {
            "source": SOURCE_ID,
            "description": "Единый экспорт данных клиента в формате, близком к глобальной схеме медиатора.",
            "count": len(data),
            "results": data,
        },
        json_dumps_params={"ensure_ascii": False, "indent": 2},
    )



def dashboard(request):
    context = {
        "schools_count": School.objects.count(),
        "sections_count": Section.objects.count(),
        "students_count": Student.objects.count(),
        "attendance_count": AttendanceRecord.objects.count(),
        "fitness_tests_count": FitnessTest.objects.count(),
        "permissions_count": DisclosurePermission.objects.count(),
        "recent_students": Student.objects.select_related("section", "section__school").order_by("-id")[:5],
        "recent_attendance": AttendanceRecord.objects.select_related("student").order_by("-training_date", "-id")[:5],
        "recent_tests": FitnessTest.objects.select_related("student").order_by("-tested_at", "-id")[:5],
    }
    return render(request, "school_source/dashboard.html", context)


def _save_form_or_render(request, form_class, template_name, context):
    if request.method == "POST":
        form = form_class(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Запись успешно добавлена.")
            return redirect(request.path)
        messages.error(request, "Проверьте заполнение формы.")
    else:
        form = form_class()

    context["form"] = form
    return render(request, template_name, context)


def schools_page(request):
    schools_qs = School.objects.order_by("name")
    return _save_form_or_render(
        request,
        SchoolForm,
        "school_source/schools.html",
        {"schools": schools_qs},
    )


def sections_page(request):
    sections_qs = Section.objects.select_related("school").order_by("name")
    return _save_form_or_render(
        request,
        SectionForm,
        "school_source/sections.html",
        {"sections": sections_qs},
    )


def students_page(request):
    students_qs = Student.objects.select_related("section", "section__school", "permission").order_by("full_name")
    return _save_form_or_render(
        request,
        StudentForm,
        "school_source/students.html",
        {"students": students_qs},
    )


def attendance_page(request):
    attendance_qs = AttendanceRecord.objects.select_related("student", "student__section").order_by("-training_date", "-id")
    return _save_form_or_render(
        request,
        AttendanceRecordForm,
        "school_source/attendance.html",
        {"attendance_records": attendance_qs},
    )


def fitness_tests_page(request):
    tests_qs = FitnessTest.objects.select_related("student", "student__section").order_by("-tested_at", "-id")
    return _save_form_or_render(
        request,
        FitnessTestForm,
        "school_source/fitness_tests.html",
        {"fitness_tests": tests_qs},
    )


def permissions_page(request):
    permissions_qs = DisclosurePermission.objects.select_related("student", "student__section").order_by("student__full_name")
    return _save_form_or_render(
        request,
        DisclosurePermissionForm,
        "school_source/permissions.html",
        {"permissions": permissions_qs},
    )
