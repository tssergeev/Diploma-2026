from datetime import date, datetime, timedelta
from decimal import Decimal, InvalidOperation

from django.db.models import Count, Q
from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.utils import timezone
from django.views.decorators.http import require_GET

from .forms import ActivityForm, ConsentForm, HealthMetricForm, MemberForm, OrganizationForm
from .models import Activity, Consent, HealthMetric, Member, Organization


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


def _age(member):
    today = date.today()
    return today.year - member.birth_date.year - (
        (today.month, today.day) < (member.birth_date.month, member.birth_date.day)
    )


def _iso_date(value):
    return value.isoformat() if value else None


def _iso_datetime(value):
    if not value:
        return None
    return timezone.localtime(value).isoformat()


def organization_to_dict(organization):
    return {
        "organization_id": organization.id,
        "organization_name": organization.name,
        "organization_type": organization.organization_type,
        "city": organization.city,
    }


def activity_to_dict(activity):
    return {
        "activity_id": activity.activity_id,
        "local_user_id": activity.member.local_id,
        "activity_date": _iso_date(activity.activity_date),
        "activity_type": activity.activity_type,
        "duration_minutes": activity.duration_minutes,
        "intensity": activity.intensity,
        "calories": activity.calories,
    }


def metric_to_dict(metric):
    return {
        "metric_id": metric.metric_id,
        "local_user_id": metric.member.local_id,
        "metric_type": metric.metric_type,
        "metric_value": float(metric.metric_value),
        "unit": metric.unit,
        "measured_at": _iso_datetime(metric.measured_at),
    }


def consent_to_dict(consent):
    return {
        "local_user_id": consent.member.local_id,
        "open_to_offers": consent.open_to_offers,
        "visible_data_categories": consent.visible_data_categories,
        "allowed_organization_types": consent.allowed_organization_types,
        "granted_at": _iso_date(consent.granted_at),
        "expires_at": _iso_date(consent.expires_at),
        "status": consent.status,
    }


def member_to_dict(member, include_nested=False):
    data = {
        "source": "fitness_club_client_1",
        "local_user_id": member.local_id,
        "full_name": member.full_name,
        "birth_date": _iso_date(member.birth_date),
        "age": _age(member),
        "gender": member.gender,
        "phone": member.phone,
        "email": member.email,
        "city": member.city,
        "sport_type": member.sport_type,
        "training_level": member.training_level,
        "organization": organization_to_dict(member.organization),
        "consent": consent_to_dict(member.consent) if hasattr(member, "consent") else None,
    }

    if include_nested:
        data["activities"] = [activity_to_dict(item) for item in member.activities.all()]
        data["health_metrics"] = [metric_to_dict(item) for item in member.metrics.all()]

    return data


@require_GET
def status(request):
    return JsonResponse(
        {
            "service": "fitness_club_client_1",
            "role": "local_data_source",
            "description": "Первый клиент: источник данных фитнес-клуба для сервера-медиатора",
            "database": "sqlite",
            "members": Member.objects.count(),
            "activities": Activity.objects.count(),
            "health_metrics": HealthMetric.objects.count(),
            "consents": Consent.objects.count(),
        },
        json_dumps_params={"ensure_ascii": False, "indent": 2},
    )


