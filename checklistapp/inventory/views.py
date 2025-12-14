import base64

from django.urls import reverse

from common.views import editable_header_view
from core.mixins import (
    CommonContextMixin,
    ProjectAdminRequiredMixin,
    ProjectReadRequiredMixin,
)
from django.contrib import messages
from django.db import transaction
from django.db.models import Count, Max
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.views import View
from django.views.generic import DetailView, ListView
from django.views.generic.base import ContextMixin
from django_htmx.http import reswap
from projects.models import Project
from templates_management.models import InventoryTemplate

from .forms import DynamicInventoryForm
from .models import InventoryField, ProjectInventory

# ViewProjectInventoryView


class AddProjectInventoryView(ProjectAdminRequiredMixin, View):
    """
    View to handle adding a new inventory to a project via HTMX.
    Expects POST data with 'inventory_template_id' and optional 'override_name'.
    Returns HTML fragment for the new step card that will be inserted via HTMX.
    If it's the first step, also returns the empty state replacement.
    """

    def post(self, request, project_id):
        project = Project.objects.get(pk=project_id)
        if not project:
            messages.error(request, "Project not found.")
            return reswap(HttpResponse(status=200), "none")

        inventory_template_id = request.POST.get("inventory_template_id")
        override_name = request.POST.get("override_name", "").strip()

        try:
            inventory_template = InventoryTemplate.objects.get(id=inventory_template_id, is_active=True)
            if not inventory_template:
                messages.error(request, "Inventory not found.")
                return reswap(HttpResponse(status=200), "none")

            # Determine inventory order and count
            result = ProjectInventory.objects.filter(project=project).aggregate(max_order=Max("order"), total=Count("id"))

            current_max_order = result["max_order"] or 0
            count_step = result["total"]

            # Use override name or default template name
            name = override_name if override_name else inventory_template.name

            # Create the project inventory
            inventory = ProjectInventory.objects.create(
                project=project,
                inventory_template=inventory_template,
                name=name,
                description=inventory_template.description,
                icon=inventory_template.icon,
                order=current_max_order + 1,
            )

            # Create fields from template
            field_templates = inventory_template.fields.filter(is_active=True).order_by("group_order", "field_order")
            for field_template in field_templates:
                InventoryField.objects.create(
                    inventory=inventory,
                    field_template=field_template,
                    group_name=field_template.group_name,
                    group_order=field_template.group_order,
                    field_name=field_template.field_name,
                    field_order=field_template.field_order,
                    field_type=field_template.field_type,
                )
            messages.success(request, "Inventory added successfully.")

            # Compute new step counter HTML that will be updated OOB
            step_counter = render_to_string(
                "inventory/partials/project_inventory_form.html#counter_inventory",
                {
                    "count": count_step + 1,
                },
            )

            # If it's the first step, change the hx-swap to replace the empty state div
            if current_max_order == 0:
                step_content = render_to_string(
                    "inventory/partials/project_inventory_form.html#inventory_row",
                    {"inventory": inventory, "project": project},
                    request=request,
                )
                response = HttpResponse(step_counter + step_content)
                return reswap(response, "innerHTML")

            # Return HTML fragment for the new step card
            step_content = render_to_string(
                "inventory/partials/project_inventory_form.html#inventory_row",
                {"inventory": inventory, "project": project},
                request=request,
            )
            return HttpResponse(step_counter + step_content)

        except Exception as e:
            print(e)
            messages.error(request, "Something went wrong when adding the inventory to the project.")
            return reswap(HttpResponse(status=200), "none")


class ReorderProjectInventoryView(ProjectAdminRequiredMixin, View):
    """
    Handle reordering of project steps via HTMX.
    Expects POST data with 'inventory_order' as a list of step IDs in the new order.
    """

    def post(self, request, project_id):
        project = get_object_or_404(Project, pk=project_id)

        order = request.POST.getlist("inventory_order", [])
        order = [int(s) for s in order]  # Ensure int

        with transaction.atomic():
            # Fetch all steps in one query
            steps = ProjectInventory.objects.filter(project=project, pk__in=order).in_bulk(field_name="pk")

            # Phase 1 : temporary order to avoid unique collision
            for tmp_idx, step in enumerate(steps.values(), start=10000):
                step.order = tmp_idx

            ProjectInventory.objects.bulk_update(steps.values(), ["order"])

            # Phase 2 : assign final order
            for index, step_id in enumerate(order, start=1):
                steps[step_id].order = index

            ProjectInventory.objects.bulk_update(steps.values(), ["order"])

        return HttpResponse("")


