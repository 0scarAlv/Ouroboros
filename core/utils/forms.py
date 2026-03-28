from django import forms

""" General inputs forms whit bootstrap"""

class TextInput(forms.TextInput):
    def __init__(self, **kwargs):
        kwargs.setdefault("attrs", {})
        kwargs["attrs"].setdefault("class", "form-control")
        super().__init__(**kwargs)


class PasswordInput(forms.PasswordInput):
    def __init__(self, **kwargs):
        kwargs.setdefault("attrs", {})
        kwargs["attrs"].setdefault("class", "form-control")
        super().__init__(**kwargs)


class EmailInput(forms.EmailInput):
    def __init__(self, **kwargs):
        kwargs.setdefault("attrs", {})
        kwargs["attrs"].setdefault("class", "form-control")
        super().__init__(**kwargs)


class NumberInput(forms.NumberInput):
    def __init__(self, **kwargs):
        kwargs.setdefault("attrs", {})
        kwargs["attrs"].setdefault("class", "form-control")
        super().__init__(**kwargs)


class DecimalInput(forms.NumberInput):
    def __init__(self, **kwargs):
        kwargs.setdefault("attrs", {})
        kwargs["attrs"].setdefault("class", "form-control")
        kwargs["attrs"].setdefault("step", "0.01")
        super().__init__(**kwargs)


class DateInput(forms.DateInput):
    def __init__(self, **kwargs):
        kwargs.setdefault("attrs", {})
        kwargs["attrs"].setdefault("class", "form-control")
        kwargs["attrs"].setdefault("type", "date")
        super().__init__(**kwargs)


class DateTimeInput(forms.DateTimeInput):
    def __init__(self, **kwargs):
        kwargs.setdefault("attrs", {})
        kwargs["attrs"].setdefault("class", "form-control")
        kwargs["attrs"].setdefault("type", "datetime-local")
        super().__init__(**kwargs)


class CheckboxInput(forms.CheckboxInput):
    def __init__(self, **kwargs):
        kwargs.setdefault("attrs", {})
        kwargs["attrs"].setdefault("class", "form-check-input")
        super().__init__(**kwargs)


class Select(forms.Select):
    def __init__(self, **kwargs):
        kwargs.setdefault("attrs", {})
        kwargs["attrs"].setdefault("class", "form-select")
        super().__init__(**kwargs)


class Textarea(forms.Textarea):
    def __init__(self, **kwargs):
        kwargs.setdefault("attrs", {})
        kwargs["attrs"].setdefault("class", "form-control")
        kwargs["attrs"].setdefault("rows", "3")
        super().__init__(**kwargs)

"""Error codes"""

DEFAULT_ERROR_CODES = {
    "required":       "FIELD_REQUIRED",
    "invalid":        "FIELD_INVALID",
    "max_length":     "FIELD_TOO_LONG",
    "min_length":     "FIELD_TOO_SHORT",
    "max_value":      "FIELD_TOO_LARGE",
    "min_value":      "FIELD_TOO_SMALL",
    "invalid_choice": "FIELD_INVALID_CHOICE",
    "unique":         "FIELD_NOT_UNIQUE",
}


class BaseForm(forms.Form):
    """
    Project base form.
    Replaces Django default error messages with translatable error codes.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field in self.fields.values():
            for key, code in DEFAULT_ERROR_CODES.items():
                field.error_messages[key] = code