@require_GET
def schema(request):
    return JsonResponse(
        {
            "source_id": "fitness_club_client_1",
            "source_type": "relational_database",
            "local_entities": {
                "member": [
                    "local_id",
                    "full_name",
                    "birth_date",
                    "gender",
                    "phone",
                    "email",
                    "city",
                    "sport_type",
                    "training_level",
                    "organization_id",
                ],
                "activity": [
                    "activity_id",
                    "member_id",
                    "activity_date",
                    "activity_type",
                    "duration_minutes",
                    "intensity",
                    "calories",
                ],
                "health_metric": [
                    "metric_id",
                    "member_id",
                    "metric_type",
                    "metric_value",
                    "unit",
                    "measured_at",
                ],
                "consent": [
                    "member_id",
                    "open_to_offers",
                    "visible_data_categories",
                    "allowed_organization_types",
                    "granted_at",
                    "expires_at",
                    "status",
                ],
            },
            "mapping_to_global_schema": {
                "member.local_id": "User.local_id",
                "member.full_name": "User.full_name",
                "member.birth_date": "User.birth_date",
                "member.gender": "User.gender",
                "activity.activity_date": "Activity.activity_date",
                "activity.activity_type": "Activity.activity_type",
                "health_metric.metric_type": "HealthMetric.metric_type",
                "health_metric.metric_value": "HealthMetric.metric_value",
                "consent.open_to_offers": "Consent.open_to_offers",
                "consent.status": "Consent.status",
            },
        },
        json_dumps_params={"ensure_ascii": False, "indent": 2},
    )


@require_GET
def organizations(request):
    data = [organization_to_dict(item) for item in Organization.objects.all()]
    return JsonResponse({"count": len(data), "results": data}, json_dumps_params={"ensure_ascii": False, "indent": 2})


@require_GET
def members(request):
    queryset = Member.objects.select_related("organization", "consent").prefetch_related("activities", "metrics")

    gender = request.GET.get("gender")
    city = request.GET.get("city")
    training_level = request.GET.get("training_level")
    activity_type = request.GET.get("activity_type")
    metric_type = request.GET.get("metric_type")
    open_to_offers = _parse_bool(request.GET.get("open_to_offers"))
    min_age = _parse_int(request.GET.get("min_age"))
    max_age = _parse_int(request.GET.get("max_age"))
    min_visits = _parse_int(request.GET.get("min_visits"))
    period_days = _parse_int(request.GET.get("period_days"), 90)
    min_metric_value = _parse_decimal(request.GET.get("min_metric_value"))
    max_metric_value = _parse_decimal(request.GET.get("max_metric_value"))

    if gender:
        queryset = queryset.filter(gender=gender)
    if city:
        queryset = queryset.filter(city__iexact=city)
    if training_level:
        queryset = queryset.filter(training_level__iexact=training_level)
    if open_to_offers is not None:
        queryset = queryset.filter(consent__open_to_offers=open_to_offers, consent__status="active")

    today = date.today()
    if min_age is not None:
        latest_birth_date = date(today.year - min_age, today.month, today.day)
        queryset = queryset.filter(birth_date__lte=latest_birth_date)
    if max_age is not None:
        earliest_birth_date = date(today.year - max_age - 1, today.month, today.day) + timedelta(days=1)
        queryset = queryset.filter(birth_date__gte=earliest_birth_date)

    if activity_type:
        queryset = queryset.filter(activities__activity_type=activity_type)

    if min_visits is not None:
        start_date = today - timedelta(days=period_days)
        activity_filter = Q(activities__activity_date__gte=start_date)
        if activity_type:
            activity_filter &= Q(activities__activity_type=activity_type)
        queryset = queryset.annotate(visits_count=Count("activities", filter=activity_filter)).filter(visits_count__gte=min_visits)

    if metric_type:
        queryset = queryset.filter(metrics__metric_type=metric_type)
    if min_metric_value is not None:
        queryset = queryset.filter(metrics__metric_value__gte=min_metric_value)
    if max_metric_value is not None:
        queryset = queryset.filter(metrics__metric_value__lte=max_metric_value)

    queryset = queryset.distinct().order_by("full_name")
    include_nested = _parse_bool(request.GET.get("include_nested")) or False
    data = [member_to_dict(member, include_nested=include_nested) for member in queryset]

    return JsonResponse(
        {
            "count": len(data),
            "filters": request.GET.dict(),
            "results": data,
        },
        json_dumps_params={"ensure_ascii": False, "indent": 2},
    )


