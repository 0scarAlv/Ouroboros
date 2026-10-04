from django import template
from django.utils.html import format_html, conditional_escape
from django.utils.safestring import mark_safe
from kernel.constants.general import ERROR_MESSAGES

register = template.Library()


@register.simple_tag
def render_field(field, label=None, placeholder=None):
    """
    Renders a form field as a complete Bootstrap 5 unit: label + input + error message block.
    """

    # Use custom label if provided, otherwise use the field's own label
    display_label = label or field.label or field.html_name

    # Inject placeholder into widget attrs if provided
    if placeholder:
        field.field.widget.attrs["placeholder"] = placeholder

    # Collect error messages for this field (may be multiple)
    errors_html = ""
    if field.errors:
        error_parts = []
        for error in field.errors:
            traslated = ERROR_MESSAGES.get(str(error), str(error))
            escaped = conditional_escape(traslated)
            error_parts.append(
                f'<div class="invalid-feedback d-block">{escaped}</div>'
            )
        errors_html = mark_safe("".join(error_parts))

        # Ensure is-invalid class is present on the widget
        current_class = field.field.widget.attrs.get("class", "")
        if "is-invalid" not in current_class:
            field.field.widget.attrs["class"] = current_class + " is-invalid"

    # Render the actual input widget
    widget_html = field.as_widget()

    return format_html(
        '<div class="mb-3">'
        '<label for="{}" class="form-label">{}</label>'
        '{}'
        '{}'
        '</div>',
        field.id_for_label,
        display_label,
        widget_html,
        errors_html,
    )