import pytest
from django.utils import timezone

from inventory.models import InventoryField, ProjectInventory


@pytest.mark.django_db
def test_create_project_inventory(project_inventory):
    assert project_inventory.title == "Test Inventory"
    assert project_inventory.description == "Test inventory description"
    assert project_inventory.icon == "📦"
    assert project_inventory.order == 1
    assert project_inventory.project is not None
    assert project_inventory.inventory_template is not None


@pytest.mark.django_db
def test_project_inventory_str(project_inventory):
    assert str(project_inventory) == "Test Inventory"


@pytest.mark.django_db
def test_project_inventory_repr(project_inventory):
    assert repr(project_inventory) == f"ProjectInventory(id={project_inventory.id}, name=Test Inventory)"


@pytest.mark.django_db
def test_project_inventory_ordering(project, inventory_template):
    _ = ProjectInventory.objects.create(
        project=project,
        inventory_template=inventory_template,
        title="First Inventory",
        icon="📦",
        order=2,
    )
    _ = ProjectInventory.objects.create(
        project=project,
        inventory_template=inventory_template,
        title="Second Inventory",
        icon="📦",
        order=1,
    )

    inventories = list(ProjectInventory.objects.all())
    assert inventories[0].order < inventories[1].order
    assert inventories[0].title == "Second Inventory"


@pytest.mark.django_db
def test_project_inventory_unique_order_per_project(project, project2, inventory_template):
    # Same order is allowed for different projects
    inventory1 = ProjectInventory.objects.create(
        project=project,
        inventory_template=inventory_template,
        title="Inventory 1",
        icon="📦",
        order=1,
    )
    inventory2 = ProjectInventory.objects.create(
        project=project2,
        inventory_template=inventory_template,
        title="Inventory 2",
        icon="📦",
        order=1,
    )

    assert inventory1.order == inventory2.order
    assert inventory1.project != inventory2.project


@pytest.mark.django_db
def test_inventory_field_get_value_text(inventory_field_text):
    assert inventory_field_text.get_value() == "Test Value"
    assert inventory_field_text.field_type == "text"


@pytest.mark.django_db
def test_inventory_field_get_value_number(inventory_field_number):
    assert inventory_field_number.get_value() == 42
    assert inventory_field_number.field_type == "number"


@pytest.mark.django_db
def test_inventory_field_get_value_url(project_inventory):
    field = InventoryField.objects.create(
        inventory=project_inventory,
        group_name="Links",
        group_order=1,
        field_name="Test URL",
        field_order=1,
        field_type="url",
        text_value="https://example.com",
    )

    assert field.get_value() == "https://example.com"


@pytest.mark.django_db
def test_inventory_field_get_value_password(project_inventory):
    field = InventoryField.objects.create(
        inventory=project_inventory,
        group_name="Security",
        group_order=1,
        field_name="Test Password",
        field_order=1,
        field_type="password",
        password_value="secret123",
    )

    assert field.get_value() == "secret123"


@pytest.mark.django_db
def test_inventory_field_get_value_datetime(project_inventory):
    test_datetime = timezone.now()
    field = InventoryField.objects.create(
        inventory=project_inventory,
        group_name="Dates",
        group_order=1,
        field_name="Test Datetime",
        field_order=1,
        field_type="datetime",
        datetime_value=test_datetime,
    )

    assert field.get_value() == test_datetime


@pytest.mark.django_db
def test_inventory_field_get_value_file(project_inventory):
    field = InventoryField.objects.create(
        inventory=project_inventory,
        group_name="Files",
        group_order=1,
        field_name="Test File",
        field_order=1,
        field_type="file",
        file_value="base64encodedstring",
        text_value="filename.txt",
    )

    assert field.get_value() == "base64encodedstring"


@pytest.mark.django_db
def test_inventory_field_get_value_none(project_inventory):
    field = InventoryField.objects.create(
        inventory=project_inventory,
        group_name="Other",
        group_order=1,
        field_name="Test Field",
        field_order=1,
        field_type="invalid_type",
    )

    assert field.get_value() is None


@pytest.mark.django_db
def test_inventory_field_relationship(project_inventory, inventory_field_text):
    assert inventory_field_text.inventory == project_inventory
    assert inventory_field_text in project_inventory.fields.all()


@pytest.mark.django_db
def test_inventory_cascade_delete(project, inventory_template):
    inventory = ProjectInventory.objects.create(
        project=project,
        inventory_template=inventory_template,
        title="Test",
        icon="=�",
        order=1,
    )

    field = InventoryField.objects.create(
        inventory=inventory,
        group_name="Test",
        group_order=1,
        field_name="Test Field",
        field_order=1,
        field_type="text",
    )

    field_id = field.id
    inventory.delete()

    assert not InventoryField.objects.filter(id=field_id).exists()
