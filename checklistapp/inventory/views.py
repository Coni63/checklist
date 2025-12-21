import base64
import logging

from common.views import editable_header_view
from core.exceptions import InvalidParameterError
from core.mixins import (
    CommonContextMixin,
    ProjectAdminRequiredMixin,
    ProjectReadRequiredMixin,
)
from django.contrib import messages
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.template.loader import render_to_string
from django.urls import reverse
from django.views import View
from django.views.generic import DetailView, ListView
from django.views.generic.base import ContextMixin
from django_htmx.http import reswap
from projects.models import Project
from projects.services import ProjectService

from .forms import DynamicInventoryForm
from .models import ProjectInventory
from .services import InventoryService

logger = logging.getLogger(__name__)


class AddProjectInventoryView(ProjectAdminRequiredMixin, View):
    """
    View to handle adding a new inventory to a project via HTMX.
    Expects POST data with 'inventory_template_id' and optional 'override_name'.
    Returns HTML fragment for the new step card that will be inserted via HTMX.
    If it's the first step, also returns the empty state replacement.
    """

    def post(self, request, project_id):
        try:
            project = ProjectService.get(project_id)

            inventory_template_id = request.POST.get("inventory_template_id")
            override_name = request.POST.get("override_name", "").strip()

            result = InventoryService.add_inventory_to_project(
                project=project, template_id=inventory_template_id, custom_title=override_name
            )

            inventory = result["inventory"]
            count_step = result["count_step"]

            # Compute new step counter HTML that will be updated OOB
            step_counter = render_to_string(
                "inventory/partials/project_inventory_form.html#counter_inventory",
                {"count": count_step + 1, "oob": True},
            )

            # Return HTML fragment for the new step card
            step_content = render_to_string(
                "inventory/partials/project_inventory_form.html#inventory_row",
                {"inventory": inventory, "project": project},
                request=request,
            )

            messages.success(request, "Inventory added successfully.")
            response = HttpResponse(step_counter + step_content)

            # If it's the first step, change the hx-swap to replace the empty state div
            return reswap(response, "innerHTML") if count_step == 0 else response
        except Exception as e:
            logger.error(e)
            if hasattr(e, "custom"):
                messages.error(request, str(e))
            else:
                messages.error(request, "Something went wrong when adding the inventory to the project.")
            return reswap(HttpResponse(status=200), "none")


class ReorderProjectInventoryView(ProjectAdminRequiredMixin, View):
    """
    Handle reordering of project steps via HTMX.
    Expects POST data with 'inventory_order' as a list of step IDs in the new order.
    """

    def post(self, request, project_id):
        try:
            project = ProjectService.get(project_id)
            try:
                order = request.POST.getlist("inventory_order", [])
                order = [int(s) for s in order]  # Ensure int
            except Exception:
                raise InvalidParameterError("Invalid 'order' input provided")

            InventoryService.reorder_inventory(project, order)

            return HttpResponse("")

        except Exception as e:
            logger.error(e)
            if hasattr(e, "custom"):
                messages.error(request, str(e))
            else:
                messages.error(request, "Something went wrong when reordering the inventory.")
            return reswap(HttpResponse(status=200), "none")


class RemoveProjectInventoryView(ProjectAdminRequiredMixin, View):
    """Handle removing a step from a project via HTMX"""

    def delete(self, request, project_id, inventory_id):
        try:
            InventoryService.delete_inventory(project_id, inventory_id)

            # Check if there are any steps left
            remaining_steps = InventoryService.get_inventory(project_id).count()

            # Compute new step counter HTML that will be updated OOB
            step_counter = render_to_string(
                "inventory/partials/project_inventory_form.html#counter_inventory",
                {"count": remaining_steps, "oob": True},
            )

            messages.success(request, "Step deleted successfully.")
            if not remaining_steps:
                # Return empty state HTML
                empty_html = render_to_string("inventory/partials/project_inventory_form.html#inventory_empty")
                return HttpResponse(step_counter + empty_html)
            else:
                # Return empty response (card will be removed by HTMX)
                return HttpResponse(step_counter)

        except Exception as e:
            logger.error(e)
            if hasattr(e, "custom"):
                messages.error(request, str(e))
            else:
                messages.error(request, "Something went wrong when removing the inventory from the project.")
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

        context["inventory_templates"] = InventoryService.get_template(load_fields=False)
        context["project_inventory"] = InventoryService.get_inventory_for_project(self.object)
        return context


"""
Detail page
"""


