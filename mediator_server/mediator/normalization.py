from datetime import date, datetime
import re

from django.utils import timezone


EMPTY_VALUES = {None, "", "null", "None", "undefined"}


def clean_text(value):
    if value in EMPTY_VALUES:
        return ""
    return str(value).strip()


def only_digits(value):
    return "".join(ch for ch in clean_text(value) if ch.isdigit())


def parse_date(value):
    if value in EMPTY_VALUES:
        return None
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    if isinstance(value, datetime):
        return value.date()
    text = clean_text(value).replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(text).date()
    except ValueError:
        pass
    for fmt in ("%d.%m.%Y", "%Y/%m/%d", "%d-%m-%Y"):
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue
    return None


def parse_datetime(value):
    if value in EMPTY_VALUES:
        return None
    if isinstance(value, datetime):
        dt = value
    else:
        text = clean_text(value).replace("Z", "+00:00")
        try:
            dt = datetime.fromisoformat(text)
        except ValueError:
            parsed_date = parse_date(text)
            if not parsed_date:
                return None
            dt = datetime.combine(parsed_date, datetime.min.time())
    if timezone.is_naive(dt):
        return timezone.make_aware(dt, timezone.get_current_timezone())
    return dt


def to_int(value):
    if value in EMPTY_VALUES:
        return None
    try:
        return int(float(str(value).replace(",", ".")))
    except (TypeError, ValueError):
        return None


def to_float(value):
    if value in EMPTY_VALUES:
        return None
    try:
        return float(str(value).replace(",", "."))
    except (TypeError, ValueError):
        return None


def calculate_age(birth_date):
    if not birth_date:
        return None
    today = date.today()
    return today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))



def make_json_safe(value):
    """Рекурсивно приводит значения к формату, который можно сохранить в JSONField."""
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, dict):
        return {str(key): make_json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [make_json_safe(item) for item in value]
    return value

def normalize_gender(value):
    text = clean_text(value).lower()
    if text in {"m", "м", "male", "муж", "мужской"}:
        return "male"
    if text in {"f", "ж", "female", "жен", "женский"}:
        return "female"
    return text


def normalize_metric_type(value):
    text = clean_text(value).lower().strip()
    aliases = {
        "hr": "heart_rate",
        "pulse": "heart_rate",
        "пульс": "heart_rate",
        "resting_pulse": "heart_rate_resting",
        "resting_heart_rate": "heart_rate_resting",
        "heart_rate_resting": "heart_rate_resting",
        "heart_rate_avg_training": "heart_rate_avg_training",
        "avg_training_hr": "heart_rate_avg_training",
        "hrv": "hrv",
        "вср": "hrv",
        "weight": "weight",
        "weight_kg": "weight",
        "sleep_quality": "sleep_quality",
        "sleep_duration": "sleep_duration",
        "endurance_score": "endurance_score",
        "flexibility_score": "flexibility_score",
        "stress_score": "stress_score",
        "vo2max": "vo2max",
    }
    return aliases.get(text, text)


def normalize_activity_type(value):
    text = clean_text(value).lower().strip()
    text = re.sub(r"\s+", "_", text)
    aliases = {
        "gym": "gym_workout",
        "gym_workout": "gym_workout",
        "силовая": "strength",
        "strength_training": "strength",
        "training": "training",
        "cardio": "cardio",
        "football": "football",
        "basketball": "basketball",
        "swimming": "swimming",
        "athletics": "athletics",
    }
    return aliases.get(text, text)


def build_fingerprint(full_name, birth_date=None, age=None, phone="", email=""):
    email = clean_text(email).lower()
    phone = only_digits(phone)
    name = re.sub(r"\s+", " ", clean_text(full_name).lower())
    if email:
        return f"email:{email}"
    if phone:
        return f"phone:{phone}"
    if birth_date:
        return f"name_birth:{name}:{birth_date.isoformat()}"
    if age is not None:
        return f"name_age:{name}:{age}"
    return f"name:{name}"


def normalize_activity(row):
    return {
        "local_activity_id": clean_text(row.get("activity_id") or row.get("record_code") or row.get("id")),
        "activity_date": parse_date(row.get("activity_date") or row.get("training_date") or row.get("date")),
        "activity_type": normalize_activity_type(row.get("activity_type") or row.get("training_type") or row.get("type")),
        "duration_minutes": to_int(row.get("duration_minutes") or row.get("durationMin") or row.get("duration")),
        "intensity": clean_text(row.get("intensity") or row.get("load_level")),
        "calories": to_int(row.get("calories")),
        "raw_data": row,
    }


def normalize_metric(row):
    return {
        "local_metric_id": clean_text(row.get("metric_id") or row.get("test_code") or row.get("id")),
        "metric_type": normalize_metric_type(row.get("metric_type")),
        "metric_value": to_float(row.get("metric_value")),
        "unit": clean_text(row.get("unit")),
        "measured_at": parse_datetime(row.get("measured_at") or row.get("tested_at") or row.get("date")),
        "raw_data": row,
    }


def normalize_consent(row):
    row = row or {}
    return {
        "open_to_offers": bool(row.get("open_to_offers", False)),
        "status": clean_text(row.get("status")),
        "visible_data_categories": row.get("visible_data_categories") or row.get("allowed_categories") or [],
        "allowed_organization_types": row.get("allowed_organization_types") or row.get("allowed_roles") or [],
        "granted_at": parse_date(row.get("granted_at") or row.get("granted_on")),
        "expires_at": parse_date(row.get("expires_at") or row.get("valid_until")),
        "raw_data": row,
    }


def normalize_user(source_id, row):
    organization = row.get("organization") or {}
    consent = normalize_consent(row.get("consent") or {})
    birth_date = parse_date(row.get("birth_date"))
    age = to_int(row.get("age")) or calculate_age(birth_date)

    local_user_id = clean_text(row.get("local_user_id") or row.get("local_code") or row.get("userId") or row.get("id"))
    full_name = clean_text(row.get("full_name") or row.get("fullName"))
    email = clean_text(row.get("email")).lower()
    phone = clean_text(row.get("phone"))

    normalized = {
        "source_id": source_id,
        "local_user_id": local_user_id,
        "full_name": full_name,
        "birth_date": birth_date,
        "age": age,
        "gender": normalize_gender(row.get("gender") or row.get("gender_source_value")),
        "phone": phone,
        "email": email,
        "city": clean_text(row.get("city")),
        "sport_type": clean_text(row.get("sport_type")),
        "training_level": clean_text(row.get("training_level")),
        "organization_name": clean_text(organization.get("organization_name") or organization.get("name")),
        "organization_type": clean_text(organization.get("organization_type") or organization.get("type")),
        "organization_city": clean_text(organization.get("city")),
        "consent": consent,
        "activities": [normalize_activity(item) for item in row.get("activities", [])],
        "health_metrics": [normalize_metric(item) for item in row.get("health_metrics", [])],
        "raw_data": row,
    }
    normalized["fingerprint"] = build_fingerprint(
        full_name=full_name,
        birth_date=birth_date,
        age=age,
        phone=phone,
        email=email,
    )
    return normalized
