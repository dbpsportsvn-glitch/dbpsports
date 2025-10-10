from django import template

register = template.Library()

@register.filter
def currency_format(value):
    """Format number with comma separators"""
    if value is None:
        return "0"
    try:
        # Convert to float first, then format
        num = float(value)
        return f"{num:,.0f}"
    except (ValueError, TypeError):
        return "0"
