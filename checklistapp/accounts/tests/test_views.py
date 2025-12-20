import pytest
from django.urls import reverse

from accounts.models import User, UserProjectPermissions


@pytest.mark.django_db
def test_login_view_success(client, user):
    login_url = reverse("accounts:login")
    response = client.post(
        login_url,
        {"username": user.username, "password": "password"},
    )

    expected_url = reverse("projects:project_list")

    assert response.status_code == 302
    assert response.url == expected_url


@pytest.mark.parametrize("url", ["accounts:login", "accounts:register"])
@pytest.mark.django_db
def test_redirect_when_authenticated(client, user, url):
    client.login(username=user.username, password="password")

    response = client.get(reverse(url))

    expected_url = reverse("projects:project_list")

    assert response.status_code == 302
    assert response.url == expected_url


@pytest.mark.django_db
def test_login_when_notauthenticated(client, user):
    login_url = reverse("accounts:login")
    expected_url = reverse("projects:project_list")

    response = client.get(login_url)

    assert response.status_code == 200
    assert response.request["PATH_INFO"] == login_url
    assert "form" in response.context

    response = client.post(
        login_url,
        {"username": user.username, "password": "password"},
    )

    assert response.status_code == 302
    assert response.url == expected_url


@pytest.mark.django_db
def test_login_view_invalid_credentials(client, user):
    login_url = reverse("accounts:login")
    response = client.post(
        login_url,
        {"username": user.username, "password": "wrong"},
    )

    assert response.status_code == 200
    assert "form" in response.context


@pytest.mark.django_db
def test_register_view_creates_user(client):
    register_url = reverse("accounts:register")
    response = client.post(
        register_url,
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
    register_url = reverse("accounts:register")
    response = client.post(
        register_url,
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
    assert response.url.split("?")[0] == expected_url


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

    list_permission_url = reverse("accounts:user_permissions_list", kwargs={"project_id": project.id})
    response = client.get(list_permission_url)

    assert response.status_code == 403


@pytest.mark.django_db
def test_user_permissions_list(client, admin_user, admin_permission, user, project):
    client.login(username=admin_user.username, password="password")

    UserProjectPermissions.objects.create(
        user=user,
        project=project,
        can_view=True,
    )

    list_permission_url = reverse("accounts:user_permissions_list", kwargs={"project_id": project.id})
    response = client.get(list_permission_url)

    assert response.status_code == 200
    assert not response.context["other_users"].exists()  # all users have at least an access
    assert response.context["current_permissions"].count() == 2


@pytest.mark.django_db
def test_admin_cannot_delete_own_permission(client, admin_user, admin_permission, project):
    client.login(username=admin_user.username, password="password")

    edit_permission_url = reverse(
        "accounts:user_permissions_update", kwargs={"project_id": project.id, "permission_id": admin_permission.id}
    )
    response = client.delete(edit_permission_url)

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

    response = client.delete(f"/accounts/user_permissions/{project.id}/permissions/{permission.id}/edit/")

    assert not UserProjectPermissions.objects.filter(id=permission.id).exists()
    assert response.status_code == 200


@pytest.mark.django_db
def test_admin_creating_user_permissions(client, project, admin_user, admin_permission, user):
    client.login(username=admin_user.username, password="password")

    # check first that we don't have the permission
    assert not UserProjectPermissions.objects.filter(
        project=project,
        user=user,
    ).exists()

    # create it
    create_permission_url = reverse("accounts:user_permissions_add", kwargs={"project_id": project.id})
    data = {
        "user_id": user.id,
    }
    response = client.post(create_permission_url, data)

    assert response.status_code == 200
    assert "user_row" in [t.name for t in response.templates]

    permission_created = response.context["permission"]
    assert not permission_created.can_view
    assert not permission_created.can_edit
    assert not permission_created.is_admin


@pytest.mark.django_db
def test_admin_creating_user_permissions_already_present(client, project, admin_user, admin_permission, user):
    client.login(username=admin_user.username, password="password")

    # create a permission for this user
    UserProjectPermissions.objects.create(
        project=project,
        user=user,
        can_view=True,
        can_edit=False,
        is_admin=False,
    )

    # create it
    create_permission_url = reverse("accounts:user_permissions_add", kwargs={"project_id": project.id})
    data = {
        "user_id": user.id,
    }
    response = client.post(create_permission_url, data)

    assert response.status_code == 200
    # HTML should be empty
    assert "user_row" not in [t.name for t in response.templates]
    assert response.context is None


@pytest.mark.parametrize(
    "role, can_view, can_edit, is_admin",
    [
        ("can_view", True, False, False),
        ("can_edit", True, True, False),
        ("is_admin", True, True, True),
        ("other", False, False, False),
    ],
)
@pytest.mark.django_db
def test_admin_edit_user_permissions(client, project, admin_user, admin_permission, user, role, can_view, can_edit, is_admin):
    client.login(username=admin_user.username, password="password")

    # create a permission for this user
    permission = UserProjectPermissions.objects.create(
        project=project,
        user=user,
        can_view=False,
        can_edit=False,
        is_admin=False,
    )

    # create it
    edit_permission_url = reverse(
        "accounts:user_permissions_update", kwargs={"project_id": project.id, "permission_id": permission.id}
    )
    data = {
        "field_name": role,
    }
    response = client.post(edit_permission_url, data)

    permission.refresh_from_db()

    assert response.status_code == 200
    assert "user_row" in [t.name for t in response.templates]
    assert permission == response.context["permission"]
    assert permission.can_view == can_view
    assert permission.can_edit == can_edit
    assert permission.is_admin == is_admin


@pytest.mark.parametrize(
    "role, can_view, can_edit, is_admin",
    [
        ("can_view", False, False, False),
        ("can_edit", True, False, False),
        ("is_admin", True, True, False),
        ("other", True, True, True),
    ],
)
@pytest.mark.django_db
def test_admin_edit_remove_user_permissions(
    client, project, admin_user, admin_permission, user, role, can_view, can_edit, is_admin
):
    client.login(username=admin_user.username, password="password")

    # create a permission for this user
    permission = UserProjectPermissions.objects.create(
        project=project,
        user=user,
        can_view=True,
        can_edit=True,
        is_admin=True,
    )

    # create it
    edit_permission_url = reverse(
        "accounts:user_permissions_update", kwargs={"project_id": project.id, "permission_id": permission.id}
    )
    data = {
        "field_name": role,
    }
    response = client.post(edit_permission_url, data)

    permission.refresh_from_db()

    assert response.status_code == 200
    assert "user_row" in [t.name for t in response.templates]
    assert permission == response.context["permission"]
    assert permission.can_view == can_view
    assert permission.can_edit == can_edit
    assert permission.is_admin == is_admin
