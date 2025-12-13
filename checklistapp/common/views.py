from django.shortcuts import render
from django.http import HttpResponse
from django.contrib import messages
from django_htmx.http import reswap


def editable_header_view(request, model_class, object_id, template_path, 
                         field_prefix='object', can_edit_check=None, 
                         extra_context=None, filter_kwargs=None,
                         url_kwargs=None):  # NOUVEAU paramètre
    """
    Vue générique pour gérer l'édition de titre et description
    
    Args:
        model_class: Le modèle Django (ex: ProjectStep)
        object_id: L'ID de l'objet
        template_path: Chemin vers le template contenant les partials
        field_prefix: Préfixe pour les IDs HTML (ex: 'step', 'task')
        can_edit_check: Fonction qui prend (request, obj) et retourne bool
        extra_context: Dict de contexte supplémentaire
        filter_kwargs: Dict de filtres supplémentaires pour la requête
        url_kwargs: Dict des kwargs pour le reverse URL (ex: {'project_id': 1, 'inventory_id': 12})
    """
    # Construire les filtres
    filters = {'pk': object_id}
    if filter_kwargs:
        filters.update(filter_kwargs)
    
    # Récupérer l'objet
    obj = model_class.objects.filter(**filters).first()
    if not obj:
        messages.error(request, f"{model_class.__name__} not found.")
        return reswap(HttpResponse(status=200), "none")
    
    # Déterminer les permissions
    can_edit = True
    if can_edit_check:
        can_edit = can_edit_check(request, obj)
    
    # Récupérer les paramètres de mode et field
    mode = request.GET.get('mode', 'display')
    field = request.GET.get('field', 'title')
    
    # Déterminer le partial à rendre
    if mode == 'edit':
        partial_name = f"{field}_form"
    else:  # display ou save
        partial_name = f"{field}_display"
    
    # Si c'est une requête POST (save), sauvegarder d'abord
    if request.method == 'POST' and mode == 'save':
        field_value = request.POST.get(field)
        if field_value is not None:
            setattr(obj, field, field_value)
            obj.save(update_fields=[field])
            messages.success(request, f"{field.title()} updated successfully.")
    
    # Préparer le contexte
    context = {
        'object': obj,
        'field_prefix': field_prefix,
        'can_edit': can_edit,
        'edit_endpoint_base': request.resolver_match.url_name,
        'url_kwargs': url_kwargs or {},  # NOUVEAU
    }
    if extra_context:
        context.update(extra_context)
    
    return render(request, f"{template_path}#{partial_name}", context=context)