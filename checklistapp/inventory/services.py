import base64

from core.exceptions import RecordNotFoundError
from django.db import transaction
from django.db.models import Count, Max, Prefetch
from templates_management.models import FieldTemplate, GroupTemplate, InventoryTemplate

from inventory.validators import InventoryFieldValidator

from .models import InventoryField, InventoryGroup, ProjectInventory


class InventoryService:
    @staticmethod
    def get_template(template_id: int | None = None, load_fields=False):
        qs = InventoryTemplate.objects.filter(is_active=True).order_by("default_order")
        if load_fields:
            qs = qs.prefetch_related(
                Prefetch(
                    "groups",
                    queryset=GroupTemplate.objects.order_by("group_order", "group_name").prefetch_related(
                        Prefetch("fields", queryset=FieldTemplate.objects.order_by("field_order", "field_name"))
                    ),
                )
            )
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
            ProjectInventory.objects.filter(project=project)
            .select_related("inventory_template")
            .prefetch_related("groups__fields")
            .order_by("order")
        )

    @staticmethod
    @transaction.atomic
    def add_inventory_to_project(project, template_id, custom_title: str | None = None) -> int:
        inventory_template = InventoryService.get_template(template_id, load_fields=True)

        # Determine inventory order and count
        result = ProjectInventory.objects.filter(project=project).aggregate(max_order=Max("order"), total=Count("id"))

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

        # Create Groups and Fields
        fields_to_create = []

        # We need to save groups first to get their IDs, so we can't do a full bulk_create for everything at once easily without IDs.
        # However, we can iterate and save groups, then bulk create fields per group or globally if we track ids.
        # Since number of groups per inventory is small, iterative save for groups is fine.

        for group_template in inventory_template.groups.all():
            group = InventoryGroup.objects.create(
                inventory=inventory,
                group_template=group_template,
                name=group_template.group_name,
                order=group_template.group_order,
            )

            for field_template in group_template.fields.all():
                fields_to_create.append(
                    InventoryField(
                        group=group,
                        field_template=field_template,
                        field_name=field_template.field_name,
                        field_order=field_template.field_order,
                        field_type=field_template.field_type,
                        is_secret=field_template.is_secret,
                    )
                )

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

    @staticmethod
    def get_group(project_id, inventory_id, group_id) -> InventoryGroup:
        field = InventoryGroup.objects.filter(
            id=group_id, inventory__project__id=project_id, inventory__id=inventory_id
        ).first()
        if not field:
            raise RecordNotFoundError(f"Group {group_id} not found in inventory {inventory_id}.")
        return field

    @staticmethod
    def add_group(project_id, inventory_id, group_name) -> InventoryGroup:
        inventory = InventoryService.get_inventory(project_id, inventory_id)

        # Auto-increment order
        max_order = inventory.groups.aggregate(Max("order"))["order__max"] or 0
        return InventoryGroup.objects.create(inventory=inventory, name=group_name, order=max_order + 1)

    @staticmethod
    def delete_group(project_id, inventory_id, group_id):
        try:
            group = InventoryService.get_group(project_id, inventory_id, group_id)
            group.delete()
        except InventoryGroup.DoesNotExist:
            raise RecordNotFoundError(f"Group {group_id} not found.")

    @staticmethod
    def get_field(project_id, inventory_id, group_id, field_id: int | None = None) -> InventoryField:
        field = InventoryField.objects.filter(
            id=field_id, group__id=group_id, group__inventory__project__id=project_id, group__inventory__id=inventory_id
        ).first()
        if not field:
            raise RecordNotFoundError(f"Field {field_id} not found in inventory {inventory_id}.")
        return field

    @staticmethod
    def add_field(project_id, inventory_id, group_id, field_name, field_type, is_secret):
        group = InventoryService.get_group(project_id, inventory_id, group_id)

        # Auto-increment order
        max_order = group.fields.aggregate(Max("field_order"))["field_order__max"] or 0

        return InventoryField.objects.create(
            group=group,
            field_name=field_name,
            field_type=field_type,
            field_order=max_order + 1,
            is_secret=is_secret,
        )

    @staticmethod
    def delete_field(project_id, inventory_id, group_id, field_id):
        try:
            field = InventoryService.get_field(project_id, inventory_id, group_id, field_id)
            field.delete()
        except InventoryField.DoesNotExist:
            raise RecordNotFoundError(f"Field {field_id} not found.")

    @staticmethod
    def update_field_type(project_id, inventory_id, group_id, field_id, new_type, is_secret: bool = False):
        field = InventoryService.get_field(project_id, inventory_id, group_id, field_id)
        field = InventoryService._update_value(field, None, None)
        field.field_type = new_type
        field.is_secret = is_secret

        field.save()

        return field

    @staticmethod
    def set_field_value(project_id, inventory_id, group_id, field_id, value, filename: str | None = None):
        field = InventoryService.get_field(project_id, inventory_id, group_id, field_id)
        field = InventoryService._update_value(field, value, filename)

        field.save()

        return field

    @staticmethod
    def _update_value(field: InventoryField, value, filename: str | None = None):
        match field.field_type:
            case "text":
                field.text_value = InventoryFieldValidator.validate_text(value, 255)
            case "url":
                field.text_value = InventoryFieldValidator.validate_url(value)
            case "longtext":
                field.text_value = InventoryFieldValidator.validate_text(value, None)
            case "number":
                field.number_value = InventoryFieldValidator.validate_text(value)
            case "file":
                MAX_FILE_SIZE = 100 * 1024  # 100 KB en bytes
                value, filename = InventoryFieldValidator.validate_text(value, filename, MAX_FILE_SIZE)

                field.text_value = filename
                field.file_value = base64.b64encode(value).decode("utf-8")
            case "password":
                # Stored encrypted
                field.password_value = InventoryFieldValidator.validate_password(value)
            case "datetime":
                field.datetime_value = InventoryFieldValidator.validate_datetime(value)

        return field
