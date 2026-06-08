from collections import defaultdict

from django.contrib import messages
from django.db.models import Avg, Count, Max, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_GET, require_POST

from .models import (
    ActivityRecord,
    AuditLog,
    ConsentRecord,
    DataSource,
    GlobalUserProfile,
    HealthMetricRecord,
    Offer,
)
from .services import check_sources, sync_all_sources, sync_source


def _percent(value, total):
    if not total:
        return 0
    return round((value / total) * 100, 1)


def _percent_width(value):
    """Return a CSS-safe percent value with a dot decimal separator.

    Django localizes floats in templates for the Russian locale, so a value
    such as 33.3 can be rendered as 33,3. CSS ignores width: 33,3%, and the
    bar expands to the default full width. Keeping a separate CSS value fixes
    the visual scale while preserving localized text output.
    """
    try:
        number = float(value or 0)
    except (TypeError, ValueError):
        number = 0
    number = max(0, min(100, number))
    return (f"{number:.1f}".rstrip("0").rstrip("."))


def _top_rows(queryset, field_name, label_field="label", value_field="value", limit=8):
    rows = (
        queryset.exclude(**{f"{field_name}__exact": ""})
        .values(field_name)
        .annotate(count=Count("id"))
        .order_by("-count", field_name)[:limit]
    )
    return [{label_field: item[field_name] or "Не указано", value_field: item["count"]} for item in rows]


def _bar_rows(rows, value_key="value"):
    max_value = max([row.get(value_key) or 0 for row in rows], default=0)
    for row in rows:
        percent = _percent(row.get(value_key) or 0, max_value)
        row["percent"] = percent
        row["percent_width"] = _percent_width(percent)
    return rows


def _latest_metric_values(profile):
    result = []
    seen = set()
    metrics = profile.health_metrics.select_related("source").order_by("metric_type", "-measured_at", "-id")
    for metric in metrics:
        if metric.metric_type in seen:
            continue
        seen.add(metric.metric_type)
        result.append(metric)
    return result[:8]


def _profile_cards(queryset):
    profiles = queryset.prefetch_related("activities", "health_metrics", "source_links__source", "consents")
    cards = []
    for profile in profiles:
        latest_activity = profile.activities.order_by("-activity_date", "-id").first()
        cards.append(
            {
                "profile": profile,
                "sources_count": profile.source_links.count(),
                "activities_count": profile.activities.count(),
                "metrics_count": profile.health_metrics.count(),
                "consents_count": profile.consents.count(),
                "latest_activity": latest_activity,
                "latest_metrics": _latest_metric_values(profile),
            }
        )
    return cards


@require_GET
def dashboard(request):
    total_profiles = GlobalUserProfile.objects.count()
    total_activities = ActivityRecord.objects.count()
    total_metrics = HealthMetricRecord.objects.count()
    total_sources = DataSource.objects.count()

    source_cards = []
    for source in DataSource.objects.annotate(
        profiles_count=Count("user_links", distinct=True),
        activities_count=Count("activities", distinct=True),
        metrics_count=Count("health_metrics", distinct=True),
        consents_count=Count("consents", distinct=True),
    ).order_by("name"):
        source_cards.append(
            {
                "source": source,
                "profiles_count": source.profiles_count,
                "activities_count": source.activities_count,
                "metrics_count": source.metrics_count,
                "consents_count": source.consents_count,
                "profile_percent": _percent(source.profiles_count, total_profiles),
                "profile_percent_width": _percent_width(_percent(source.profiles_count, total_profiles)),
            }
        )

    gender_rows = _bar_rows(
        [
            {"label": item["gender"] or "Не указано", "value": item["count"]}
            for item in GlobalUserProfile.objects.values("gender").annotate(count=Count("global_id")).order_by("-count")
        ]
    )
    activity_rows = _bar_rows(_top_rows(ActivityRecord.objects.all(), "activity_type"))
    metric_rows = _bar_rows(_top_rows(HealthMetricRecord.objects.all(), "metric_type"))

    metric_averages = (
        HealthMetricRecord.objects.exclude(metric_type="")
        .values("metric_type", "unit")
        .annotate(avg_value=Avg("metric_value"), count=Count("id"))
        .order_by("metric_type")[:10]
    )

    recent_profiles = GlobalUserProfile.objects.order_by("-updated_at")[:6]
    recent_audit = AuditLog.objects.select_related("source", "profile").order_by("-created_at")[:8]

    context = {
        "title": "Сводная статистика",
        "nav": "dashboard",
        "cards": {
            "sources": total_sources,
            "active_sources": DataSource.objects.filter(is_active=True).count(),
            "profiles": total_profiles,
            "open_profiles": GlobalUserProfile.objects.filter(open_to_offers=True).count(),
            "activities": total_activities,
            "metrics": total_metrics,
            "consents": ConsentRecord.objects.count(),
            "offers": Offer.objects.count(),
        },
        "source_cards": source_cards,
        "gender_rows": gender_rows,
        "activity_rows": activity_rows,
        "metric_rows": metric_rows,
        "metric_averages": metric_averages,
        "recent_profiles": recent_profiles,
        "recent_audit": recent_audit,
    }
    return render(request, "mediator/dashboard.html", context)


