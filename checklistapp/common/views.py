from django.contrib import messages
from django.http import HttpResponse
from django.shortcuts import render
from django.urls import reverse
from django_htmx.http import reswap


def editable_header_view(
    request,
    model_class,
    template_path,
    field_prefix="object",
    can_edit=None,
    extra_context=None,
    filter_kwargs=None,
    edit_endpoint_base=None
):
    """
    Vue générique pour gérer l'édition de titre et description

    Args:
        model_class: Le modèle Django (ex: ProjectStep)
        template_path: Chemin vers le template contenant les partials
        field_prefix: Préfixe pour les IDs HTML (ex: 'step', 'task')
        can_edit: Boolean based on access rights
        extra_context: Dict de contexte supplémentaire
        filter_kwargs: Dict de filtres pour la requête
        edit_endpoint_base: Url to edit/save/display a field
    """
    # Construire les filtres

    # Récupérer l'objet
    obj = model_class.objects.filter(**filter_kwargs).first()
    if not obj:
        messages.error(request, f"{model_class.__name__} not found.")
        return reswap(HttpResponse(status=200), "none")

    # Récupérer les paramètres de mode et field
    mode = request.GET.get("mode", "display")
    field = request.GET.get("field", "title")

    # Déterminer le partial à rendre
    if mode == "edit":
        partial_name = f"{field}_form"
    else:  # display ou save
        partial_name = f"{field}_display"

    # Si c'est une requête POST (save), sauvegarder d'abord
    if request.method == "POST" and mode == "save":
        field_value = request.POST.get(field)
        if field_value is not None:
            setattr(obj, field, field_value)
            obj.save(update_fields=[field])
            messages.success(request, f"{field.title()} updated successfully.")

    # Préparer le contexte
    context = {
        "object": obj,
        "field_prefix": field_prefix,
        "can_edit": can_edit,
        "edit_endpoint_base": edit_endpoint_base,
    }
    if extra_context:
        context.update(extra_context)

    return render(request, f"{template_path}#{partial_name}", context=context)
