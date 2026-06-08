import json

from django import forms
from django.core.exceptions import ValidationError

from .models import Activity, Consent, HealthMetric, Member, Organization


class DateInput(forms.DateInput):
    input_type = "date"


class DateTimeInput(forms.DateTimeInput):
    input_type = "datetime-local"


class JsonListWidget(forms.Textarea):
    def format_value(self, value):
        if value in (None, ""):
            return "[]"
        if isinstance(value, str):
            return value
        return json.dumps(value, ensure_ascii=False, indent=2)


class JsonListField(forms.Field):
    widget = JsonListWidget

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("help_text", "Введите JSON-массив, например: [\"activity\", \"hrv\"]")
        super().__init__(*args, **kwargs)

    def to_python(self, value):
        if value in (None, ""):
            return []
        if isinstance(value, list):
            return value
        try:
            result = json.loads(value)
        except json.JSONDecodeError as exc:
            raise ValidationError("Введите корректный JSON-массив.") from exc
        if not isinstance(result, list):
            raise ValidationError("Значение должно быть JSON-массивом.")
        return result


class BaseStyledModelForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            css_class = "form-control"
            if isinstance(field.widget, forms.CheckboxInput):
                css_class = "form-check-input"
            elif isinstance(field.widget, forms.Select):
                css_class = "form-select"
            field.widget.attrs.setdefault("class", css_class)


class OrganizationForm(BaseStyledModelForm):
    class Meta:
        model = Organization
        fields = ["name", "organization_type", "city"]


class MemberForm(BaseStyledModelForm):
    class Meta:
        model = Member
        fields = [
            "local_id",
            "full_name",
            "birth_date",
            "gender",
            "phone",
            "email",
            "city",
            "sport_type",
            "training_level",
            "organization",
        ]
        widgets = {
            "birth_date": DateInput(),
        }


class ActivityForm(BaseStyledModelForm):
    class Meta:
        model = Activity
        fields = [
            "member",
            "activity_id",
            "activity_date",
            "activity_type",
            "duration_minutes",
            "intensity",
            "calories",
        ]
        widgets = {
            "activity_date": DateInput(),
        }


class HealthMetricForm(BaseStyledModelForm):
    measured_at = forms.DateTimeField(
        label="Время измерения",
        input_formats=["%Y-%m-%dT%H:%M", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M"],
        widget=DateTimeInput(format="%Y-%m-%dT%H:%M"),
    )

    class Meta:
        model = HealthMetric
        fields = [
            "member",
            "metric_id",
            "metric_type",
            "metric_value",
            "unit",
            "measured_at",
        ]


class ConsentForm(BaseStyledModelForm):
    visible_data_categories = JsonListField(label="Открытые категории данных")
    allowed_organization_types = JsonListField(label="Разрешённые типы организаций")

    class Meta:
        model = Consent
        fields = [
            "member",
            "open_to_offers",
            "visible_data_categories",
            "allowed_organization_types",
            "granted_at",
            "expires_at",
            "status",
        ]
        widgets = {
            "granted_at": DateInput(),
            "expires_at": DateInput(),
        }