class RemoveProjectInventoryView(ProjectAdminRequiredMixin, View):
    """Handle removing a step from a project via HTMX"""

    def delete(self, request, project_id, inventory_id):
        project = get_object_or_404(Project, pk=project_id)
        project_step = get_object_or_404(ProjectInventory, id=inventory_id, project=project)

        try:
            project_step.delete()

            # Check if there are any steps left
            remaining_steps = ProjectInventory.objects.filter(project=project).count()

            # Compute new step counter HTML that will be updated OOB
            step_counter = render_to_string(
                "inventory/partials/project_inventory_form.html#counter_inventory",
                {
                    "count": remaining_steps,
                },
            )

            messages.success(request, "Step deleted successfully.")
            if not remaining_steps:
                # Return empty state HTML
                empty_html = render_to_string("inventory/partials/project_inventory_form.html#inventory_empty")
                return HttpResponse(step_counter + empty_html)
            else:
                # Return empty response (card will be removed by HTMX)
                return HttpResponse(step_counter)

        except Exception:
            messages.error(request, "Something went wrong when deleting the step from the project.")
            return reswap(HttpResponse(status=200), "none")


class ListProjectInventoryView(ProjectAdminRequiredMixin, CommonContextMixin, DetailView):
    """
    View to display project details, including steps and tasks.
    Supports HTMX requests to load tasks for a specific step.
    """

    model = Project
    template_name = "inventory/partials/project_inventory_form.html"
    context_object_name = "project"
    pk_url_kwarg = "project_id"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["inventory_templates"] = InventoryTemplate.objects.filter(is_active=True).order_by("default_order")
        context["project_inventory"] = (
            ProjectInventory.objects.filter(project=self.object)  # i need the project Id that is in url
            .select_related("inventory_template")
            .prefetch_related("fields")
            .order_by("order")
        )
        return context


"""
Detail page
"""


def download_inventory_file(request, project_id, inventory_id, field_id):
    # 1. Récupérer l'instance du champ
    inventory_field = get_object_or_404(
        InventoryField,
        id=field_id,
        # Vous pouvez ajouter ici une vérification de l'utilisateur/permissions
    )

    # Sécurité : vérifier que c'est bien un champ de type 'file'
    if inventory_field.field_type != "file":
        return HttpResponse("Type de champ non supporté pour le téléchargement.", status=400)

    # Récupérer la chaîne B64 stockée
    b64_data = inventory_field.file_value
    filename = inventory_field.text_value or "attachement.txt"

    if not b64_data:
        return HttpResponse("Le fichier est vide ou n'a pas été défini.", status=404)

    try:
        # 2. Décoder la chaîne Base64 en données binaires
        file_content = base64.b64decode(b64_data)

    except (TypeError, ValueError):
        # Cela peut arriver si la B64 est mal formée (corruption de données)
        return HttpResponse("Erreur lors du décodage Base64.", status=500)

    # 3. Préparer la réponse HTTP pour le téléchargement
    # Si vous avez stocké l'extension ou le nom original, utilisez-le ici.

    # B. Créer la réponse
    response = HttpResponse(file_content, content_type="application/octet-stream")

    # C. Définir l'en-tête Content-Disposition pour forcer le téléchargement
    response["Content-Disposition"] = f'attachment; filename="{filename}"'

    return response


class InventoryList(ProjectReadRequiredMixin, CommonContextMixin, ListView):
    model = ProjectInventory
    template_name = "inventory/partials/inventory_cards.html"
    context_object_name = "inventories"
    pk_url_kwarg = "project_id"

    def get_queryset(self):
        # Retrieve the project_id from the URL keyword arguments
        project_id = self.kwargs.get(self.pk_url_kwarg)

        # Filter ProjectInventory objects where the 'project' field matches the ID
        return ProjectInventory.objects.filter(project_id=project_id)


