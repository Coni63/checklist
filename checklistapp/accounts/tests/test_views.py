from django.urls import reverse
import pytest

from accounts.models import User, UserProjectPermissions

@pytest.mark.django_db
def test_login_view_success(client, user):
    response = client.post(
        "/accounts/login/",
        {"username": user.username, "password": "password"},
    )

    expected_url = reverse("projects:project_list")

    assert response.status_code == 302
    assert response.url == expected_url

@pytest.mark.django_db
def test_login_view_invalid_credentials(client, user):
    response = client.post(
        "/accounts/login/",
        {"username": user.username, "password": "wrong"},
    )

    assert response.status_code == 200
    assert "form" in response.context


@pytest.mark.django_db
def test_register_view_creates_user(client):
    response = client.post(
        "/accounts/register/",
        {
            "username": "newuser",
            "email": "new@test.com",
            "password1": "StrongPass123!",
            "password2": "StrongPass123!",
        },
    )
    expected_url = reverse("projects:project_list")

    assert User.objects.filter(username="newuser").exists()
    assert response.status_code == 302
    assert response.url == expected_url


@pytest.mark.django_db
def test_register_user_already_existing(client, user):
    response = client.post(
        "/accounts/register/",
        {
            "username": user.username,
            "email": user.email,
            "password1": "StrongPass123!",
            "password2": "StrongPass123!",
        },
    )

    assert response.status_code == 200
    assert "form" in response.context


@pytest.mark.django_db
def test_profile_requires_login(client):
    response = client.get("/accounts/")
    expected_url = reverse("accounts:login")

    assert response.status_code == 302
    assert response.url.split('?')[0] == expected_url

@pytest.mark.django_db
def test_profile_update(client, user):
    client.login(username=user.username, password="password")

    response = client.post(
        "/accounts/",
        {"first_name": "Nico", "last_name": "Test"},
    )

    expected_url = reverse("accounts:profile")

    user.refresh_from_db()
    assert user.first_name == "Nico"
    assert response.status_code == 302
    assert response.url == expected_url

@pytest.mark.django_db
def test_user_permissions_list_denied_for_non_admin(client, user, project):
    client.login(username=user.username, password="password")

    response = client.get(
        f"/accounts/user_permissions/{project.id}/permissions/"
    )

    assert response.status_code == 403


@pytest.mark.django_db
def test_user_permissions_list(client, admin_user, admin_permission, user, project):
    client.login(username=admin_user.username, password="password")

    UserProjectPermissions.objects.create(
        user=user,
        project=project,
        can_view=True,
    )

    response = client.get(
        f"/accounts/user_permissions/{project.id}/permissions/"
    )

    assert response.status_code == 200
    assert not response.context["other_users"].exists() # all users have at least an access
    assert response.context["current_permissions"].count() == 2



@pytest.mark.django_db
def test_admin_cannot_delete_own_permission(client, admin_user, admin_permission, project):
    client.login(username=admin_user.username, password="password")

    response = client.delete(
        f"/accounts/user_permissions/{project.id}/permissions/{admin_permission.id}/edit/"
    )

    assert UserProjectPermissions.objects.filter(id=admin_permission.id).exists()
    assert response.status_code == 200


@pytest.mark.django_db
def test_admin_cannot_delete_other_permission(client, admin_user, admin_permission, user, project):
    permission = UserProjectPermissions.objects.create(
        user=user,
        project=project,
        can_view=True,
    )

    client.login(username=admin_user.username, password="password")

    response = client.delete(
        f"/accounts/user_permissions/{project.id}/permissions/{permission.id}/edit/"
    )

    assert not UserProjectPermissions.objects.filter(id=permission.id).exists()
    assert response.status_code == 200