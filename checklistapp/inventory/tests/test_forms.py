
import pytest

from inventory.forms import DynamicInventoryForm
from inventory.models import InventoryField


@pytest.mark.django_db
def test_dynamic_form_initialization(project_inventory, inventory_field_text):
    context = {
        "roles": ["edit", "admin"],
        "project_id": project_inventory.project.id,
        "inventory_id": project_inventory.id,
    }

    form = DynamicInventoryForm(project_inventory, context)

    assert f"field_{inventory_field_text.id}" in form.fields
    assert form.fields[f"field_{inventory_field_text.id}"].initial == "Test Value"


@pytest.mark.django_db
def test_dynamic_form_text_field(project_inventory):
    field = InventoryField.objects.create(
        inventory=project_inventory,
        group_name="General",
        group_order=1,
        field_name="Test Text",
        field_order=1,
        field_type="text",
        text_value="Initial Value",
    )

    context = {
        "roles": ["edit"],
        "project_id": project_inventory.project.id,
        "inventory_id": project_inventory.id,
    }

    form = DynamicInventoryForm(
        project_inventory,
        context,
        data={f"field_{field.id}": "New Value"},
    )

    assert form.is_valid()
    form.save(is_admin=False)

    field.refresh_from_db()
    assert field.text_value == "New Value"


@pytest.mark.django_db
def test_dynamic_form_number_field(project_inventory, inventory_field_number):
    context = {
        "roles": ["edit"],
        "project_id": project_inventory.project.id,
        "inventory_id": project_inventory.id,
    }

    form = DynamicInventoryForm(
        project_inventory,
        context,
        data={f"field_{inventory_field_number.id}": "100"},
    )

    assert form.is_valid()
    form.save(is_admin=False)

    inventory_field_number.refresh_from_db()
    assert inventory_field_number.number_value == 100


@pytest.mark.django_db
def test_dynamic_form_url_field(project_inventory):
    field = InventoryField.objects.create(
        inventory=project_inventory,
        group_name="Links",
        group_order=1,
        field_name="Website",
        field_order=1,
        field_type="url",
    )

    context = {
        "roles": ["edit"],
        "project_id": project_inventory.project.id,
        "inventory_id": project_inventory.id,
    }

    form = DynamicInventoryForm(
        project_inventory,
        context,
        data={f"field_{field.id}": "https://example.com"},
    )

    assert form.is_valid()
    form.save(is_admin=False)

    field.refresh_from_db()
    assert field.text_value == "https://example.com"


@pytest.mark.django_db
def test_dynamic_form_password_field(project_inventory):
    field = InventoryField.objects.create(
        inventory=project_inventory,
        group_name="Security",
        group_order=1,
        field_name="Password",
        field_order=1,
        field_type="password",
    )

    context = {
        "roles": ["edit", "admin"],
        "project_id": project_inventory.project.id,
        "inventory_id": project_inventory.id,
    }

    form = DynamicInventoryForm(
        project_inventory,
        context,
        data={f"field_{field.id}": "secret123"},
    )

    assert form.is_valid()
    form.save(is_admin=True)

    field.refresh_from_db()
    assert field.password_value == "secret123"


@pytest.mark.django_db
def test_dynamic_form_datetime_field(project_inventory):
    field = InventoryField.objects.create(
        inventory=project_inventory,
        group_name="Dates",
        group_order=1,
        field_name="Created At",
        field_order=1,
        field_type="datetime",
    )

    context = {
        "roles": ["edit"],
        "project_id": project_inventory.project.id,
        "inventory_id": project_inventory.id,
    }

    datetime_str = "2024-01-15T10:30:00"
    form = DynamicInventoryForm(
        project_inventory,
        context,
        data={f"field_{field.id}": datetime_str},
    )

    assert form.is_valid()
    form.save(is_admin=False)

    field.refresh_from_db()
    assert field.datetime_value is not None


