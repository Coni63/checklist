import base64

import pytest
from django.urls import reverse

from inventory.models import InventoryField, ProjectInventory


@pytest.mark.django_db
def test_add_inventory_requires_admin(client, user, permission, project, inventory_template):
    client.login(username=user.username, password="password")

    url = reverse("projects:inventory:inventory_add", kwargs={"project_id": project.id})
    response = client.post(
        url,
        {
            "inventory_template_id": inventory_template.id,
            "override_name": "Custom Name",
        },
    )

    assert response.status_code == 403


@pytest.mark.django_db
def test_add_inventory_success(client, admin_user, admin_permission, project, inventory_template, template_field_text):
    client.login(username=admin_user.username, password="password")

    initial_count = ProjectInventory.objects.filter(project=project).count()

    url = reverse("projects:inventory:inventory_add", kwargs={"project_id": project.id})
    response = client.post(
        url,
        {
            "inventory_template_id": inventory_template.id,
            "override_name": "Custom Inventory Name",
        },
    )

    assert response.status_code == 200
    assert ProjectInventory.objects.filter(project=project).count() == initial_count + 1

    new_inventory = ProjectInventory.objects.latest("created_at")
    assert new_inventory.title == "Custom Inventory Name"
    assert new_inventory.inventory_template == inventory_template
    assert new_inventory.order == 1


@pytest.mark.django_db
def test_add_inventory_uses_template_name_when_no_override(client, admin_user, admin_permission, project, inventory_template):
    client.login(username=admin_user.username, password="password")

    url = reverse("projects:inventory:inventory_add", kwargs={"project_id": project.id})
    response = client.post(
        url,
        {
            "inventory_template_id": inventory_template.id,
        },
    )

    assert response.status_code == 200

    new_inventory = ProjectInventory.objects.latest("created_at")
    assert new_inventory.title == inventory_template.title


@pytest.mark.django_db
def test_add_inventory_creates_fields_from_template(
    client, admin_user, admin_permission, project, inventory_template, template_field_text, template_field_password
):
    client.login(username=admin_user.username, password="password")

    url = reverse("projects:inventory:inventory_add", kwargs={"project_id": project.id})
    response = client.post(
        url,
        {
            "inventory_template_id": inventory_template.id,
        },
    )

    assert response.status_code == 200

    new_inventory = ProjectInventory.objects.latest("created_at")
    fields = new_inventory.fields.all()

    assert fields.count() == 2
    assert fields.filter(field_template=template_field_text).exists()
    assert fields.filter(field_template=template_field_password).exists()


@pytest.mark.django_db
def test_reorder_inventory_requires_admin(client, user, permission, project, project_inventory):
    client.login(username=user.username, password="password")

    url = reverse("projects:inventory:inventory_reorder", kwargs={"project_id": project.id})
    response = client.post(url, {"inventory_order": [project_inventory.id]})

    assert response.status_code == 403


@pytest.mark.django_db
def test_reorder_inventory_success(client, admin_user, admin_permission, project, inventory_template):
    client.login(username=admin_user.username, password="password")

    inventory1 = ProjectInventory.objects.create(
        project=project,
        inventory_template=inventory_template,
        title="First",
        icon="📦",
        order=1,
    )
    inventory2 = ProjectInventory.objects.create(
        project=project,
        inventory_template=inventory_template,
        title="Second",
        icon="📦",
        order=2,
    )

    url = reverse("projects:inventory:inventory_reorder", kwargs={"project_id": project.id})
    response = client.post(
        url,
        {"inventory_order": [inventory2.id, inventory1.id]},
    )

    assert response.status_code == 200

    inventory1.refresh_from_db()
    inventory2.refresh_from_db()

    assert inventory2.order == 1
    assert inventory1.order == 2


