from datetime import timedelta

from django import template
from django.utils import timezone
from django.urls import reverse

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


@register.simple_tag(takes_context=True)
def url_with_query(context, url_name, query_string='', **kwargs):
    """
    Construit une URL avec query string
    Usage: {% url_with_query 'my_url' 'mode=edit&field=title' project_id=1 inventory_id=12 %}
    """
    # Récupérer les url_kwargs du contexte s'ils existent
    url_kwargs = context.get('url_kwargs', {})
    url_kwargs.update(kwargs)
    
    url = reverse(url_name, kwargs=url_kwargs)
    if query_string:
        url = f"{url}?{query_string}"
    return url