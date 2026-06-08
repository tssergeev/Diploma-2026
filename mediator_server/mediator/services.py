from dataclasses import dataclass, field
from datetime import date

from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from .models import (
    ActivityRecord,
    AuditLog,
    ConsentRecord,
    DataSource,
    GlobalUserProfile,
    HealthMetricRecord,
    SourceUserLink,
)
from .normalization import clean_text, make_json_safe, normalize_user, only_digits
from .wrappers import get_wrapper
from .wrappers.base import WrapperError


@dataclass
class SyncResult:
    source_id: str
    loaded: int = 0
    created_profiles: int = 0
    updated_profiles: int = 0
    created_links: int = 0
    activities: int = 0
    metrics: int = 0
    errors: list = field(default_factory=list)

    def as_dict(self):
        return {
            "source_id": self.source_id,
            "status": "error" if self.errors else "ok",
            "fetched": self.loaded,
            "loaded": self.loaded,
            "created_profiles": self.created_profiles,
            "updated_profiles": self.updated_profiles,
            "created_links": self.created_links,
            "activities": self.activities,
            "metrics": self.metrics,
            "errors": self.errors,
        }


def _find_existing_profile(source, normalized):
    local_user_id = normalized["local_user_id"]
    if local_user_id:
        link = SourceUserLink.objects.select_related("profile").filter(source=source, local_user_id=local_user_id).first()
        if link:
            return link.profile

    email = normalized.get("email")
    if email:
        profile = GlobalUserProfile.objects.filter(email__iexact=email).first()
        if profile:
            return profile

    phone = only_digits(normalized.get("phone"))
    if phone:
        profiles = GlobalUserProfile.objects.exclude(phone="")
        for profile in profiles:
            if only_digits(profile.phone) == phone:
                return profile

    fingerprint = normalized.get("fingerprint")
    if fingerprint:
        link = SourceUserLink.objects.select_related("profile").filter(fingerprint=fingerprint).first()
        if link:
            return link.profile

    name = clean_text(normalized.get("full_name"))
    birth_date = normalized.get("birth_date")
    age = normalized.get("age")
    if name and birth_date:
        profile = GlobalUserProfile.objects.filter(full_name__iexact=name, birth_date=birth_date).first()
        if profile:
            return profile
    if name and age is not None:
        profile = GlobalUserProfile.objects.filter(full_name__iexact=name, age=age).first()
        if profile:
            return profile

    return None


def _merge_value(current, incoming):
    if incoming in (None, "", [], {}):
        return current
    return incoming


def _update_profile_fields(profile, normalized):
    profile.full_name = _merge_value(profile.full_name, normalized.get("full_name"))
    profile.birth_date = _merge_value(profile.birth_date, normalized.get("birth_date"))
    profile.age = _merge_value(profile.age, normalized.get("age"))
    profile.gender = _merge_value(profile.gender, normalized.get("gender"))
    profile.phone = _merge_value(profile.phone, normalized.get("phone"))
    profile.email = _merge_value(profile.email, normalized.get("email"))
    profile.city = _merge_value(profile.city, normalized.get("city"))
    profile.sport_type = _merge_value(profile.sport_type, normalized.get("sport_type"))
    profile.training_level = _merge_value(profile.training_level, normalized.get("training_level"))
    profile.organization_name = _merge_value(profile.organization_name, normalized.get("organization_name"))
    profile.organization_type = _merge_value(profile.organization_type, normalized.get("organization_type"))
    profile.organization_city = _merge_value(profile.organization_city, normalized.get("organization_city"))
    profile.raw_snapshot = make_json_safe(normalized)
    profile.save()


def _save_source_link(source, profile, normalized):
    local_user_id = normalized.get("local_user_id") or str(profile.global_id)
    link, created = SourceUserLink.objects.update_or_create(
        source=source,
        local_user_id=local_user_id,
        defaults={
            "profile": profile,
            "fingerprint": normalized.get("fingerprint", ""),
            "raw_data": make_json_safe(normalized.get("raw_data", {})),
        },
    )
    return link, created


def _replace_activities(source, profile, activities):
    ActivityRecord.objects.filter(source=source, profile=profile).delete()
    rows = []
    for item in activities:
        rows.append(
            ActivityRecord(
                source=source,
                profile=profile,
                local_activity_id=item.get("local_activity_id", ""),
                activity_date=item.get("activity_date"),
                activity_type=item.get("activity_type", ""),
                duration_minutes=item.get("duration_minutes"),
                intensity=item.get("intensity", ""),
                calories=item.get("calories"),
                raw_data=make_json_safe(item.get("raw_data", {})),
            )
        )
    ActivityRecord.objects.bulk_create(rows)
    return len(rows)


