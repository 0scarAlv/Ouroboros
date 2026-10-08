from django import template
from django.core.exceptions import FieldDoesNotExist
from django.db import models

from kernel.utils import format_boolean, format_date, format_datatime

register = template.Library()


@register.simple_tag
def field_label(model, name):
    """Column header for a field name, or the model name for '__str__'."""
    if name == '__str__':
        return model._meta.verbose_name
    try:
        return model._meta.get_field(name).verbose_name
    except FieldDoesNotExist:
        attr = getattr(model, name, None)
        return getattr(attr, 'short_description', name.replace('_', ' '))


@register.simple_tag
def field_value(obj, name):
    """Display value of a field: choice labels, readable dates and booleans."""
    if name == '__str__':
        return str(obj)
    try:
        field = obj._meta.get_field(name)
    except FieldDoesNotExist:
        value = getattr(obj, name, '')
        return value() if callable(value) else value
    if field.choices:
        return getattr(obj, f'get_{name}_display')()
    value = getattr(obj, name)
    if value is None:
        return ''
    if isinstance(field, models.BooleanField):
        return format_boolean(value, 'Sí', 'No')
    if isinstance(field, models.DateTimeField):
        return format_datatime(value)
    if isinstance(field, models.DateField):
        return format_date(value)
    return value


NUMERIC_FIELDS = (models.IntegerField, models.DecimalField, models.FloatField)


@register.simple_tag
def column_class(model, name):
    """'num' for numeric columns (right-aligned, tabular figures), else ''."""
    try:
        field = model._meta.get_field(name)
    except FieldDoesNotExist:
        return ''
    if isinstance(field, NUMERIC_FIELDS) and not field.choices and not field.is_relation:
        return 'num'
    return ''