@require_POST
def sync_all_view(request):
    results = sync_all_sources(active_only=True)
    ok_count = sum(1 for item in results if item.get("status") == "ok")
    if ok_count:
        messages.success(request, f"Синхронизация выполнена: успешно {ok_count} из {len(results)} источников.")
    else:
        messages.error(request, "Синхронизация не получила данные. Проверьте, запущены ли клиенты.")
    return redirect(request.POST.get("next") or "dashboard")


@require_POST
def sync_source_view(request, source_id):
    source = get_object_or_404(DataSource, source_id=source_id)
    result = sync_source(source).as_dict()
    if result.get("status") == "ok":
        messages.success(request, f"Источник «{source.name}» синхронизирован: {result.get('fetched', 0)} записей.")
    else:
        messages.error(request, f"Источник «{source.name}» не синхронизирован: {result.get('error', 'ошибка')}.")
    return redirect(request.POST.get("next") or "client_detail", source_id=source.source_id)


@require_GET
def clients_stats(request):
    source_statuses = {item["source_id"]: item for item in check_sources()}
    sources = DataSource.objects.annotate(
        profiles_count=Count("user_links", distinct=True),
        activities_count=Count("activities", distinct=True),
        metrics_count=Count("health_metrics", distinct=True),
        consents_count=Count("consents", distinct=True),
        avg_age=Avg("user_links__profile__age"),
    ).order_by("name")

    rows = []
    for source in sources:
        linked_profiles = GlobalUserProfile.objects.filter(source_links__source=source).distinct()
        rows.append(
            {
                "source": source,
                "status": source_statuses.get(source.source_id, {}),
                "profiles_count": source.profiles_count,
                "open_profiles_count": linked_profiles.filter(open_to_offers=True).count(),
                "activities_count": source.activities_count,
                "metrics_count": source.metrics_count,
                "consents_count": source.consents_count,
                "avg_age": source.avg_age,
                "activity_types": _bar_rows(_top_rows(ActivityRecord.objects.filter(source=source), "activity_type", limit=5)),
                "metric_types": _bar_rows(_top_rows(HealthMetricRecord.objects.filter(source=source), "metric_type", limit=5)),
            }
        )

    return render(
        request,
        "mediator/clients_stats.html",
        {
            "title": "Статистика по клиентам",
            "nav": "clients",
            "rows": rows,
        },
    )


@require_GET
def client_detail(request, source_id):
    source = get_object_or_404(DataSource, source_id=source_id)
    profiles = GlobalUserProfile.objects.filter(source_links__source=source).distinct()
    profile_cards = _profile_cards(profiles.order_by("full_name")[:100])

    daily_activity = list(
        ActivityRecord.objects.filter(source=source, activity_date__isnull=False)
        .values("activity_date")
        .annotate(count=Count("id"))
        .order_by("-activity_date")[:12]
    )
    daily_activity = _bar_rows(daily_activity, value_key="count")

    metric_averages = (
        HealthMetricRecord.objects.filter(source=source)
        .exclude(metric_type="")
        .values("metric_type", "unit")
        .annotate(avg_value=Avg("metric_value"), count=Count("id"))
        .order_by("metric_type")
    )

    context = {
        "title": source.name,
        "nav": "clients",
        "source": source,
        "status": check_sources(),
        "stats": {
            "profiles": profiles.count(),
            "open_profiles": profiles.filter(open_to_offers=True).count(),
            "activities": ActivityRecord.objects.filter(source=source).count(),
            "metrics": HealthMetricRecord.objects.filter(source=source).count(),
            "consents": ConsentRecord.objects.filter(source=source).count(),
        },
        "activity_types": _bar_rows(_top_rows(ActivityRecord.objects.filter(source=source), "activity_type")),
        "metric_types": _bar_rows(_top_rows(HealthMetricRecord.objects.filter(source=source), "metric_type")),
        "metric_averages": metric_averages,
        "daily_activity": daily_activity,
        "profile_cards": profile_cards,
    }
    return render(request, "mediator/client_detail.html", context)