def _replace_metrics(source, profile, metrics):
    HealthMetricRecord.objects.filter(source=source, profile=profile).delete()
    rows = []
    for item in metrics:
        if not item.get("metric_type"):
            continue
        rows.append(
            HealthMetricRecord(
                source=source,
                profile=profile,
                local_metric_id=item.get("local_metric_id", ""),
                metric_type=item.get("metric_type", ""),
                metric_value=item.get("metric_value"),
                unit=item.get("unit", ""),
                measured_at=item.get("measured_at"),
                raw_data=make_json_safe(item.get("raw_data", {})),
            )
        )
    HealthMetricRecord.objects.bulk_create(rows)
    return len(rows)


def _save_consent(source, profile, consent):
    ConsentRecord.objects.update_or_create(
        profile=profile,
        source=source,
        defaults={
            "open_to_offers": consent.get("open_to_offers", False),
            "status": consent.get("status", ""),
            "visible_data_categories": consent.get("visible_data_categories", []),
            "allowed_organization_types": consent.get("allowed_organization_types", []),
            "granted_at": consent.get("granted_at"),
            "expires_at": consent.get("expires_at"),
            "raw_data": make_json_safe(consent.get("raw_data", {})),
        },
    )


def recalculate_profile_access(profile):
    consents = list(profile.consents.all())
    today = date.today()
    active_open = []
    statuses = []
    categories = set()
    allowed_types = set()

    for consent in consents:
        if consent.status:
            statuses.append(consent.status)
        not_expired = consent.expires_at is None or consent.expires_at >= today
        is_active = consent.status == "active" and consent.open_to_offers and not_expired
        if is_active:
            active_open.append(consent)
        for category in consent.visible_data_categories or []:
            categories.add(category)
        for organization_type in consent.allowed_organization_types or []:
            allowed_types.add(organization_type)

    profile.open_to_offers = bool(active_open)
    profile.consent_status = "active" if active_open else (statuses[0] if statuses else "unknown")
    profile.visible_data_categories = sorted(categories)
    profile.allowed_organization_types = sorted(allowed_types)
    profile.source_summary = [
        {
            "source_id": link.source.source_id,
            "source_name": link.source.name,
            "source_type": link.source.source_type,
            "local_user_id": link.local_user_id,
        }
        for link in profile.source_links.select_related("source").all()
    ]
    profile.save(update_fields=[
        "open_to_offers",
        "consent_status",
        "visible_data_categories",
        "allowed_organization_types",
        "source_summary",
        "updated_at",
    ])


def sync_source(source):
    result = SyncResult(source_id=source.source_id)
    wrapper = get_wrapper(source)

    try:
        rows = wrapper.fetch_users()
    except WrapperError as exc:
        source.last_error = str(exc)
        source.save(update_fields=["last_error", "updated_at"])
        result.errors.append(str(exc))
        AuditLog.objects.create(action="sync_source_failed", source=source, details=result.as_dict())
        return result

    result.loaded = len(rows)

    with transaction.atomic():
        for row in rows:
            normalized = normalize_user(source.source_id, row)
            profile = _find_existing_profile(source, normalized)
            created_profile = False

            if not profile:
                profile = GlobalUserProfile.objects.create(full_name=normalized.get("full_name") or "Без имени")
                created_profile = True
                result.created_profiles += 1
            else:
                result.updated_profiles += 1

            _update_profile_fields(profile, normalized)
            _, created_link = _save_source_link(source, profile, normalized)
            if created_link:
                result.created_links += 1

            result.activities += _replace_activities(source, profile, normalized.get("activities", []))
            result.metrics += _replace_metrics(source, profile, normalized.get("health_metrics", []))
            _save_consent(source, profile, normalized.get("consent", {}))
            recalculate_profile_access(profile)

            AuditLog.objects.create(
                action="profile_created" if created_profile else "profile_updated",
                source=source,
                profile=profile,
                details={"local_user_id": normalized.get("local_user_id"), "fingerprint": normalized.get("fingerprint")},
            )

    source.last_sync_at = timezone.now()
    source.last_error = ""
    source.save(update_fields=["last_sync_at", "last_error", "updated_at"])
    AuditLog.objects.create(action="sync_source_completed", source=source, details=result.as_dict())
    return result


def sync_all_sources(active_only=True):
    queryset = DataSource.objects.all()
    if active_only:
        queryset = queryset.filter(is_active=True)
    return [sync_source(source).as_dict() for source in queryset]


def check_sources():
    rows = []
    for source in DataSource.objects.all().order_by("name"):
        wrapper = get_wrapper(source)
        try:
            status = wrapper.fetch_status()
            error = ""
        except WrapperError as exc:
            status = None
            error = str(exc)
        rows.append({
            "source_id": source.source_id,
            "name": source.name,
            "source_type": source.source_type,
            "base_url": source.base_url,
            "is_active": source.is_active,
            "available": status is not None,
            "status": status,
            "error": error,
        })
    return rows
