from datetime import timedelta

from django import template
from django.urls import reverse
from django.utils import timezone

register = template.Library()


@register.filter
def get_item(dictionary, key):
    """Permet de récupérer une valeur dans un dictionnaire à l'aide d'une clé."""
    return dictionary.get(key)


@register.filter
def smart_timesince(value):
    """
    Render timesince until 1 day then return a formatted date
    """
    if not value:
        return ""

    now = timezone.now()
    if value > now:
        # Si la date est dans le futur, on l'affiche telle quelle
        return value.strftime("%Y-%m-%d %H:%M:%S")

    time_difference = now - value

    # La condition est : si le temps écoulé est d'au moins 1 jour (86400 secondes)
    if time_difference <= timedelta(days=1):
        # Utilise le timesince de Django (renvoyé en format lisible : "2 days, 3 hours")
        # Note : On doit importer timesince. Si on l'utilise dans un filtre, on doit le faire manuellement.
        from django.template.defaultfilters import timesince

        return timesince(value) + " ago"
    else:
        # Affiche la date et l'heure complètes pour les durées de moins de 1 jour
        # Vous pouvez ajuster le format de la date ici :
        return value.strftime("%Y-%m-%d %H:%M:%S")


@register.simple_tag
def url_with_query(base_url, query_string):
    """
    Ajoute une chaîne de paramètres de requête à une URL de base existante.
    Usage: {% add_query_params edit_endpoint_base 'mode=edit&field=title' %}
    """
    if query_string:
        # Vérifie si l'URL contient déjà des paramètres
        separator = '&' if '?' in base_url else '?'
        return f"{base_url}{separator}{query_string}"
    return base_url