import pytest
from accounts.models import UserProjectPermissions
from django.urls import reverse

from projects.models import Project


@pytest.mark.django_db
def test_project_list_requires_login(client):
    """Test that project list requires authentication"""
    url = reverse("projects:project_list")
    response = client.get(url)

    assert response.status_code == 302
    assert "/accounts/login/" in response.url


@pytest.mark.django_db
def test_project_list_authenticated(client, user, project, permission):
    """Test project list view for authenticated user"""
    client.login(username=user.username, password="password")

    url = reverse("projects:project_list")
    response = client.get(url)

    assert response.status_code == 200
    assert "projects" in response.context
    assert project in response.context["projects"]


@pytest.mark.django_db
def test_project_list_only_shows_user_projects(client, user, project, project2):
    """Test that users only see projects they have permission to"""
    # Give user permission only to project
    UserProjectPermissions.objects.create(user=user, project=project, can_view=True)

    client.login(username=user.username, password="password")

    url = reverse("projects:project_list")
    response = client.get(url)

    assert response.status_code == 200
    assert project in response.context["projects"]
    assert project2 not in response.context["projects"]


@pytest.mark.django_db
def test_project_list_filter_by_status_active(client, user, project, project2):
    """Test filtering projects by active status"""
    # Set up permissions
    UserProjectPermissions.objects.create(user=user, project=project, can_view=True)
    UserProjectPermissions.objects.create(user=user, project=project2, can_view=True)

    # Set different statuses
    project.status = "active"
    project.save()

    project2.status = "completed"
    project2.save()

    client.login(username=user.username, password="password")

    url = reverse("projects:project_list") + "?status=active"
    response = client.get(url)

    assert response.status_code == 200
    assert project in response.context["projects"]
    assert project2 not in response.context["projects"]
    assert response.context["status"] == "active"


@pytest.mark.django_db
def test_project_list_filter_by_status_completed(client, user, project, project2):
    """Test filtering projects by completed status"""
    # Set up permissions
    UserProjectPermissions.objects.create(user=user, project=project, can_view=True)
    UserProjectPermissions.objects.create(user=user, project=project2, can_view=True)

    # Set different statuses
    project.status = "active"
    project.save()

    project2.status = "completed"
    project2.save()

    client.login(username=user.username, password="password")

    url = reverse("projects:project_list") + "?status=completed"
    response = client.get(url)

    assert response.status_code == 200
    assert project not in response.context["projects"]
    assert project2 in response.context["projects"]
    assert response.context["status"] == "completed"


@pytest.mark.django_db
def test_project_list_filter_by_status_all(client, user, project, project2):
    """Test showing all projects regardless of status"""
    # Set up permissions
    UserProjectPermissions.objects.create(user=user, project=project, can_view=True)
    UserProjectPermissions.objects.create(user=user, project=project2, can_view=True)

    project.status = "active"
    project.save()

    project2.status = "completed"
    project2.save()

    client.login(username=user.username, password="password")

    url = reverse("projects:project_list") + "?status=all"
    response = client.get(url)

    assert response.status_code == 200
    assert project in response.context["projects"]
    assert project2 in response.context["projects"]


@pytest.mark.django_db
def test_project_list_default_status_active(client, user, project):
    """Test that default status filter is active"""
    UserProjectPermissions.objects.create(user=user, project=project, can_view=True)

    client.login(username=user.username, password="password")

    url = reverse("projects:project_list")
    response = client.get(url)

    assert response.status_code == 200
    assert response.context["status"] == "active"


@pytest.mark.django_db
def test_project_list_includes_user_roles(client, user, project, admin_user):
    """Test that project list includes user roles"""
    # Give user edit permission
    UserProjectPermissions.objects.create(user=user, project=project, can_view=True, can_edit=True)

    client.login(username=user.username, password="password")

    url = reverse("projects:project_list")
    response = client.get(url)

    assert response.status_code == 200
    assert "roles" in response.context
    assert project.id in response.context["roles"]
    assert "edit" in response.context["roles"][project.id]
    assert "read" in response.context["roles"][project.id]


@pytest.mark.django_db
def test_project_list_admin_role(client, admin_user, project, admin_permission):
    """Test that admin users have admin role in context"""
    client.login(username=admin_user.username, password="password")

    url = reverse("projects:project_list")
    response = client.get(url)

    assert response.status_code == 200
    assert "roles" in response.context
    assert project.id in response.context["roles"]
    assert "admin" in response.context["roles"][project.id]
    assert "edit" in response.context["roles"][project.id]
    assert "read" in response.context["roles"][project.id]


@pytest.mark.django_db
def test_project_create_requires_login(client):
    """Test that project creation requires authentication"""
    url = reverse("projects:project_create")
    response = client.get(url)

    assert response.status_code == 302
    assert "/accounts/login/" in response.url


@pytest.mark.django_db
def test_project_create_get(client, user):
    """Test GET request to project create view"""
    client.login(username=user.username, password="password")

    url = reverse("projects:project_create")
    response = client.get(url)

    assert response.status_code == 200
    assert "form" in response.context


@pytest.mark.django_db
def test_project_create_post_success(client, user):
    """Test successful project creation"""
    client.login(username=user.username, password="password")

    url = reverse("projects:project_create")
    data = {
        "name": "New Project",
        "status": "active",
        "description": "Test description",
    }
    response = client.post(url, data)

    # Should redirect to project edit page
    assert response.status_code == 302

    # Check project was created
    project = Project.objects.get(name="New Project")
    assert project.description == "Test description"
    assert project.status == "active"

    # Check redirect URL
    expected_url = reverse("projects:project_edit", kwargs={"project_id": project.id})
    assert response.url == expected_url

    # Check permission was created for creator
    permission = UserProjectPermissions.objects.get(user=user, project=project)
    assert permission.is_admin is True
    assert permission.can_edit is True
    assert permission.can_view is True