@pytest.mark.django_db
def test_dynamic_form_readonly_for_non_edit_role(project_inventory, inventory_field_text):
    context = {
        "roles": ["view"],
        "project_id": project_inventory.project.id,
        "inventory_id": project_inventory.id,
    }

    form = DynamicInventoryForm(project_inventory, context)
    field_widget = form.fields[f"field_{inventory_field_text.id}"].widget

    assert "readonly" in field_widget.attrs


@pytest.mark.django_db
def test_dynamic_form_secret_field_hidden_for_non_admin(project_inventory, template_field_password):
    field = InventoryField.objects.create(
        inventory=project_inventory,
        field_template=template_field_password,
        group_name="Security",
        group_order=1,
        field_name="Secret Password",
        field_order=1,
        field_type="password",
        password_value="existing_secret",
    )

    context = {
        "roles": ["edit"],
        "project_id": project_inventory.project.id,
        "inventory_id": project_inventory.id,
    }

    form = DynamicInventoryForm(project_inventory, context)

    form_field = form.fields[f"field_{field.id}"]
    assert form_field.disabled is True
    assert form_field.initial == "••••••"


@pytest.mark.django_db
def test_dynamic_form_secret_field_visible_for_admin(project_inventory, template_field_password):
    field = InventoryField.objects.create(
        inventory=project_inventory,
        field_template=template_field_password,
        group_name="Security",
        group_order=1,
        field_name="Secret Password",
        field_order=1,
        field_type="password",
        password_value="existing_secret",
    )

    context = {
        "roles": ["edit", "admin"],
        "project_id": project_inventory.project.id,
        "inventory_id": project_inventory.id,
    }

    form = DynamicInventoryForm(project_inventory, context)

    form_field = form.fields[f"field_{field.id}"]
    assert form_field.disabled is not True
    assert form_field.initial == "existing_secret"


@pytest.mark.django_db
def test_dynamic_form_non_admin_cannot_edit_secret_field(project_inventory, template_field_password):
    field = InventoryField.objects.create(
        inventory=project_inventory,
        field_template=template_field_password,
        group_name="Security",
        group_order=1,
        field_name="Secret Password",
        field_order=1,
        field_type="password",
        password_value="original_secret",
    )

    context = {
        "roles": ["edit"],
        "project_id": project_inventory.project.id,
        "inventory_id": project_inventory.id,
    }

    form = DynamicInventoryForm(
        project_inventory,
        context,
        data={f"field_{field.id}": "new_secret"},
    )

    assert form.is_valid()
    form.save(is_admin=False)

    field.refresh_from_db()
    # Value should remain unchanged
    assert field.password_value == "original_secret"


@pytest.mark.django_db
def test_dynamic_form_admin_can_edit_secret_field(project_inventory, template_field_password):
    field = InventoryField.objects.create(
        inventory=project_inventory,
        field_template=template_field_password,
        group_name="Security",
        group_order=1,
        field_name="Secret Password",
        field_order=1,
        field_type="password",
        password_value="original_secret",
    )

    context = {
        "roles": ["edit", "admin"],
        "project_id": project_inventory.project.id,
        "inventory_id": project_inventory.id,
    }

    form = DynamicInventoryForm(
        project_inventory,
        context,
        data={f"field_{field.id}": "new_secret"},
    )

    assert form.is_valid()
    form.save(is_admin=True)

    field.refresh_from_db()
    assert field.password_value == "new_secret"


@pytest.mark.django_db
def test_dynamic_form_field_grouping(project_inventory):
    InventoryField.objects.create(
        inventory=project_inventory,
        group_name="Group A",
        group_order=1,
        field_name="Field 1",
        field_order=1,
        field_type="text",
    )
    InventoryField.objects.create(
        inventory=project_inventory,
        group_name="Group B",
        group_order=2,
        field_name="Field 2",
        field_order=1,
        field_type="text",
    )

    context = {
        "roles": ["edit"],
        "project_id": project_inventory.project.id,
        "inventory_id": project_inventory.id,
    }

    form = DynamicInventoryForm(project_inventory, context)

    field1 = list(form.fields.values())[0]
    field2 = list(form.fields.values())[1]

    assert field1.group_name == "Group A"
    assert field2.group_name == "Group B"
    assert field1.group_order < field2.group_order
