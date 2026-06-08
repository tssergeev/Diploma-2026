import json
from datetime import date, timedelta

from django.db.models import Count, Q
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from .models import AuditLog, DataSource, GlobalUserProfile, Offer
from .serializers import audit_to_dict, offer_to_dict, profile_to_dict, source_to_dict
from .services import check_sources, sync_all_sources, sync_source


def _json_error(message, status=400, **extra):
    payload = {"detail": message}
    payload.update(extra)
    return JsonResponse(payload, status=status, json_dumps_params={"ensure_ascii": False, "indent": 2})


def _json_body(request):
    if not request.body:
        return {}
    try:
        return json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        return None


def _parse_bool(value):
    if value is None:
        return None
    return str(value).strip().lower() in {"1", "true", "yes", "да", "on"}


def _parse_int(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _parse_float(value):
    try:
        return float(str(value).replace(",", "."))
    except (TypeError, ValueError):
        return None


@require_GET
def status(request):
    return JsonResponse(
        {
            "service": "mediator_server",
            "role": "central_mediator",
            "description": "Центральный сервер-медиатор для интеграции трёх локальных клиентов",
            "sources": DataSource.objects.count(),
            "active_sources": DataSource.objects.filter(is_active=True).count(),
            "global_profiles": GlobalUserProfile.objects.count(),
            "offers": Offer.objects.count(),
            "api": {
                "sources": "/api/sources/",
                "check_sources": "/api/sources/check/",
                "sync": "/api/sync/",
                "users": "/api/users/?include_nested=true",
                "search": "/api/search/users/?open_to_offers=true&metric_type=hrv&min_metric_value=50",
                "offers": "/api/offers/",
            },
        },
        json_dumps_params={"ensure_ascii": False, "indent": 2},
    )


@require_http_methods(["GET", "POST"])
@csrf_exempt
def sources(request):
    if request.method == "GET":
        include_mapping = _parse_bool(request.GET.get("include_mapping")) or False
        items = DataSource.objects.all()
        return JsonResponse(
            {"count": items.count(), "results": [source_to_dict(item, include_mapping) for item in items]},
            json_dumps_params={"ensure_ascii": False, "indent": 2},
        )

    data = _json_body(request)
    if data is None:
        return _json_error("Некорректный JSON")

    required = ["source_id", "name", "source_type", "base_url", "users_endpoint"]
    missing = [field for field in required if not data.get(field)]
    if missing:
        return _json_error("Не заполнены обязательные поля", missing=missing)

    source, created = DataSource.objects.update_or_create(
        source_id=data["source_id"],
        defaults={
            "name": data["name"],
            "source_type": data["source_type"],
            "base_url": data["base_url"],
            "status_endpoint": data.get("status_endpoint", "status/"),
            "schema_endpoint": data.get("schema_endpoint", "schema/"),
            "users_endpoint": data["users_endpoint"],
            "timeout_seconds": data.get("timeout_seconds", 5),
            "is_active": data.get("is_active", True),
            "description": data.get("description", ""),
            "mapping_config": data.get("mapping_config", {}),
        },
    )
    AuditLog.objects.create(action="source_registered" if created else "source_updated", source=source, details=source_to_dict(source))
    return JsonResponse(
        {"created": created, "source": source_to_dict(source, include_mapping=True)},
        status=201 if created else 200,
        json_dumps_params={"ensure_ascii": False, "indent": 2},
    )


@require_GET
def source_detail(request, source_id):
    try:
        source = DataSource.objects.get(source_id=source_id)
    except DataSource.DoesNotExist:
        return _json_error("Источник не найден", status=404)
    return JsonResponse(source_to_dict(source, include_mapping=True), json_dumps_params={"ensure_ascii": False, "indent": 2})


@require_GET
def source_check(request):
    return JsonResponse({"results": check_sources()}, json_dumps_params={"ensure_ascii": False, "indent": 2})


@require_POST
@csrf_exempt
def sync(request):
    data = _json_body(request)
    if data is None:
        return _json_error("Некорректный JSON")

    source_id = data.get("source_id") if data else None
    if source_id:
        try:
            source = DataSource.objects.get(source_id=source_id)
        except DataSource.DoesNotExist:
            return _json_error("Источник не найден", status=404)
        result = sync_source(source).as_dict()
        return JsonResponse(result, json_dumps_params={"ensure_ascii": False, "indent": 2})

    results = sync_all_sources(active_only=True)
    return JsonResponse({"count": len(results), "results": results}, json_dumps_params={"ensure_ascii": False, "indent": 2})


def _filter_profiles(request):
    queryset = GlobalUserProfile.objects.prefetch_related("activities", "health_metrics", "consents", "source_links")

    gender = request.GET.get("gender")
    city = request.GET.get("city")
    sport_type = request.GET.get("sport_type")
    training_level = request.GET.get("training_level")
    open_to_offers = _parse_bool(request.GET.get("open_to_offers"))
    source_id = request.GET.get("source_id")
    q = request.GET.get("q")

    min_age = _parse_int(request.GET.get("min_age"))
    max_age = _parse_int(request.GET.get("max_age"))
    metric_type = request.GET.get("metric_type")
    min_metric_value = _parse_float(request.GET.get("min_metric_value"))
    max_metric_value = _parse_float(request.GET.get("max_metric_value"))
    activity_type = request.GET.get("activity_type")
    min_activities = _parse_int(request.GET.get("min_activities") or request.GET.get("min_visits"))
    period_days = _parse_int(request.GET.get("period_days")) or 90

    if q:
        queryset = queryset.filter(
            Q(full_name__icontains=q)
            | Q(phone__icontains=q)
            | Q(email__icontains=q)
            | Q(city__icontains=q)
            | Q(sport_type__icontains=q)
        )
    if gender:
        queryset = queryset.filter(gender=gender)
    if city:
        queryset = queryset.filter(city__iexact=city)
    if sport_type:
        queryset = queryset.filter(sport_type__iexact=sport_type)
    if training_level:
        queryset = queryset.filter(training_level__iexact=training_level)
    if open_to_offers is not None:
        queryset = queryset.filter(open_to_offers=open_to_offers)
    if source_id:
        queryset = queryset.filter(source_links__source__source_id=source_id)
    if min_age is not None:
        queryset = queryset.filter(age__gte=min_age)
    if max_age is not None:
        queryset = queryset.filter(age__lte=max_age)

    if metric_type:
        queryset = queryset.filter(health_metrics__metric_type=metric_type)
    if min_metric_value is not None:
        queryset = queryset.filter(health_metrics__metric_value__gte=min_metric_value)
    if max_metric_value is not None:
        queryset = queryset.filter(health_metrics__metric_value__lte=max_metric_value)

    if activity_type:
        queryset = queryset.filter(activities__activity_type=activity_type)

    if min_activities is not None:
        start_date = date.today() - timedelta(days=period_days)
        activity_filter = Q(activities__activity_date__gte=start_date)
        if activity_type:
            activity_filter &= Q(activities__activity_type=activity_type)
        queryset = queryset.annotate(activity_count=Count("activities", filter=activity_filter)).filter(
            activity_count__gte=min_activities
        )

    return queryset.distinct().order_by("full_name")


@require_GET
def users(request):
    include_nested = _parse_bool(request.GET.get("include_nested")) or False
    queryset = _filter_profiles(request)
    return JsonResponse(
        {
            "count": queryset.count(),
            "filters": request.GET.dict(),
            "results": [profile_to_dict(item, include_nested=include_nested) for item in queryset],
        },
        json_dumps_params={"ensure_ascii": False, "indent": 2},
    )


@require_GET
def user_detail(request, global_id):
    try:
        item = GlobalUserProfile.objects.prefetch_related("activities", "health_metrics", "consents", "source_links").get(
            global_id=global_id
        )
    except GlobalUserProfile.DoesNotExist:
        return _json_error("Глобальный профиль не найден", status=404)
    return JsonResponse(profile_to_dict(item, include_nested=True), json_dumps_params={"ensure_ascii": False, "indent": 2})


@require_GET
def audit(request):
    limit = _parse_int(request.GET.get("limit")) or 50
    rows = AuditLog.objects.select_related("source", "profile").all()[:limit]
    return JsonResponse({"count": len(rows), "results": [audit_to_dict(item) for item in rows]}, json_dumps_params={"ensure_ascii": False, "indent": 2})


@require_http_methods(["GET", "POST"])
@csrf_exempt
def offers(request):
    if request.method == "GET":
        rows = Offer.objects.select_related("profile").all()
        status_value = request.GET.get("status")
        if status_value:
            rows = rows.filter(status=status_value)
        return JsonResponse(
            {"count": rows.count(), "results": [offer_to_dict(item) for item in rows]},
            json_dumps_params={"ensure_ascii": False, "indent": 2},
        )

    data = _json_body(request)
    if data is None:
        return _json_error("Некорректный JSON")
    global_id = data.get("global_id")
    if not global_id:
        return _json_error("Нужно передать global_id")
    try:
        profile = GlobalUserProfile.objects.get(global_id=global_id)
    except GlobalUserProfile.DoesNotExist:
        return _json_error("Глобальный профиль не найден", status=404)
    if not profile.open_to_offers:
        return _json_error("Пользователь не открыт к предложениям")

    offer = Offer.objects.create(
        profile=profile,
        trainer_name=data.get("trainer_name", "Тренер"),
        organization_name=data.get("organization_name", ""),
        message=data.get("message", "Предложение персональной тренировки"),
    )
    AuditLog.objects.create(action="offer_created", profile=profile, details=offer_to_dict(offer))
    return JsonResponse(offer_to_dict(offer), status=201, json_dumps_params={"ensure_ascii": False, "indent": 2})
