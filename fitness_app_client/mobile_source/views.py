from datetime import date, datetime, timedelta

from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.views.decorators.http import require_GET

from .forms import ActivityAppendForm, ConsentUpdateForm, FitnessDocumentForm, HealthMetricsForm
from .models import FitnessDocument


SOURCE_ID = "fitness_app_client_3"


def _parse_bool(value):
    if value is None:
        return None
    return str(value).strip().lower() in {"1", "true", "yes", "да", "on"}


def _parse_int(value, default=None):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _parse_float(value, default=None):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _parse_date(value):
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00")).date()
    except ValueError:
        try:
            return date.fromisoformat(str(value))
        except ValueError:
            return None


def _age_from_birth_date(value):
    birth_date = _parse_date(value)
    if not birth_date:
        return None
    today = date.today()
    return today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))


def _get_document_data(item):
    return item.document if isinstance(item.document, dict) else {}


def _profile(doc):
    return doc.get("profile", {}) if isinstance(doc.get("profile", {}), dict) else {}


def _organization(doc):
    return doc.get("organization", {}) if isinstance(doc.get("organization", {}), dict) else {}


def _consent(doc):
    return doc.get("consent", {}) if isinstance(doc.get("consent", {}), dict) else {}


def _activities(doc):
    activities = doc.get("activities", [])
    return activities if isinstance(activities, list) else []


def _health_metrics(doc):
    metrics = doc.get("healthMetrics", {})
    return metrics if isinstance(metrics, dict) else {}


def organization_to_dict(doc):
    organization = _organization(doc)
    return {
        "organization_id": organization.get("orgId"),
        "organization_name": organization.get("name"),
        "organization_type": organization.get("type"),
        "city": organization.get("city"),
    }


def consent_to_dict(doc, local_user_id):
    consent = _consent(doc)
    return {
        "local_user_id": local_user_id,
        "open_to_offers": bool(consent.get("openToOffers", False)),
        "visible_data_categories": consent.get("visibleDataCategories", []),
        "allowed_organization_types": consent.get("allowedOrganizationTypes", []),
        "granted_at": consent.get("grantedAt"),
        "expires_at": consent.get("expiresAt"),
        "status": consent.get("status", "unknown"),
    }


def activity_to_dict(activity, local_user_id):
    return {
        "activity_id": activity.get("activityId"),
        "local_user_id": local_user_id,
        "activity_date": activity.get("date"),
        "activity_type": activity.get("type"),
        "duration_minutes": activity.get("durationMin"),
        "intensity": activity.get("intensity"),
        "calories": activity.get("calories"),
        "source_format": "nested_json_array",
    }


def _metric_record(local_user_id, metric_type, value, unit, measured_at=None):
    if value is None:
        return None
    return {
        "metric_id": f"{local_user_id}_{metric_type}_{measured_at or 'latest'}",
        "local_user_id": local_user_id,
        "metric_type": metric_type,
        "metric_value": value,
        "unit": unit,
        "measured_at": measured_at,
        "source_format": "nested_json_object",
    }


def metric_records(doc, local_user_id):
    metrics = _health_metrics(doc)
    records = []

    heart_rate = metrics.get("heartRate", {}) if isinstance(metrics.get("heartRate", {}), dict) else {}
    records.append(_metric_record(local_user_id, "heart_rate_resting", heart_rate.get("resting"), "bpm", heart_rate.get("measuredAt")))
    records.append(_metric_record(local_user_id, "heart_rate_avg_training", heart_rate.get("avgTraining"), "bpm", heart_rate.get("measuredAt")))

    hrv = metrics.get("hrv", {}) if isinstance(metrics.get("hrv", {}), dict) else {}
    records.append(_metric_record(local_user_id, "hrv", hrv.get("value"), hrv.get("unit", "ms"), hrv.get("measuredAt")))

    sleep = metrics.get("sleep", {}) if isinstance(metrics.get("sleep", {}), dict) else {}
    records.append(_metric_record(local_user_id, "sleep_duration", sleep.get("durationHours"), "hours", sleep.get("measuredAt")))
    records.append(_metric_record(local_user_id, "sleep_quality", sleep.get("qualityScore"), "score", sleep.get("measuredAt")))

    weight = metrics.get("weight", {}) if isinstance(metrics.get("weight", {}), dict) else {}
    records.append(_metric_record(local_user_id, "weight", weight.get("value"), weight.get("unit", "kg"), weight.get("measuredAt")))

    stress = metrics.get("stress", {}) if isinstance(metrics.get("stress", {}), dict) else {}
    records.append(_metric_record(local_user_id, "stress_score", stress.get("score"), "score", stress.get("measuredAt")))

    vo2max = metrics.get("vo2max", {}) if isinstance(metrics.get("vo2max", {}), dict) else {}
    records.append(_metric_record(local_user_id, "vo2max", vo2max.get("value"), vo2max.get("unit", "ml/kg/min"), vo2max.get("measuredAt")))

    return [record for record in records if record is not None]


