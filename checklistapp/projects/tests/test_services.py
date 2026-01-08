import pytest
from datetime import date
from unittest.mock import patch

from django.contrib.auth import get_user_model

from projects.models import Project
from projects.services import ProjectService

User = get_user_model()


@pytest.mark.django_db
def test_get_projects_for_user_ordering(mocker, admin_user):
    """
    Tests that projects are ordered correctly: null completion dates first,
    then by ascending completion date.
    """
    # Create projects with different completion dates
    project_late = Project.objects.create(name="Late Project", expected_completion_date=date(2026, 12, 31))
    project_early = Project.objects.create(name="Early Project", expected_completion_date=date(2026, 2, 15))
    project_no_date = Project.objects.create(name="Project No Date", expected_completion_date=None)
    project_mid = Project.objects.create(name="Mid Project", expected_completion_date=date(2026, 8, 1))

    all_projects = [
        project_no_date,
        project_late,
        project_early,
        project_mid,
    ]
    project_ids = [p.id for p in all_projects]

    # Mock the permission service to return all project IDs
    # We assume the user has access to all projects for this test
    mock_get_permissions = mocker.patch("projects.services.AccountService.get_all_permissions_for_user")
    mock_get_permissions.return_value.values_list.return_value = project_ids

    # 2. Action
    sorted_projects = ProjectService.get_projects_for_user(admin_user, status="all")

    # 3. Assert
    # Verify the order is correct
    expected_order = [
        project_no_date,
        project_early,
        project_mid,
        project_late,
    ]

    assert list(sorted_projects) == expected_order
    assert sorted_projects[0].name == "Project No Date"
    assert sorted_projects[1].name == "Early Project"
    assert sorted_projects[2].name == "Mid Project"
    assert sorted_projects[3].name == "Late Project"

    # Check that the mock was called
    mock_get_permissions.assert_called_once_with(admin_user, True, False, False)
