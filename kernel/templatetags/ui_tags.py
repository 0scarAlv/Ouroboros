from django import template

from kernel.constants.icons import ICON_SET

register = template.Library()


@register.filter
def known_icon(name):
    """The icon name if the vendored font has it, else '' (an unknown name renders as text)."""
    return name if name in ICON_SET else ''