class InventoryDetail(ProjectReadRequiredMixin, CommonContextMixin, ContextMixin, View):
    """
    View to display project details, including steps and tasks.
    Supports HTMX requests to load tasks for a specific step.
    """

    template_name = "inventory/partials/inventory_right_side.html"

    def get(self, request, *args, **kwargs):
        context = self.get_context_data()

        if not request.htmx:
            project = get_object_or_404(
                Project,
                id=context["project_id"],
            )
            context["project"] = project
            context["inventories"] = project.inventories.all()
            self.template_name = "inventory/inventory_detail.html"
            return render(request, self.template_name, context)

        inventory_id = context.get("inventory_id")
        if not inventory_id:
            return render(request, self.template_name, context)

        inventory = get_object_or_404(
            ProjectInventory.objects.prefetch_related("fields"),
            id=inventory_id,
        )
        context["tasks"] = inventory.fields.all()
        context["inventory"] = inventory

        form = DynamicInventoryForm(inventory, context)
        context["form"] = form
        context["groups"] = InventoryDetail.group_fields_by_group(form)

        context["edit_endpoint_base"] = reverse("projects:inventory:inventory_header_edit", kwargs={"project_id": context["project_id"], "inventory_id": context["inventory_id"]})
        context["can_edit"] = "edit" in context["roles"]

        return render(request, self.template_name, context)

    @staticmethod
    def group_fields_by_group(form):
        groups = {}

        # Copy metadata for sorting
        meta = {}

        for name, field in form.fields.items():
            group = getattr(field, "group_name", "Other")
            order = getattr(field, "group_order", 999)

            groups.setdefault(group, []).append((name, form[name]))
            meta[group] = order

        # Sort groups by group_order
        sorted_groups = dict(sorted(groups.items(), key=lambda item: meta[item[0]]))

        return sorted_groups

    def post(self, request, *args, **kwargs):
        inventory_id = request.POST.get("inventory_id")

        inventory = get_object_or_404(
            ProjectInventory.objects.prefetch_related("fields"),
            id=inventory_id,
        )

        context = self.get_context_data()

        is_admin = "admin" in context["roles"]

        form = DynamicInventoryForm(inventory, context, request.POST, request.FILES)

        if form.is_valid():
            form.save(is_admin=is_admin)

            if request.headers.get("HX-Request"):
                # return freshly rendered partial
                context["form"] = DynamicInventoryForm(inventory, context)
                context["groups"] = InventoryDetail.group_fields_by_group(context["form"])
                return render(request, "inventory/partials/fields_form.html", context)
            return redirect(request.path)

        context["form"] = form
        context["groups"] = InventoryDetail.group_fields_by_group(form)

        if request.headers.get("HX-Request"):
            return render(request, "inventory/partials/fields_form.html", context)

        return redirect(request.path)


class InventoryHeaderEditView(
    ProjectReadRequiredMixin,
    CommonContextMixin,
    ContextMixin,
    View,
):
    def post(self, request, *args, **kwargs):
        return self._inner(request, *args, **kwargs)
    
    def get(self, request, *args, **kwargs):
        return self._inner(request, *args, **kwargs)
    
    def _inner(self, request, *args, **kwargs):
        context = self.get_context_data()

        project_id = context["project_id"]
        inventory_id = context["inventory_id"]
        can_edit = "edit" in context["roles"]

        print(project_id, inventory_id, can_edit)

        edit_endpoint_base = reverse("projects:inventory:inventory_header_edit", kwargs={"project_id": project_id, "inventory_id": inventory_id})

        return editable_header_view(
            request=request,
            model_class=ProjectInventory,
            template_path="common/partials/editable_header.html",
            can_edit=can_edit,
            extra_context={
                "project_id": project_id, 
                "inventory_id": inventory_id
            },
            filter_kwargs={"project__id": project_id, "pk": inventory_id},
            edit_endpoint_base=edit_endpoint_base,
        )