def download_inventory_file(request, project_id, inventory_id, field_id):
    try:
        # 1. Récupérer l'instance du champ
        inventory_field = InventoryService.get_fields(project_id, inventory_id, field_id)

        # Sécurité : vérifier que c'est bien un champ de type 'file'
        if inventory_field.field_type != "file":
            return HttpResponse("Filetype not supported", status=400)

        # Récupérer la chaîne B64 stockée
        b64_data = inventory_field.file_value
        filename = inventory_field.text_value or "attachement.txt"

        if not b64_data:
            return HttpResponse("File is empty.", status=404)

        try:
            file_content = base64.b64decode(b64_data)
        except (TypeError, ValueError):
            return HttpResponse("File is corrupted.", status=500)

        response = HttpResponse(file_content, content_type="application/octet-stream")
        response["Content-Disposition"] = f'attachment; filename="{filename}"'

        return response
    except Exception as e:
        import traceback

        print(traceback.print_exc())
        logger.error(e)
        if hasattr(e, "custom"):
            return HttpResponse(str(e), status=500)
        else:
            return HttpResponse("Something went wrong when downloading the file.", status=500)


class InventoryList(ProjectReadRequiredMixin, CommonContextMixin, ListView):
    model = ProjectInventory
    template_name = "inventory/partials/inventory_cards.html"
    context_object_name = "inventories"
    pk_url_kwarg = "project_id"

    def get_queryset(self):
        # Retrieve the project_id from the URL keyword arguments
        project_id = self.kwargs.get(self.pk_url_kwarg)

        return InventoryService.get_inventory(project_id)


class InventoryDetail(ProjectReadRequiredMixin, CommonContextMixin, ContextMixin, View):
    """
    View to display project details, including steps and tasks.
    Supports HTMX requests to load tasks for a specific step.
    """

    template_name = "inventory/partials/inventory_right_side.html"

    def get(self, request, *args, **kwargs):
        try:
            context = self.get_context_data()

            if not request.htmx:
                project = ProjectService.get(context["project_id"], prefetch_related=["inventories"])

                context["project"] = project
                context["inventories"] = project.inventories.all()
                self.template_name = "inventory/inventory_detail.html"
                return render(request, self.template_name, context)

            inventory_id = context.get("inventory_id")
            if not inventory_id:
                return render(request, self.template_name, context)

            inventory = InventoryService.get_inventory(context["project_id"], inventory_id, prefetch_related=["fields"])
            context["tasks"] = inventory.fields.all()
            context["inventory"] = inventory

            form = DynamicInventoryForm(inventory, context)
            context["form"] = form
            context["groups"] = InventoryDetail._group_fields_by_group(form)

            context["edit_endpoint_base"] = reverse(
                "projects:inventory:inventory_header_edit",
                kwargs={"project_id": context["project_id"], "inventory_id": context["inventory_id"]},
            )
            context["can_edit"] = "edit" in context["roles"]

            return render(request, self.template_name, context)
        except Exception as e:
            logger.error(e)
            if hasattr(e, "custom"):
                messages.error(request, str(e))
            else:
                messages.error(request, "Something went wrong when listing the inventory.")
            return render(request, self.template_name, context)

    @staticmethod
    def _group_fields_by_group(form):
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
        try:
            context = self.get_context_data()

            inventory_id = request.POST.get("inventory_id")
            inventory = InventoryService.get_inventory(context["project_id"], inventory_id, prefetch_related=["fields"])

            form = DynamicInventoryForm(inventory, context, request.POST, request.FILES)
            if form.is_valid():
                form.save(is_admin="admin" in context["roles"])

                if request.htmx:
                    # return freshly rendered partial
                    context["form"] = DynamicInventoryForm(inventory, context)
                    context["groups"] = InventoryDetail._group_fields_by_group(context["form"])
                    return render(request, "inventory/partials/inventory_form.html", context)
                return redirect(request.path)

            context["form"] = form
            context["groups"] = InventoryDetail._group_fields_by_group(form)

            if request.htmx:
                return render(request, "inventory/partials/inventory_form.html", context)

            return redirect(request.path)
        except Exception as e:
            logger.error(e)
            if hasattr(e, "custom"):
                messages.error(request, str(e))
            else:
                messages.error(request, "Something went wrong when listing the inventory.")
            if request.htmx:
                return reswap(HttpResponse(status=200), "none")
            else:
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
        try:
            context = self.get_context_data()

            project_id = context["project_id"]
            inventory_id = context["inventory_id"]
            can_edit = "edit" in context["roles"]

            edit_endpoint_base = reverse(
                "projects:inventory:inventory_header_edit", kwargs={"project_id": project_id, "inventory_id": inventory_id}
            )

            return editable_header_view(
                request=request,
                model_class=ProjectInventory,
                template_path="common/partials/editable_header.html",
                can_edit=can_edit,
                extra_context={"project_id": project_id, "inventory_id": inventory_id},
                filter_kwargs={"project__id": project_id, "pk": inventory_id},
                edit_endpoint_base=edit_endpoint_base,
            )
        except Exception as e:
            logger.error(e)
            messages.error(request, "Something went wrong.")
            return redirect(request.path)
