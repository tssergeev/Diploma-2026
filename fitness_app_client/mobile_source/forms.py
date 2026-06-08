from django import forms

from .models import FitnessDocument


TEXT_CLASS = "form-control"
SELECT_CLASS = "form-select"
CHECK_CLASS = "form-check-input"


GENDER_CHOICES = [
    ("female", "Женский"),
    ("male", "Мужской"),
    ("unknown", "Не указано"),
]

LEVEL_CHOICES = [
    ("beginner", "Начальный"),
    ("intermediate", "Средний"),
    ("advanced", "Продвинутый"),
]

ORG_TYPE_CHOICES = [
    ("fitness_app", "Фитнес-приложение"),
    ("wearable_platform", "Носимое устройство"),
    ("mobile_health_platform", "Мобильная health-платформа"),
]

INTENSITY_CHOICES = [
    ("low", "Низкая"),
    ("medium", "Средняя"),
    ("high", "Высокая"),
]

CONSENT_STATUS_CHOICES = [
    ("active", "Активно"),
    ("expired", "Истекло"),
    ("revoked", "Отозвано"),
]


class StyledFormMixin:
    def _apply_styles(self):
        for field in self.fields.values():
            widget = field.widget
            if isinstance(widget, forms.CheckboxInput):
                widget.attrs.setdefault("class", CHECK_CLASS)
            elif isinstance(widget, forms.Select):
                widget.attrs.setdefault("class", SELECT_CLASS)
            else:
                widget.attrs.setdefault("class", TEXT_CLASS)


def _split_list(value):
    if not value:
        return []
    return [item.strip() for item in str(value).split(",") if item.strip()]


class FitnessDocumentForm(StyledFormMixin, forms.Form):
    local_id = forms.CharField(label="Локальный ID", max_length=64)
    full_name = forms.CharField(label="ФИО", max_length=255)
    birth_date = forms.DateField(label="Дата рождения", widget=forms.DateInput(attrs={"type": "date"}))
    gender = forms.ChoiceField(label="Пол", choices=GENDER_CHOICES)
    phone = forms.CharField(label="Телефон", max_length=32, required=False)
    email = forms.EmailField(label="Email", required=False)
    city = forms.CharField(label="Город", max_length=120, required=False)
    sport_type = forms.CharField(label="Вид активности", max_length=120, required=False)
    training_level = forms.ChoiceField(label="Уровень подготовки", choices=LEVEL_CHOICES)
    org_id = forms.CharField(label="ID источника", max_length=64, initial="fitapp_manual")
    org_name = forms.CharField(label="Название источника", max_length=255, initial="Manual Fitness App")
    org_type = forms.ChoiceField(label="Тип источника", choices=ORG_TYPE_CHOICES)
    source_system = forms.CharField(label="Система", max_length=120, initial="manual_fitness_app")
    schema_version = forms.CharField(label="Версия схемы", max_length=32, initial="1.0")
    device = forms.CharField(label="Устройство", max_length=120, required=False, initial="manual_entry")
    open_to_offers = forms.BooleanField(label="Открыт к предложениям", required=False, initial=True)
    visible_categories = forms.CharField(label="Видимые категории", required=False, initial="activity, heart_rate, hrv")
    allowed_organization_types = forms.CharField(label="Допустимые типы организаций", required=False, initial="fitness_club, personal_trainer")
    granted_at = forms.DateField(label="Дата согласия", widget=forms.DateInput(attrs={"type": "date"}), required=False)
    expires_at = forms.DateField(label="Срок действия", widget=forms.DateInput(attrs={"type": "date"}), required=False)
    consent_status = forms.ChoiceField(label="Статус согласия", choices=CONSENT_STATUS_CHOICES, initial="active")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._apply_styles()

    def clean_local_id(self):
        local_id = self.cleaned_data["local_id"].strip()
        if FitnessDocument.objects.filter(local_id=local_id).exists():
            raise forms.ValidationError("Такой локальный ID уже существует.")
        return local_id

    def save(self):
        data = self.cleaned_data
        local_id = data["local_id"]
        document = {
            "userId": local_id,
            "profile": {
                "fullName": data["full_name"],
                "birthDate": data["birth_date"].isoformat(),
                "gender": data["gender"],
                "phone": data.get("phone") or "",
                "email": data.get("email") or "",
                "city": data.get("city") or "",
                "sportType": data.get("sport_type") or "",
                "trainingLevel": data["training_level"],
            },
            "organization": {
                "orgId": data["org_id"],
                "name": data["org_name"],
                "type": data["org_type"],
                "city": data.get("city") or "",
            },
            "activities": [],
            "healthMetrics": {},
            "consent": {
                "openToOffers": bool(data.get("open_to_offers")),
                "visibleDataCategories": _split_list(data.get("visible_categories")),
                "allowedOrganizationTypes": _split_list(data.get("allowed_organization_types")),
                "grantedAt": data["granted_at"].isoformat() if data.get("granted_at") else None,
                "expiresAt": data["expires_at"].isoformat() if data.get("expires_at") else None,
                "status": data["consent_status"],
            },
            "sourceMeta": {
                "sourceSystem": data["source_system"],
                "schemaVersion": data["schema_version"],
                "device": data.get("device") or "manual_entry",
            },
        }
        return FitnessDocument.objects.create(local_id=local_id, document=document)


class FitnessDocumentChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        doc = obj.document if isinstance(obj.document, dict) else {}
        profile = doc.get("profile", {}) if isinstance(doc.get("profile", {}), dict) else {}
        return f"{obj.local_id} — {profile.get('fullName') or obj.local_id}"


class ActivityAppendForm(StyledFormMixin, forms.Form):
    document = FitnessDocumentChoiceField(label="Документ пользователя", queryset=FitnessDocument.objects.all())
    activity_id = forms.CharField(label="ID активности", max_length=64)
    activity_date = forms.DateField(label="Дата", widget=forms.DateInput(attrs={"type": "date"}))
    activity_type = forms.CharField(label="Тип активности", max_length=120)
    duration_min = forms.IntegerField(label="Длительность, мин", min_value=1)
    intensity = forms.ChoiceField(label="Интенсивность", choices=INTENSITY_CHOICES)
    calories = forms.IntegerField(label="Калории", min_value=0, required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["document"].queryset = FitnessDocument.objects.order_by("local_id")
        self._apply_styles()

    def save(self):
        item = self.cleaned_data["document"]
        doc = item.document if isinstance(item.document, dict) else {}
        doc.setdefault("activities", [])
        doc["activities"].append(
            {
                "activityId": self.cleaned_data["activity_id"],
                "date": self.cleaned_data["activity_date"].isoformat(),
                "type": self.cleaned_data["activity_type"],
                "durationMin": self.cleaned_data["duration_min"],
                "intensity": self.cleaned_data["intensity"],
                "calories": self.cleaned_data.get("calories"),
            }
        )
        item.document = doc
        item.save(update_fields=["document", "updated_at"])
        return item


class HealthMetricsForm(StyledFormMixin, forms.Form):
    document = FitnessDocumentChoiceField(label="Документ пользователя", queryset=FitnessDocument.objects.all())
    measured_at = forms.DateTimeField(label="Дата и время измерения", widget=forms.DateTimeInput(attrs={"type": "datetime-local"}), required=False)
    resting_pulse = forms.IntegerField(label="Пульс в покое", min_value=1, required=False)
    avg_training_pulse = forms.IntegerField(label="Средний пульс тренировки", min_value=1, required=False)
    hrv = forms.FloatField(label="ВСР", min_value=0, required=False)
    sleep_duration = forms.FloatField(label="Сон, часов", min_value=0, required=False)
    sleep_quality = forms.IntegerField(label="Качество сна", min_value=0, max_value=100, required=False)
    weight = forms.FloatField(label="Вес, кг", min_value=0, required=False)
    stress = forms.IntegerField(label="Стресс", min_value=0, max_value=100, required=False)
    vo2max = forms.FloatField(label="VO2max", min_value=0, required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["document"].queryset = FitnessDocument.objects.order_by("local_id")
        self._apply_styles()

    def clean(self):
        cleaned = super().clean()
        metric_fields = [
            "resting_pulse",
            "avg_training_pulse",
            "hrv",
            "sleep_duration",
            "sleep_quality",
            "weight",
            "stress",
            "vo2max",
        ]
        if not any(cleaned.get(field) is not None for field in metric_fields):
            raise forms.ValidationError("Укажите хотя бы один показатель.")
        return cleaned

    def save(self):
        item = self.cleaned_data["document"]
        doc = item.document if isinstance(item.document, dict) else {}
        metrics = doc.setdefault("healthMetrics", {})
        measured_at = self.cleaned_data.get("measured_at")
        measured_at_value = measured_at.isoformat(timespec="minutes") if measured_at else None

        resting = self.cleaned_data.get("resting_pulse")
        avg_training = self.cleaned_data.get("avg_training_pulse")
        if resting is not None or avg_training is not None:
            heart_rate = metrics.setdefault("heartRate", {})
            if resting is not None:
                heart_rate["resting"] = resting
            if avg_training is not None:
                heart_rate["avgTraining"] = avg_training
            if measured_at_value:
                heart_rate["measuredAt"] = measured_at_value

        if self.cleaned_data.get("hrv") is not None:
            metrics["hrv"] = {"value": self.cleaned_data["hrv"], "unit": "ms"}
            if measured_at_value:
                metrics["hrv"]["measuredAt"] = measured_at_value

        sleep_duration = self.cleaned_data.get("sleep_duration")
        sleep_quality = self.cleaned_data.get("sleep_quality")
        if sleep_duration is not None or sleep_quality is not None:
            sleep = metrics.setdefault("sleep", {})
            if sleep_duration is not None:
                sleep["durationHours"] = sleep_duration
            if sleep_quality is not None:
                sleep["qualityScore"] = sleep_quality
            if measured_at_value:
                sleep["measuredAt"] = measured_at_value

        if self.cleaned_data.get("weight") is not None:
            metrics["weight"] = {"value": self.cleaned_data["weight"], "unit": "kg"}
            if measured_at_value:
                metrics["weight"]["measuredAt"] = measured_at_value

        if self.cleaned_data.get("stress") is not None:
            metrics["stress"] = {"score": self.cleaned_data["stress"]}
            if measured_at_value:
                metrics["stress"]["measuredAt"] = measured_at_value

        if self.cleaned_data.get("vo2max") is not None:
            metrics["vo2max"] = {"value": self.cleaned_data["vo2max"], "unit": "ml/kg/min"}
            if measured_at_value:
                metrics["vo2max"]["measuredAt"] = measured_at_value

        item.document = doc
        item.save(update_fields=["document", "updated_at"])
        return item


class ConsentUpdateForm(StyledFormMixin, forms.Form):
    document = FitnessDocumentChoiceField(label="Документ пользователя", queryset=FitnessDocument.objects.all())
    open_to_offers = forms.BooleanField(label="Открыт к предложениям", required=False, initial=True)
    visible_categories = forms.CharField(label="Видимые категории", required=False, initial="activity, heart_rate, hrv")
    allowed_organization_types = forms.CharField(label="Допустимые типы организаций", required=False, initial="fitness_club, personal_trainer")
    granted_at = forms.DateField(label="Дата согласия", widget=forms.DateInput(attrs={"type": "date"}), required=False)
    expires_at = forms.DateField(label="Срок действия", widget=forms.DateInput(attrs={"type": "date"}), required=False)
    status = forms.ChoiceField(label="Статус", choices=CONSENT_STATUS_CHOICES, initial="active")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["document"].queryset = FitnessDocument.objects.order_by("local_id")
        self._apply_styles()

    def save(self):
        item = self.cleaned_data["document"]
        doc = item.document if isinstance(item.document, dict) else {}
        doc["consent"] = {
            "openToOffers": bool(self.cleaned_data.get("open_to_offers")),
            "visibleDataCategories": _split_list(self.cleaned_data.get("visible_categories")),
            "allowedOrganizationTypes": _split_list(self.cleaned_data.get("allowed_organization_types")),
            "grantedAt": self.cleaned_data["granted_at"].isoformat() if self.cleaned_data.get("granted_at") else None,
            "expiresAt": self.cleaned_data["expires_at"].isoformat() if self.cleaned_data.get("expires_at") else None,
            "status": self.cleaned_data["status"],
        }
        item.document = doc
        item.save(update_fields=["document", "updated_at"])
        return item