@pytest.mark.django_db
def test_project_create_post_invalid_data(client, user):
    """Test project creation with invalid data"""
    client.login(username=user.username, password="password")

    url = reverse("projects:project_create")
    data = {
        "name": "",  # Empty name should fail validation
        "status": "active",
    }
    response = client.post(url, data)

    assert response.status_code == 200
    assert "form" in response.context
    assert response.context["form"].errors


@pytest.mark.django_db
def test_project_edit_requires_login(client, project):
    """Test that project edit requires authentication"""
    url = reverse("projects:project_edit", kwargs={"project_id": project.id})
    response = client.get(url)

    assert response.status_code == 302
    assert "/accounts/login/" in response.url


@pytest.mark.django_db
def test_project_edit_requires_admin_permission(client, user, project):
    """Test that project edit requires admin permission"""
    # Give user only view permission
    UserProjectPermissions.objects.create(user=user, project=project, can_view=True, can_edit=False, is_admin=False)

    client.login(username=user.username, password="password")

    url = reverse("projects:project_edit", kwargs={"project_id": project.id})
    response = client.get(url)

    assert response.status_code == 403


@pytest.mark.django_db
def test_project_edit_get(client, admin_user, project, admin_permission):
    """Test GET request to project edit view"""
    client.login(username=admin_user.username, password="password")

    url = reverse("projects:project_edit", kwargs={"project_id": project.id})
    response = client.get(url)

    assert response.status_code == 200
    assert "form" in response.context
    assert response.context["project"] == project
    assert "available_templates" in response.context
    assert "inventory_templates" in response.context
    assert "project_steps" in response.context
    assert "project_inventory" in response.context


@pytest.mark.django_db
def test_project_edit_post_success(client, admin_user, project, admin_permission):
    """Test successful project edit"""
    client.login(username=admin_user.username, password="password")

    url = reverse("projects:project_edit", kwargs={"project_id": project.id})
    data = {
        "name": "Updated Project Name",
        "status": "completed",
        "description": "Updated description",
    }
    response = client.post(url, data)

    # Should redirect back to edit page
    assert response.status_code == 302
    expected_url = reverse("projects:project_edit", kwargs={"project_id": project.id})
    assert response.url == expected_url

    # Check project was updated
    project.refresh_from_db()
    assert project.name == "Updated Project Name"
    assert project.status == "completed"
    assert project.description == "Updated description"


@pytest.mark.django_db
def test_project_edit_post_invalid_data(client, admin_user, project, admin_permission):
    """Test project edit with invalid data"""
    client.login(username=admin_user.username, password="password")

    url = reverse("projects:project_edit", kwargs={"project_id": project.id})
    data = {
        "name": "",  # Empty name should fail
        "status": "active",
    }
    response = client.post(url, data)

    assert response.status_code == 200
    assert "form" in response.context
    assert response.context["form"].errors


@pytest.mark.django_db
def test_project_delete_requires_login(client, project):
    """Test that project delete requires authentication"""
    url = reverse("projects:project_delete", kwargs={"project_id": project.id})
    response = client.delete(url)

    assert response.status_code == 302
    assert "/accounts/login/" in response.url


@pytest.mark.django_db
def test_project_delete_requires_admin_permission(client, user, project):
    """Test that project delete requires admin permission"""
    # Give user only view permission
    UserProjectPermissions.objects.create(user=user, project=project, can_view=True, can_edit=False, is_admin=False)

    client.login(username=user.username, password="password")

    url = reverse("projects:project_delete", kwargs={"project_id": project.id})
    response = client.delete(url)

    assert response.status_code == 403


@pytest.mark.django_db
def test_project_delete_success(client, admin_user, project, admin_permission):
    """Test successful project deletion"""
    client.login(username=admin_user.username, password="password")

    project_id = project.id
    url = reverse("projects:project_delete", kwargs={"project_id": project_id})
    response = client.delete(url)

    # Should redirect to project list
    assert response.status_code == 302
    expected_url = reverse("projects:project_list")
    assert response.url == expected_url

    # Check project was deleted
    assert not Project.objects.filter(id=project_id).exists()


@pytest.mark.django_db
def test_project_delete_using_post(client, admin_user, project, admin_permission):
    """Test project deletion using POST method"""
    client.login(username=admin_user.username, password="password")

    project_id = project.id
    url = reverse("projects:project_delete", kwargs={"project_id": project_id})
    response = client.post(url)

    # Should redirect to project list
    assert response.status_code == 302
    expected_url = reverse("projects:project_list")
    assert response.url == expected_url

    # Check project was deleted
    assert not Project.objects.filter(id=project_id).exists()


@pytest.mark.django_db
def test_project_edit_non_existent_project(client, admin_user):
    """
    Test editing a non-existent project returns 403
    Does not return 404 because the project may exist but he does not have any access
    """
    client.login(username=admin_user.username, password="password")

    url = reverse("projects:project_edit", kwargs={"project_id": 99999})
    response = client.get(url)

    assert response.status_code == 403


@pytest.mark.django_db
def test_project_delete_non_existent_project(client, admin_user):
    """
    Test deleting a non-existent project returns 403
    Does not return 404 because the project may exist but he does not have any access
    """
    client.login(username=admin_user.username, password="password")

    url = reverse("projects:project_delete", kwargs={"project_id": 99999})
    response = client.delete(url)

    assert response.status_code == 403
