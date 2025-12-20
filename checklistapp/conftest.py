import pytest
from accounts.models import User, UserProjectPermissions
from projects.models import Project


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