def user_to_dict(item, include_nested=False, include_raw=False):
    doc = _get_document_data(item)
    profile = _profile(doc)
    local_user_id = doc.get("userId") or item.local_id

    data = {
        "source": SOURCE_ID,
        "local_user_id": local_user_id,
        "full_name": profile.get("fullName"),
        "birth_date": profile.get("birthDate"),
        "age": _age_from_birth_date(profile.get("birthDate")),
        "gender": profile.get("gender"),
        "phone": profile.get("phone"),
        "email": profile.get("email"),
        "city": profile.get("city"),
        "sport_type": profile.get("sportType"),
        "training_level": profile.get("trainingLevel"),
        "organization": organization_to_dict(doc),
        "consent": consent_to_dict(doc, local_user_id),
        "source_meta": doc.get("sourceMeta", {}),
    }

    if include_nested:
        data["activities"] = [activity_to_dict(activity, local_user_id) for activity in _activities(doc)]
        data["health_metrics"] = metric_records(doc, local_user_id)

    if include_raw:
        data["raw_document"] = doc

    return data


def _matches_user_filters(item, request):
    doc = _get_document_data(item)
    profile = _profile(doc)
    consent = _consent(doc)
    local_user_id = doc.get("userId") or item.local_id

    gender = request.GET.get("gender")
    city = request.GET.get("city")
    training_level = request.GET.get("training_level")
    open_to_offers = _parse_bool(request.GET.get("open_to_offers"))
    min_age = _parse_int(request.GET.get("min_age"))
    max_age = _parse_int(request.GET.get("max_age"))
    activity_type = request.GET.get("activity_type")
    min_activities = _parse_int(request.GET.get("min_activities"))
    period_days = _parse_int(request.GET.get("period_days"), 90)
    metric_type = request.GET.get("metric_type")
    min_metric_value = _parse_float(request.GET.get("min_metric_value"))
    max_metric_value = _parse_float(request.GET.get("max_metric_value"))

    if gender and profile.get("gender") != gender:
        return False
    if city and str(profile.get("city", "")).lower() != city.lower():
        return False
    if training_level and str(profile.get("trainingLevel", "")).lower() != training_level.lower():
        return False

    if open_to_offers is not None:
        is_open = bool(consent.get("openToOffers", False)) and consent.get("status") == "active"
        if is_open != open_to_offers:
            return False

    age = _age_from_birth_date(profile.get("birthDate"))
    if min_age is not None and (age is None or age < min_age):
        return False
    if max_age is not None and (age is None or age > max_age):
        return False

    user_activities = _activities(doc)
    if activity_type:
        user_activities = [item for item in user_activities if item.get("type") == activity_type]
        if not user_activities:
            return False

    if min_activities is not None:
        start_date = date.today() - timedelta(days=period_days)
        recent_activities = [item for item in user_activities if (_parse_date(item.get("date")) or date.min) >= start_date]
        if len(recent_activities) < min_activities:
            return False

    if metric_type or min_metric_value is not None or max_metric_value is not None:
        records = metric_records(doc, local_user_id)
        if metric_type:
            records = [item for item in records if item["metric_type"] == metric_type]
        if min_metric_value is not None:
            records = [item for item in records if _parse_float(item.get("metric_value"), float("-inf")) >= min_metric_value]
        if max_metric_value is not None:
            records = [item for item in records if _parse_float(item.get("metric_value"), float("inf")) <= max_metric_value]
        if not records:
            return False

    return True


@require_GET
def status(request):
    documents = FitnessDocument.objects.all()
    total_activities = 0
    total_metrics = 0
    active_consents = 0

    for item in documents:
        doc = _get_document_data(item)
        total_activities += len(_activities(doc))
        total_metrics += len(metric_records(doc, item.local_id))
        current_consent = _consent(doc)
        if current_consent.get("openToOffers") and current_consent.get("status") == "active":
            active_consents += 1

    return JsonResponse(
        {
            "service": SOURCE_ID,
            "role": "local_data_source",
            "description": "Третий клиент: источник данных фитнес-приложения с JSON-документами",
            "database": "sqlite_with_json_documents",
            "source_type": "document_oriented_source",
            "documents": documents.count(),
            "activities": total_activities,
            "health_metrics": total_metrics,
            "active_open_to_offers_consents": active_consents,
        },
        json_dumps_params={"ensure_ascii": False, "indent": 2},
    )


