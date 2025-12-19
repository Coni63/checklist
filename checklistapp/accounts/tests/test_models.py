import pytest

from accounts.models import UserProjectPermissions


@pytest.mark.django_db
def test_get_user_permissions_single_project(permission):
    perms = UserProjectPermissions.objects.get_user_permissions(
        user=permission.user,
        project_id=permission.project.id,
    )
    assert perms == permission

@pytest.mark.django_db
def test_get_user_permissions_list_projects(user, project, project2):
    UserProjectPermissions.objects.create(user=user, project=project)
    UserProjectPermissions.objects.create(user=user, project=project2)

    perms = UserProjectPermissions.objects.get_user_permissions(
        user=user,
        project_id=[project.id, project2.id],
    )

    assert perms.count() == 2

@pytest.mark.django_db
def test_get_user_permissions_not_found(user, project):
    perms = UserProjectPermissions.objects.get_user_permissions(
        user=user,
        project_id=project.id,
    )
    assert perms is None

@pytest.mark.django_db
def test_get_projects_for_user_read(user, project):
    UserProjectPermissions.objects.create(
        user=user,
        project=project,
        can_view=True,
        can_edit=False,
        is_admin=False,
    )

    projects = UserProjectPermissions.objects.get_projects_for_user(user)
    assert list(projects) == [project.id]

@pytest.mark.django_db
def test_get_projects_for_user_write(user, project):
    UserProjectPermissions.objects.create(
        user=user,
        project=project,
        can_view=True,
        can_edit=True,
        is_admin=False,
    )

    projects = UserProjectPermissions.objects.get_projects_for_user(user, write=True)
    assert project.id in projects

@pytest.mark.django_db
def test_get_projects_for_user_admin_only(user, project):
    UserProjectPermissions.objects.create(
        user=user,
        project=project,
        is_admin=True,
    )

    projects = UserProjectPermissions.objects.get_projects_for_user(user, admin=True)
    assert list(projects) == [project.id]