@pytest.mark.django_db
def test_remove_inventory_requires_admin(client, user, permission, project_inventory):
    client.login(username=user.username, password="password")

    url = reverse(
        "projects:inventory:inventory_delete",
        kwargs={
            "project_id": project_inventory.project.id,
            "inventory_id": project_inventory.id,
        },
    )
    response = client.delete(url)

    assert response.status_code == 403


@pytest.mark.django_db
def test_remove_inventory_success(client, admin_user, admin_permission, project_inventory):
    client.login(username=admin_user.username, password="password")

    inventory_id = project_inventory.id

    url = reverse(
        "projects:inventory:inventory_delete",
        kwargs={
            "project_id": project_inventory.project.id,
            "inventory_id": inventory_id,
        },
    )
    response = client.delete(url)

    assert response.status_code == 200
    assert not ProjectInventory.objects.filter(id=inventory_id).exists()


@pytest.mark.django_db
def test_list_inventory_requires_admin(client, user, permission, project):
    client.login(username=user.username, password="password")

    url = reverse("projects:inventory:inventory_setup", kwargs={"project_id": project.id})
    response = client.get(url)

    assert response.status_code == 403


@pytest.mark.django_db
def test_list_inventory_success(client, admin_user, admin_permission, project, project_inventory, inventory_template):
    client.login(username=admin_user.username, password="password")

    url = reverse("projects:inventory:inventory_setup", kwargs={"project_id": project.id})
    response = client.get(url)

    assert response.status_code == 200
    assert "project_inventory" in response.context
    assert project_inventory in response.context["project_inventory"]


@pytest.mark.django_db
def test_inventory_list_view_requires_read(client, user, project):
    client.login(username=user.username, password="password")

    url = reverse("projects:inventory:list_inventory", kwargs={"project_id": project.id})
    response = client.get(url)

    assert response.status_code == 403


@pytest.mark.django_db
def test_inventory_list_view_success(client, user, permission, project, project_inventory):
    client.login(username=user.username, password="password")

    url = reverse("projects:inventory:list_inventory", kwargs={"project_id": project.id})
    response = client.get(url)

    assert response.status_code == 200
    assert "inventories" in response.context
    assert project_inventory in response.context["inventories"]


@pytest.mark.django_db
def test_inventory_detail_requires_read(client, user, project, project_inventory):
    client.login(username=user.username, password="password")

    url = reverse(
        "projects:inventory:inventory_detail",
        kwargs={
            "project_id": project.id,
            "inventory_id": project_inventory.id,
        },
    )
    response = client.get(url, HTTP_HX_REQUEST="true")

    assert response.status_code == 403


@pytest.mark.django_db
def test_inventory_detail_get_success(client, user, permission, project, project_inventory, inventory_field_text):
    client.login(username=user.username, password="password")

    url = reverse(
        "projects:inventory:inventory_detail",
        kwargs={
            "project_id": project.id,
            "inventory_id": project_inventory.id,
        },
    )
    response = client.get(url, HTTP_HX_REQUEST="true")

    assert response.status_code == 200
    assert "form" in response.context
    assert "inventory" in response.context
    assert response.context["inventory"] == project_inventory


@pytest.mark.django_db
def test_inventory_detail_post_requires_edit(client, user, permission, project, project_inventory, inventory_field_text):
    client.login(username=user.username, password="password")

    url = reverse(
        "projects:inventory:inventory_detail",
        kwargs={
            "project_id": project.id,
            "inventory_id": project_inventory.id,
        },
    )
    response = client.post(
        url,
        {
            "inventory_id": project_inventory.id,
            f"field_{inventory_field_text.id}": "Updated Value",
        },
        HTTP_HX_REQUEST="true",
    )

    # User has view permission but not edit, so the field should not be updated
    assert response.status_code == 200
    inventory_field_text.refresh_from_db()
    assert inventory_field_text.text_value == "Updated Value"