@require_GET
def schema(request):
    return JsonResponse(
        {
            "source_id": SOURCE_ID,
            "source_type": "document_oriented_database",
            "local_format": "JSON document stored in SQLite JSONField",
            "root_entity": "FitnessDocument",
            "document_structure": {
                "userId": "локальный идентификатор пользователя",
                "profile": "анкетные данные пользователя",
                "organization": "организация или приложение-источник",
                "activities": "массив тренировок и активностей",
                "healthMetrics": "вложенный объект с биометрическими показателями",
                "consent": "настройки согласия и открытости к предложениям",
                "sourceMeta": "метаданные источника и версия схемы",
            },
            "mapping_to_global_schema": {
                "userId": "User.local_id",
                "profile.fullName": "User.full_name",
                "profile.birthDate": "User.birth_date",
                "profile.gender": "User.gender",
                "profile.city": "User.city",
                "organization.orgId": "Organization.organization_id",
                "organization.name": "Organization.organization_name",
                "activities[].activityId": "Activity.activity_id",
                "activities[].date": "Activity.activity_date",
                "activities[].type": "Activity.activity_type",
                "activities[].durationMin": "Activity.duration_minutes",
                "healthMetrics.heartRate.resting": "HealthMetric.heart_rate_resting",
                "healthMetrics.heartRate.avgTraining": "HealthMetric.heart_rate_avg_training",
                "healthMetrics.hrv.value": "HealthMetric.hrv",
                "healthMetrics.sleep.durationHours": "HealthMetric.sleep_duration",
                "healthMetrics.sleep.qualityScore": "HealthMetric.sleep_quality",
                "healthMetrics.weight.value": "HealthMetric.weight",
                "consent.openToOffers": "Consent.open_to_offers",
                "consent.visibleDataCategories": "Consent.visible_data_categories",
                "consent.allowedOrganizationTypes": "Consent.allowed_organization_types",
                "consent.status": "Consent.status",
            },
        },
        json_dumps_params={"ensure_ascii": False, "indent": 2},
    )


@require_GET
def documents(request):
    results = []
    for item in FitnessDocument.objects.all():
        results.append(
            {
                "local_id": item.local_id,
                "updated_at": item.updated_at.isoformat(),
                "document": _get_document_data(item),
            }
        )
    return JsonResponse({"count": len(results), "results": results}, json_dumps_params={"ensure_ascii": False, "indent": 2})


@require_GET
def document_detail(request, local_id):
    try:
        item = FitnessDocument.objects.get(local_id=local_id)
    except FitnessDocument.DoesNotExist:
        return JsonResponse({"detail": "Документ не найден"}, status=404, json_dumps_params={"ensure_ascii": False})

    return JsonResponse(
        {
            "local_id": item.local_id,
            "updated_at": item.updated_at.isoformat(),
            "document": _get_document_data(item),
        },
        json_dumps_params={"ensure_ascii": False, "indent": 2},
    )


@require_GET
def users(request):
    include_nested = _parse_bool(request.GET.get("include_nested")) or False
    include_raw = _parse_bool(request.GET.get("include_raw")) or False
    results = []

    for item in FitnessDocument.objects.all():
        if _matches_user_filters(item, request):
            results.append(user_to_dict(item, include_nested=include_nested, include_raw=include_raw))

    return JsonResponse(
        {
            "count": len(results),
            "source": SOURCE_ID,
            "results": results,
        },
        json_dumps_params={"ensure_ascii": False, "indent": 2},
    )


@require_GET
def user_detail(request, local_id):
    try:
        item = FitnessDocument.objects.get(local_id=local_id)
    except FitnessDocument.DoesNotExist:
        return JsonResponse({"detail": "Пользователь не найден"}, status=404, json_dumps_params={"ensure_ascii": False})

    return JsonResponse(user_to_dict(item, include_nested=True, include_raw=True), json_dumps_params={"ensure_ascii": False, "indent": 2})


@require_GET
def activities(request):
    local_user_id = request.GET.get("local_user_id")
    activity_type = request.GET.get("activity_type")
    results = []

    queryset = FitnessDocument.objects.all()
    if local_user_id:
        queryset = queryset.filter(local_id=local_user_id)

    for item in queryset:
        doc = _get_document_data(item)
        user_id = doc.get("userId") or item.local_id
        for activity in _activities(doc):
            if activity_type and activity.get("type") != activity_type:
                continue
            results.append(activity_to_dict(activity, user_id))

    return JsonResponse({"count": len(results), "results": results}, json_dumps_params={"ensure_ascii": False, "indent": 2})


