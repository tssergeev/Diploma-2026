from django.utils import timezone


def date_to_iso(value):
    return value.isoformat() if value else None


def datetime_to_iso(value):
    if not value:
        return None
    return timezone.localtime(value).isoformat()


def activity_to_dict(item):
    return {
        "id": item.id,
        "source_id": item.source.source_id,
        "local_activity_id": item.local_activity_id,
        "activity_date": date_to_iso(item.activity_date),
        "activity_type": item.activity_type,
        "duration_minutes": item.duration_minutes,
        "intensity": item.intensity,
        "calories": item.calories,
    }


def metric_to_dict(item):
    return {
        "id": item.id,
        "source_id": item.source.source_id,
        "local_metric_id": item.local_metric_id,
        "metric_type": item.metric_type,
        "metric_value": item.metric_value,
        "unit": item.unit,
        "measured_at": datetime_to_iso(item.measured_at),
    }


def consent_to_dict(item):
    return {
        "id": item.id,
        "source_id": item.source.source_id,
        "open_to_offers": item.open_to_offers,
        "status": item.status,
        "visible_data_categories": item.visible_data_categories,
        "allowed_organization_types": item.allowed_organization_types,
        "granted_at": date_to_iso(item.granted_at),
        "expires_at": date_to_iso(item.expires_at),
    }


def source_to_dict(item, include_mapping=False):
    data = {
        "id": item.id,
        "source_id": item.source_id,
        "name": item.name,
        "source_type": item.source_type,
        "base_url": item.base_url,
        "status_endpoint": item.status_endpoint,
        "schema_endpoint": item.schema_endpoint,
        "users_endpoint": item.users_endpoint,
        "timeout_seconds": item.timeout_seconds,
        "is_active": item.is_active,
        "description": item.description,
        "last_sync_at": datetime_to_iso(item.last_sync_at),
        "last_error": item.last_error,
    }
    if include_mapping:
        data["mapping_config"] = item.mapping_config
    return data


def profile_to_dict(item, include_nested=False):
    data = {
        "global_id": str(item.global_id),
        "full_name": item.full_name,
        "birth_date": date_to_iso(item.birth_date),
        "age": item.age,
        "gender": item.gender,
        "phone": item.phone,
        "email": item.email,
        "city": item.city,
        "sport_type": item.sport_type,
        "training_level": item.training_level,
        "organization": {
            "organization_name": item.organization_name,
            "organization_type": item.organization_type,
            "city": item.organization_city,
        },
        "open_to_offers": item.open_to_offers,
        "consent_status": item.consent_status,
        "visible_data_categories": item.visible_data_categories,
        "allowed_organization_types": item.allowed_organization_types,
        "source_summary": item.source_summary,
        "updated_at": datetime_to_iso(item.updated_at),
    }

    if include_nested:
        data["activities"] = [activity_to_dict(activity) for activity in item.activities.select_related("source").all()]
        data["health_metrics"] = [metric_to_dict(metric) for metric in item.health_metrics.select_related("source").all()]
        data["consents"] = [consent_to_dict(consent) for consent in item.consents.select_related("source").all()]
        data["source_links"] = [
            {
                "source_id": link.source.source_id,
                "source_name": link.source.name,
                "source_type": link.source.source_type,
                "local_user_id": link.local_user_id,
                "fingerprint": link.fingerprint,
            }
            for link in item.source_links.select_related("source").all()
        ]
    return data


def offer_to_dict(item):
    return {
        "id": item.id,
        "global_id": str(item.profile_id),
        "profile_name": item.profile.full_name,
        "trainer_name": item.trainer_name,
        "organization_name": item.organization_name,
        "message": item.message,
        "status": item.status,
        "created_at": datetime_to_iso(item.created_at),
        "updated_at": datetime_to_iso(item.updated_at),
    }


def audit_to_dict(item):
    return {
        "id": item.id,
        "created_at": datetime_to_iso(item.created_at),
        "action": item.action,
        "source_id": item.source.source_id if item.source else None,
        "profile_id": str(item.profile_id) if item.profile_id else None,
        "details": item.details,
    }
