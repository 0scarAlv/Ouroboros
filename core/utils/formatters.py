from django.utils import timezone

def format_datatime(value):
    """Format a datetime object to readable string."""
    if not value:
        return ''
    return value.strftime('%B %d, %Y %H:%M')

def format_date(value):
    """Format a date object to readable string."""
    if not value:
        return ''
    return value.strftime('%B %d, %Y')

def format_currency(value, symbol='$'):
    """Format a number as currency string."""
    if value is None:
        return ''
    return f"{symbol}{value:,.2f}"


def format_boolean(value, true_label='Yes', false_label='No'):
    """Format a boolean value to a human-readable string."""
    return true_label if value else false_label

