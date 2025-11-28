from django import template
from django.forms import Form

register = template.Library()


@register.filter(name="get_item")
def get_item(obj, key):
    """
    Accesses an item by key on any object, supporting standard dicts
    and specialized objects like Django Forms (which use obj[key] for lookup).
    """
    if isinstance(obj, Form):
        # Use square bracket lookup for Django Form objects
        return obj[key]

    # Fallback for standard dictionaries or objects with .get()
    try:
        return obj.get(key)
    except AttributeError:
        # Final attempt for general objects using square bracket lookup
        return obj[key]


@register.filter
def quantity_tagname(template_id):
    return f"template_{template_id}_quantity"


@register.filter
def names_tagname(template_id):
    return f"template_{template_id}_names"
