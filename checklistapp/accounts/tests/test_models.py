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
