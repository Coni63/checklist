from django import template

register = template.Library()


@register.filter
def get_item(dictionary, key):
    """Permet de récupérer une valeur dans un dictionnaire à l'aide d'une clé."""
    return dictionary.get(key)
