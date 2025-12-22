import pytest
from accounts.models import User, UserProjectPermissions
from freezegun import freeze_time
from inventory.models import InventoryField, ProjectInventory
from projects.models import Project
from templates_management.models import InventoryTemplate, TemplateField


@pytest.fixture
def user(db):
    return User.objects.create_user(
        username="user",
        password="password",
        email="user@test.com",
    )


@pytest.fixture
def admin_user(db):
    return User.objects.create_superuser(
        username="admin",
        password="password",
        email="admin@test.com",
    )


@pytest.fixture
def project(db):
    return Project.objects.create(name="Test Project")


@pytest.fixture
def project2(db):
    with freeze_time("2023-01-01"):
        return Project.objects.create(name="Test Project 2")


@pytest.fixture
def permission(user, project):
    return UserProjectPermissions.objects.create(
        user=user,
        project=project,
        can_view=True,
    )


@pytest.fixture
def admin_permission(db, admin_user, project):
    return UserProjectPermissions.objects.create(user=admin_user, project=project, can_view=True, can_edit=True, is_admin=True)


@pytest.fixture
def inventory_template(db):
    return InventoryTemplate.objects.create(
        title="Test Inventory Template",
        icon="📦",
        description="Test description",
        default_order=1,
        is_active=True,
    )


@pytest.fixture
def template_field_text(inventory_template):
    return TemplateField.objects.create(
        template=inventory_template,
        group_name="General",
        group_order=1,
        field_name="Test Text Field",
        field_order=1,
        field_type="text",
        is_active=True,
    )


@pytest.fixture
def template_field_password(inventory_template):
    return TemplateField.objects.create(
        template=inventory_template,
        group_name="Security",
        group_order=2,
        field_name="Test Password Field",
        field_order=1,
        field_type="password",
        is_secret=True,
        is_active=True,
    )


@pytest.fixture
def project_inventory(project, inventory_template):
    return ProjectInventory.objects.create(
        project=project,
        inventory_template=inventory_template,
        title="Test Inventory",
        description="Test inventory description",
        icon="📦",
        order=1,
    )


@pytest.fixture
def inventory_field_text(project_inventory, template_field_text):
    return InventoryField.objects.create(
        inventory=project_inventory,
        field_template=template_field_text,
        group_name="General",
        group_order=1,
        field_name="Test Text Field",
        field_order=1,
        field_type="text",
        text_value="Test Value",
    )


@pytest.fixture
def inventory_field_number(project_inventory):
    return InventoryField.objects.create(
        inventory=project_inventory,
        group_name="General",
        group_order=1,
        field_name="Test Number Field",
        field_order=2,
        field_type="number",
        number_value=42,
    )


@pytest.fixture
def inventory_field_file(project_inventory):
    return InventoryField.objects.create(
        inventory=project_inventory,
        group_name="General",
        group_order=1,
        field_name="Test Number Field",
        field_order=1,
        field_type="file",
    )