@require_GET
def member_detail(request, local_id):
    try:
        member = Member.objects.select_related("organization", "consent").prefetch_related("activities", "metrics").get(local_id=local_id)
    except Member.DoesNotExist:
        return JsonResponse({"detail": "Пользователь не найден"}, status=404, json_dumps_params={"ensure_ascii": False})

    return JsonResponse(member_to_dict(member, include_nested=True), json_dumps_params={"ensure_ascii": False, "indent": 2})


@require_GET
def activities(request):
    queryset = Activity.objects.select_related("member").all()
    local_user_id = request.GET.get("local_user_id")
    activity_type = request.GET.get("activity_type")
    date_from = request.GET.get("date_from")
    date_to = request.GET.get("date_to")

    if local_user_id:
        queryset = queryset.filter(member__local_id=local_user_id)
    if activity_type:
        queryset = queryset.filter(activity_type=activity_type)
    if date_from:
        queryset = queryset.filter(activity_date__gte=date_from)
    if date_to:
        queryset = queryset.filter(activity_date__lte=date_to)

    data = [activity_to_dict(item) for item in queryset]
    return JsonResponse({"count": len(data), "results": data}, json_dumps_params={"ensure_ascii": False, "indent": 2})


@require_GET
def metrics(request):
    queryset = HealthMetric.objects.select_related("member").all()
    local_user_id = request.GET.get("local_user_id")
    metric_type = request.GET.get("metric_type")

    if local_user_id:
        queryset = queryset.filter(member__local_id=local_user_id)
    if metric_type:
        queryset = queryset.filter(metric_type=metric_type)

    data = [metric_to_dict(item) for item in queryset]
    return JsonResponse({"count": len(data), "results": data}, json_dumps_params={"ensure_ascii": False, "indent": 2})


@require_GET
def consents(request):
    queryset = Consent.objects.select_related("member").all()
    status_value = request.GET.get("status")
    open_to_offers = _parse_bool(request.GET.get("open_to_offers"))

    if status_value:
        queryset = queryset.filter(status=status_value)
    if open_to_offers is not None:
        queryset = queryset.filter(open_to_offers=open_to_offers)

    data = [consent_to_dict(item) for item in queryset]
    return JsonResponse({"count": len(data), "results": data}, json_dumps_params={"ensure_ascii": False, "indent": 2})


def dashboard(request):
    context = {
        "members_count": Member.objects.count(),
        "activities_count": Activity.objects.count(),
        "metrics_count": HealthMetric.objects.count(),
        "consents_count": Consent.objects.count(),
        "organizations_count": Organization.objects.count(),
        "recent_members": Member.objects.select_related("organization").order_by("-created_at")[:5],
        "recent_activities": Activity.objects.select_related("member").order_by("-activity_date", "-id")[:5],
        "recent_metrics": HealthMetric.objects.select_related("member").order_by("-measured_at", "-id")[:5],
    }
    return render(request, "club_source/dashboard.html", context)


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


def organizations_page(request):
    organizations_qs = Organization.objects.order_by("name")
    return _save_form_or_render(
        request,
        OrganizationForm,
        "club_source/organizations.html",
        {"organizations": organizations_qs},
    )


def members_page(request):
    members_qs = Member.objects.select_related("organization", "consent").order_by("full_name")
    return _save_form_or_render(
        request,
        MemberForm,
        "club_source/members.html",
        {"members": members_qs},
    )


def activities_page(request):
    activities_qs = Activity.objects.select_related("member").order_by("-activity_date", "-id")
    return _save_form_or_render(
        request,
        ActivityForm,
        "club_source/activities.html",
        {"activities": activities_qs},
    )


def metrics_page(request):
    metrics_qs = HealthMetric.objects.select_related("member").order_by("-measured_at", "-id")
    return _save_form_or_render(
        request,
        HealthMetricForm,
        "club_source/metrics.html",
        {"metrics": metrics_qs},
    )


def consents_page(request):
    consents_qs = Consent.objects.select_related("member").order_by("member__full_name")
    return _save_form_or_render(
        request,
        ConsentForm,
        "club_source/consents.html",
        {"consents": consents_qs},
    )