@require_GET
def metrics(request):
    local_user_id = request.GET.get("local_user_id")
    metric_type = request.GET.get("metric_type")
    min_metric_value = _parse_float(request.GET.get("min_metric_value"))
    max_metric_value = _parse_float(request.GET.get("max_metric_value"))
    results = []

    queryset = FitnessDocument.objects.all()
    if local_user_id:
        queryset = queryset.filter(local_id=local_user_id)

    for item in queryset:
        doc = _get_document_data(item)
        user_id = doc.get("userId") or item.local_id
        for metric in metric_records(doc, user_id):
            value = _parse_float(metric.get("metric_value"))
            if metric_type and metric.get("metric_type") != metric_type:
                continue
            if min_metric_value is not None and (value is None or value < min_metric_value):
                continue
            if max_metric_value is not None and (value is None or value > max_metric_value):
                continue
            results.append(metric)

    return JsonResponse({"count": len(results), "results": results}, json_dumps_params={"ensure_ascii": False, "indent": 2})


@require_GET
def consents(request):
    open_to_offers = _parse_bool(request.GET.get("open_to_offers"))
    status_filter = request.GET.get("status")
    results = []

    for item in FitnessDocument.objects.all():
        doc = _get_document_data(item)
        user_id = doc.get("userId") or item.local_id
        consent_data = consent_to_dict(doc, user_id)
        if open_to_offers is not None and consent_data["open_to_offers"] != open_to_offers:
            continue
        if status_filter and consent_data["status"] != status_filter:
            continue
        results.append(consent_data)

    return JsonResponse({"count": len(results), "results": results}, json_dumps_params={"ensure_ascii": False, "indent": 2})


def _display_name(item):
    doc = _get_document_data(item)
    profile = _profile(doc)
    return profile.get("fullName") or item.local_id


def _flatten_activities(queryset):
    rows = []
    for item in queryset:
        doc = _get_document_data(item)
        local_user_id = doc.get("userId") or item.local_id
        for activity in _activities(doc):
            row = activity_to_dict(activity, local_user_id)
            row["full_name"] = _display_name(item)
            rows.append(row)
    return sorted(rows, key=lambda item: item.get("activity_date") or "", reverse=True)


def _flatten_metrics(queryset):
    rows = []
    for item in queryset:
        doc = _get_document_data(item)
        local_user_id = doc.get("userId") or item.local_id
        for metric in metric_records(doc, local_user_id):
            metric["full_name"] = _display_name(item)
            rows.append(metric)
    return sorted(rows, key=lambda item: item.get("measured_at") or "", reverse=True)


def _flatten_consents(queryset):
    rows = []
    for item in queryset:
        doc = _get_document_data(item)
        local_user_id = doc.get("userId") or item.local_id
        consent_data = consent_to_dict(doc, local_user_id)
        consent_data["full_name"] = _display_name(item)
        rows.append(consent_data)
    return rows


def dashboard(request):
    documents_qs = FitnessDocument.objects.order_by("-updated_at")
    activities_rows = _flatten_activities(documents_qs)
    metrics_rows = _flatten_metrics(documents_qs)
    consent_rows = _flatten_consents(documents_qs)
    context = {
        "documents_count": documents_qs.count(),
        "activities_count": len(activities_rows),
        "metrics_count": len(metrics_rows),
        "active_consents_count": len([item for item in consent_rows if item["open_to_offers"] and item["status"] == "active"]),
        "recent_documents": documents_qs[:5],
        "recent_activities": activities_rows[:5],
        "recent_metrics": metrics_rows[:5],
    }
    return render(request, "mobile_source/dashboard.html", context)


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


def documents_page(request):
    documents_qs = FitnessDocument.objects.order_by("local_id")
    return _save_form_or_render(
        request,
        FitnessDocumentForm,
        "mobile_source/documents.html",
        {"documents": documents_qs},
    )


def profiles_page(request):
    documents_qs = FitnessDocument.objects.order_by("local_id")
    profiles = [user_to_dict(item, include_nested=False, include_raw=False) for item in documents_qs]
    return render(request, "mobile_source/profiles.html", {"profiles": profiles})


def activities_page(request):
    documents_qs = FitnessDocument.objects.order_by("local_id")
    return _save_form_or_render(
        request,
        ActivityAppendForm,
        "mobile_source/activities.html",
        {"activities_rows": _flatten_activities(documents_qs)},
    )


def metrics_page(request):
    documents_qs = FitnessDocument.objects.order_by("local_id")
    return _save_form_or_render(
        request,
        HealthMetricsForm,
        "mobile_source/metrics.html",
        {"metrics_rows": _flatten_metrics(documents_qs)},
    )


def consents_page(request):
    documents_qs = FitnessDocument.objects.order_by("local_id")
    return _save_form_or_render(
        request,
        ConsentUpdateForm,
        "mobile_source/consents.html",
        {"consent_rows": _flatten_consents(documents_qs)},
    )
