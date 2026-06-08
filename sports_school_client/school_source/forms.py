import json

from django import forms
from django.core.exceptions import ValidationError

from .models import AttendanceRecord, DisclosurePermission, FitnessTest, School, Section, Student


class DateInput(forms.DateInput):
    input_type = "date"


class JsonListWidget(forms.Textarea):
    def format_value(self, value):
        if value in (None, ""):
            return "[]"
        if isinstance(value, str):
            return value
        return json.dumps(value, ensure_ascii=False, indent=2)


class JsonListField(forms.Field):
    widget = JsonListWidget

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


class SchoolForm(BaseStyledModelForm):
    class Meta:
        model = School
        fields = ["name", "organization_type", "city", "address"]


class SectionForm(BaseStyledModelForm):
    class Meta:
        model = Section
        fields = ["school", "code", "name", "sport_type", "coach_name", "age_group"]


class StudentForm(BaseStyledModelForm):
    class Meta:
        model = Student
        fields = [
            "local_code",
            "full_name",
            "birth_year",
            "gender_code",
            "parent_phone",
            "city",
            "section",
            "skill_level",
            "enrollment_date",
        ]
        widgets = {
            "enrollment_date": DateInput(),
        }


class AttendanceRecordForm(BaseStyledModelForm):
    class Meta:
        model = AttendanceRecord
        fields = [
            "student",
            "record_code",
            "training_date",
            "present",
            "training_type",
            "duration_minutes",
            "load_level",
        ]
        widgets = {
            "training_date": DateInput(),
        }


class FitnessTestForm(BaseStyledModelForm):
    class Meta:
        model = FitnessTest
        fields = [
            "student",
            "test_code",
            "tested_at",
            "resting_pulse",
            "height_cm",
            "weight_kg",
            "endurance_score",
            "flexibility_score",
            "notes",
        ]
        widgets = {
            "tested_at": DateInput(),
        }


class DisclosurePermissionForm(BaseStyledModelForm):
    allowed_categories = JsonListField(label="Открытые категории данных")
    allowed_roles = JsonListField(label="Разрешённые роли")

    class Meta:
        model = DisclosurePermission
        fields = [
            "student",
            "can_be_found",
            "allowed_categories",
            "allowed_roles",
            "granted_on",
            "valid_until",
            "status",
        ]
        widgets = {
            "granted_on": DateInput(),
            "valid_until": DateInput(),
        }