@require_GET
def people_stats(request):
    profiles = GlobalUserProfile.objects.all().order_by("full_name")

    q = request.GET.get("q", "").strip()
    source_id = request.GET.get("source_id", "").strip()
    open_to_offers = request.GET.get("open_to_offers", "").strip()
    metric_type = request.GET.get("metric_type", "").strip()
    activity_type = request.GET.get("activity_type", "").strip()

    if q:
        profiles = profiles.filter(
            Q(full_name__icontains=q)
            | Q(city__icontains=q)
            | Q(sport_type__icontains=q)
            | Q(organization_name__icontains=q)
            | Q(phone__icontains=q)
            | Q(email__icontains=q)
        )
    if source_id:
        profiles = profiles.filter(source_links__source__source_id=source_id)
    if open_to_offers == "yes":
        profiles = profiles.filter(open_to_offers=True)
    elif open_to_offers == "no":
        profiles = profiles.filter(open_to_offers=False)
    if metric_type:
        profiles = profiles.filter(health_metrics__metric_type=metric_type)
    if activity_type:
        profiles = profiles.filter(activities__activity_type=activity_type)

    profiles = profiles.distinct()

    context = {
        "title": "Персональная статистика",
        "nav": "people",
        "filters": {
            "q": q,
            "source_id": source_id,
            "open_to_offers": open_to_offers,
            "metric_type": metric_type,
            "activity_type": activity_type,
        },
        "sources": DataSource.objects.order_by("name"),
        "metric_types": HealthMetricRecord.objects.exclude(metric_type="").values_list("metric_type", flat=True).distinct().order_by("metric_type"),
        "activity_types": ActivityRecord.objects.exclude(activity_type="").values_list("activity_type", flat=True).distinct().order_by("activity_type"),
        "count": profiles.count(),
        "profile_cards": _profile_cards(profiles[:100]),
    }
    return render(request, "mediator/people_stats.html", context)


@require_GET
def person_detail(request, global_id):
    profile = get_object_or_404(
        GlobalUserProfile.objects.prefetch_related("activities__source", "health_metrics__source", "consents__source", "source_links__source", "offers"),
        global_id=global_id,
    )

    metrics_by_type = defaultdict(list)
    for metric in profile.health_metrics.select_related("source").order_by("metric_type", "-measured_at", "-id"):
        metrics_by_type[metric.metric_type].append(metric)

    activities_by_source = defaultdict(list)
    for activity in profile.activities.select_related("source").order_by("-activity_date", "-id"):
        activities_by_source[activity.source.name].append(activity)

    stats = {
        "sources": profile.source_links.count(),
        "activities": profile.activities.count(),
        "metrics": profile.health_metrics.count(),
        "consents": profile.consents.count(),
        "offers": profile.offers.count(),
        "latest_activity": profile.activities.order_by("-activity_date", "-id").first(),
        "latest_metric_date": profile.health_metrics.aggregate(value=Max("measured_at"))["value"],
    }

    context = {
        "title": profile.full_name,
        "nav": "people",
        "profile": profile,
        "stats": stats,
        "latest_metrics": _latest_metric_values(profile),
        "metrics_by_type": dict(metrics_by_type),
        "activities_by_source": dict(activities_by_source),
        "consents": profile.consents.select_related("source").order_by("source__name"),
        "source_links": profile.source_links.select_related("source").order_by("source__name"),
        "offers": profile.offers.order_by("-created_at"),
    }
    return render(request, "mediator/person_detail.html", context)