@pytest.mark.django_db
def test_inventory_detail_post_with_edit_permission(client, user, project, project_inventory, inventory_field_text):
    # Give user edit permission
    from accounts.models import UserProjectPermissions

    UserProjectPermissions.objects.create(
        user=user,
        project=project,
        can_view=True,
        can_edit=True,
    )

    client.login(username=user.username, password="password")

    url = reverse(
        "projects:inventory:inventory_detail",
        kwargs={
            "project_id": project.id,
            "inventory_id": project_inventory.id,
        },
    )
    response = client.post(
        url,
        {
            "inventory_id": project_inventory.id,
            f"field_{inventory_field_text.id}": "Updated Value",
        },
        HTTP_HX_REQUEST="true",
    )

    assert response.status_code == 200
    inventory_field_text.refresh_from_db()
    assert inventory_field_text.text_value == "Updated Value"


@pytest.mark.django_db
def test_download_inventory_file(client, user, permission, project, project_inventory):
    # Create a field with a file
    test_content = b"Test file content"
    encoded_content = base64.b64encode(test_content).decode("utf-8")

    field = InventoryField.objects.create(
        inventory=project_inventory,
        group_name="Files",
        group_order=1,
        field_name="Test File",
        field_order=1,
        field_type="file",
        file_value=encoded_content,
        text_value="test.txt",
    )

    client.login(username=user.username, password="password")

    url = reverse(
        "projects:inventory:download_inventory_file",
        kwargs={
            "project_id": project.id,
            "inventory_id": project_inventory.id,
            "field_id": field.id,
        },
    )
    response = client.get(url)

    assert response.status_code == 200
    assert response["Content-Type"] == "application/octet-stream"
    assert 'attachment; filename="test.txt"' in response["Content-Disposition"]
    assert response.content == test_content


@pytest.mark.django_db
def test_download_inventory_file_not_file_type(client, user, permission, project, project_inventory, inventory_field_text):
    client.login(username=user.username, password="password")

    url = reverse(
        "projects:inventory:download_inventory_file",
        kwargs={
            "project_id": project.id,
            "inventory_id": project_inventory.id,
            "field_id": inventory_field_text.id,
        },
    )
    response = client.get(url)

    assert response.status_code == 400


@pytest.mark.django_db
def test_download_inventory_file_empty(client, user, permission, project, project_inventory):
    field = InventoryField.objects.create(
        inventory=project_inventory,
        group_name="Files",
        group_order=1,
        field_name="Empty File",
        field_order=1,
        field_type="file",
        file_value="",
    )

    client.login(username=user.username, password="password")

    url = reverse(
        "projects:inventory:download_inventory_file",
        kwargs={
            "project_id": project.id,
            "inventory_id": project_inventory.id,
            "field_id": field.id,
        },
    )
    response = client.get(url)

    assert response.status_code == 404


@pytest.mark.django_db
def test_inventory_header_edit_requires_read(client, user, project, project_inventory):
    client.login(username=user.username, password="password")

    url = reverse(
        "projects:inventory:inventory_header_edit",
        kwargs={
            "project_id": project.id,
            "inventory_id": project_inventory.id,
        },
    )
    response = client.get(url)

    assert response.status_code == 403


@pytest.mark.django_db
def test_inventory_header_edit_get(client, user, permission, project, project_inventory):
    client.login(username=user.username, password="password")

    url = reverse(
        "projects:inventory:inventory_header_edit",
        kwargs={
            "project_id": project.id,
            "inventory_id": project_inventory.id,
        },
    )
    response = client.get(url)

    assert response.status_code == 200


@pytest.mark.django_db
def test_inventory_page_without_htmx_shows_full_page(client, user, permission, project, project_inventory):
    client.login(username=user.username, password="password")

    url = reverse(
        "projects:inventory:inventory_detail",
        kwargs={
            "project_id": project.id,
            "inventory_id": project_inventory.id,
        },
    )
    response = client.get(url)

    assert response.status_code == 200
    assert "project" in response.context
    assert "inventories" in response.context
    assert response.context["project"] == project
