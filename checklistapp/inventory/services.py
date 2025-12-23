from core.exceptions import RecordNotFoundError
from django.db import transaction
from django.db.models import Count, Max, Prefetch
from templates_management.models import InventoryTemplate, TemplateField

from .models import InventoryField, ProjectInventory


class InventoryService:
    @staticmethod
    def get_template(template_id: int | None = None, load_fields=False):
        qs = InventoryTemplate.objects.filter(is_active=True).order_by("default_order")
        if load_fields:
            qs = qs.prefetch_related(Prefetch("fields", queryset=TemplateField.objects.order_by("group_order", "field_order")))
        if template_id:
            template = qs.filter(id=template_id).first()
            if not template:
                raise RecordNotFoundError("Inventory template not found.")
            return template
        return qs

    @staticmethod
    def get_inventory(project_id, inventory_id: int | None = None, prefetch_related: list[str] | None = None):
        qs = ProjectInventory.objects.filter(project__id=project_id)

        if prefetch_related:
            qs = qs.prefetch_related(*prefetch_related)

        if inventory_id:
            qs = qs.filter(id=inventory_id).first()
            if not qs:
                raise RecordNotFoundError(f"Inventory {inventory_id} not found in project {project_id}.")

        return qs

    @staticmethod
    def get_inventory_for_project(project):
        return (
            ProjectInventory.objects.filter(project=project)  # i need the project Id that is in url
            .select_related("inventory_template")
            .prefetch_related("fields")
            .order_by("order")
        )

    @staticmethod
    def get_fields(project_id, inventory_id, field_id: int | None = None):
        qs = InventoryField.objects.filter(inventory__project__id=project_id, inventory__id=inventory_id)
        if field_id:
            field = qs.filter(id=field_id).first()
            if not field:
                raise RecordNotFoundError(f"Field {field_id} not found in inventory {inventory_id}.")
            return field
        return qs

    @staticmethod
    @transaction.atomic
    def add_inventory_to_project(project, template_id, custom_title: str | None = None) -> int:
        inventory_template = InventoryService.get_template(template_id, load_fields=True)

        # Determine inventory order and count
        result = ProjectInventory.objects.filter(project=project).aggregate(max_order=Max("order"), total=Count("id"))

        # Reorder does not follow the count, for example we can have task 1, 2, 3. Delete the 2, add a task and we have 1, 3, 4.
        # Max Order is 3 avec the delete but count is 2
        current_max_order = result["max_order"] or 0
        count_step = result["total"]

        # Create the project inventory
        inventory = ProjectInventory.objects.create(
            project=project,
            inventory_template=inventory_template,
            title=custom_title or inventory_template.title,
            description=inventory_template.description,
            icon=inventory_template.icon,
            order=current_max_order + 1,
        )

        # Create fields from template
        fields_to_create = [
            InventoryField(
                inventory=inventory,
                field_template=field_template,
                group_name=field_template.group_name,
                group_order=field_template.group_order,
                field_name=field_template.field_name,
                field_order=field_template.field_order,
                field_type=field_template.field_type,
            )
            for field_template in inventory_template.fields.all()
        ]

        if fields_to_create:
            InventoryField.objects.bulk_create(fields_to_create)

        return {"inventory": inventory, "count_step": count_step}

    @staticmethod
    @transaction.atomic
    def reorder_inventory(project, ids: list[int]):
        """
        Take a list of ids and change their order to match the index.

        [1, 42, 3] means that step 1 is 1st, 42 is order 2, 3 is order 3
        """
        steps = ProjectInventory.objects.filter(project=project, pk__in=ids).in_bulk(field_name="pk")

        # Phase 1 : temporary order to avoid unique collision
        for tmp_idx, step in enumerate(steps.values(), start=10000):
            step.order = tmp_idx

        ProjectInventory.objects.bulk_update(steps.values(), ["order"])

        # Phase 2 : assign final order
        for index, step_id in enumerate(ids, start=1):
            steps[step_id].order = index

        ProjectInventory.objects.bulk_update(steps.values(), ["order"])

    @staticmethod
    @transaction.atomic
    def delete_inventory(project_id, inventory_id):
        inventory = InventoryService.get_inventory(project_id, inventory_id)

        inventory.delete()
