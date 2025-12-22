import pytest
from accounts.models import UserProjectPermissions
from django.urls import reverse
from templates_management.models import StepTemplate, TaskTemplate

from checklist.models import ProjectStep, ProjectTask, TaskComment


@pytest.fixture
def step_template(db):
    """Fixture for a step template"""
    return StepTemplate.objects.create(
        title="Test Step Template", description="Test description", icon="📝", default_order=1, is_active=True
    )


@pytest.fixture
def task_template(step_template):
    """Fixture for a task template"""
    return TaskTemplate.objects.create(
        step_template=step_template, title="Test Task Template", info_text="Test info", order=1, is_active=True
    )


@pytest.fixture
def project_step(project):
    """Fixture for a project step"""
    return ProjectStep.objects.create(project=project, title="Test Step", icon="📝", order=1)


@pytest.fixture
def project_task(project_step):
    """Fixture for a project task"""
    return ProjectTask.objects.create(project_step=project_step, title="Test Task", order=1, status="pending")


# ProjectStepDetailView Tests


@pytest.mark.django_db
def test_project_step_detail_requires_login(client, project):
    """Test that project step detail requires authentication"""
    url = reverse("projects:checklist:step_detail_default", kwargs={"project_id": project.id})
    response = client.get(url)

    assert response.status_code == 302
    assert "/accounts/login/" in response.url


@pytest.mark.django_db
def test_project_step_detail_requires_permission(client, user, project):
    """Test that project step detail requires read permission"""
    client.login(username=user.username, password="password")

    url = reverse("projects:checklist:step_detail_default", kwargs={"project_id": project.id})
    response = client.get(url)

    assert response.status_code == 403


@pytest.mark.django_db
def test_project_step_detail_view(client, user, project, permission, project_step):
    """Test project step detail view"""
    client.login(username=user.username, password="password")

    url = reverse("projects:checklist:step_detail_default", kwargs={"project_id": project.id})
    response = client.get(url)

    assert response.status_code == 200
    assert "project" in response.context
    assert "steps" in response.context


@pytest.mark.django_db
def test_project_step_detail_with_step_id(client, user, project, permission, project_step):
    """Test project step detail view with specific step"""
    client.login(username=user.username, password="password")

    url = reverse("projects:checklist:step_detail", kwargs={"project_id": project.id, "step_id": project_step.id})
    response = client.get(url)

    assert response.status_code == 200
    assert "active_step" in response.context
    assert response.context["active_step"] == project_step
    assert "tasks" in response.context


# ListProjectStepView Tests


@pytest.mark.django_db
def test_list_project_step_requires_admin(client, user, project):
    """Test that list project step requires admin permission"""
    UserProjectPermissions.objects.create(user=user, project=project, can_view=True, can_edit=True, is_admin=False)

    client.login(username=user.username, password="password")

    url = reverse("projects:checklist:checklist_setup", kwargs={"project_id": project.id})
    response = client.get(url)

    assert response.status_code == 403


@pytest.mark.django_db
def test_list_project_step_view(client, admin_user, project, admin_permission):
    """Test list project step view for admin"""
    client.login(username=admin_user.username, password="password")

    url = reverse("projects:checklist:checklist_setup", kwargs={"project_id": project.id})
    response = client.get(url)

    assert response.status_code == 200
    assert "project" in response.context
    assert "available_templates" in response.context
    assert "project_steps" in response.context


# AddProjectStepView Tests


@pytest.mark.django_db
def test_add_project_step_requires_admin(client, user, project, step_template):
    """Test that adding step requires admin permission"""
    UserProjectPermissions.objects.create(user=user, project=project, can_view=True, can_edit=True, is_admin=False)

    client.login(username=user.username, password="password")

    url = reverse("projects:checklist:step_add", kwargs={"project_id": project.id})
    response = client.post(url, {"step_template_id": step_template.id})

    assert response.status_code == 403


@pytest.mark.django_db
def test_add_project_step_success(client, admin_user, project, admin_permission, step_template, task_template):
    """Test successfully adding a step to project"""
    client.login(username=admin_user.username, password="password")

    url = reverse("projects:checklist:step_add", kwargs={"project_id": project.id})
    response = client.post(url, {"step_template_id": step_template.id})

    assert response.status_code == 200

    # Check step was created
    step = ProjectStep.objects.get(project=project, step_template=step_template)
    assert step.title == step_template.title
    assert step.icon == step_template.icon

    # Check tasks were created from template
    tasks = ProjectTask.objects.filter(project_step=step)
    assert tasks.count() == 1
    assert tasks.first().title == task_template.title


@pytest.mark.django_db
def test_add_project_step_with_override_name(client, admin_user, project, admin_permission, step_template):
    """Test adding step with custom name"""
    client.login(username=admin_user.username, password="password")

    url = reverse("projects:checklist:step_add", kwargs={"project_id": project.id})
    response = client.post(url, {"step_template_id": step_template.id, "override_name": "Custom Step Name"})

    assert response.status_code == 200

    step = ProjectStep.objects.get(project=project)
    assert step.title == "Custom Step Name"


@pytest.mark.django_db
def test_add_project_step_invalid_template(client, admin_user, project, admin_permission):
    """Test adding step with invalid template ID"""
    client.login(username=admin_user.username, password="password")

    url = reverse("projects:checklist:step_add", kwargs={"project_id": project.id})
    response = client.post(url, {"step_template_id": 99999})

    assert response.status_code == 200
    assert ProjectStep.objects.filter(project=project).count() == 0


# RemoveProjectStepView Tests


@pytest.mark.django_db
def test_remove_project_step_requires_admin(client, user, project, project_step):
    """Test that removing step requires admin permission"""
    UserProjectPermissions.objects.create(user=user, project=project, can_view=True, can_edit=True, is_admin=False)

    client.login(username=user.username, password="password")

    url = reverse("projects:checklist:step_delete", kwargs={"project_id": project.id, "step_id": project_step.id})
    response = client.delete(url)

    assert response.status_code == 403


@pytest.mark.django_db
def test_remove_project_step_success(client, admin_user, project, admin_permission, project_step):
    """Test successfully removing a step"""
    client.login(username=admin_user.username, password="password")

    url = reverse("projects:checklist:step_delete", kwargs={"project_id": project.id, "step_id": project_step.id})
    response = client.delete(url)

    assert response.status_code == 200
    assert not ProjectStep.objects.filter(id=project_step.id).exists()


# ReorderProjectStepsView Tests


@pytest.mark.django_db
def test_reorder_project_steps_requires_admin(client, user, project):
    """Test that reordering steps requires admin permission"""
    UserProjectPermissions.objects.create(user=user, project=project, can_view=True, can_edit=True, is_admin=False)

    client.login(username=user.username, password="password")

    url = reverse("projects:checklist:step_reorder", kwargs={"project_id": project.id})
    response = client.post(url, {"step_order": []})

    assert response.status_code == 403


@pytest.mark.django_db
def test_reorder_project_steps_success(client, admin_user, project, admin_permission):
    """Test successfully reordering steps"""
    # Create multiple steps
    step1 = ProjectStep.objects.create(project=project, title="Step 1", icon="📝", order=1)
    step2 = ProjectStep.objects.create(project=project, title="Step 2", icon="📝", order=2)
    step3 = ProjectStep.objects.create(project=project, title="Step 3", icon="📝", order=3)

    client.login(username=admin_user.username, password="password")

    # Reorder: step3, step1, step2
    url = reverse("projects:checklist:step_reorder", kwargs={"project_id": project.id})
    response = client.post(url, {"step_order": [step3.id, step1.id, step2.id]})

    assert response.status_code == 200

    # Check new order
    step1.refresh_from_db()
    step2.refresh_from_db()
    step3.refresh_from_db()

    assert step3.order == 1
    assert step1.order == 2
    assert step2.order == 3


# AddProjectTaskView Tests


@pytest.mark.django_db
def test_add_project_task_requires_edit_permission(client, user, project, project_step):
    """Test that adding task requires edit permission"""
    UserProjectPermissions.objects.create(user=user, project=project, can_view=True, can_edit=False)

    client.login(username=user.username, password="password")

    url = reverse("projects:checklist:task_create", kwargs={"project_id": project.id, "step_id": project_step.id})
    response = client.post(url, {"title": "New Task"})

    assert response.status_code == 403


@pytest.mark.django_db
def test_add_project_task_success(client, user, project, project_step):
    """Test successfully adding a task"""
    UserProjectPermissions.objects.create(user=user, project=project, can_view=True, can_edit=True)

    client.login(username=user.username, password="password")

    url = reverse("projects:checklist:task_create", kwargs={"project_id": project.id, "step_id": project_step.id})
    response = client.post(url, {"title": "New Manual Task"})

    assert response.status_code == 200

    # Check task was created
    task = ProjectTask.objects.get(project_step=project_step, title="New Manual Task")
    assert task.manually_created is True


@pytest.mark.django_db
def test_add_project_task_empty_title(client, user, project, project_step):
    """Test adding task with empty title"""
    UserProjectPermissions.objects.create(user=user, project=project, can_view=True, can_edit=True)

    client.login(username=user.username, password="password")

    url = reverse("projects:checklist:task_create", kwargs={"project_id": project.id, "step_id": project_step.id})
    response = client.post(url, {"title": ""})

    assert response.status_code == 200
    assert ProjectTask.objects.filter(project_step=project_step).count() == 0


# UpdateProjectTaskView Tests


@pytest.mark.django_db
def test_update_project_task_requires_edit_permission(client, user, project, project_step, project_task):
    """Test that updating task requires edit permission"""
    UserProjectPermissions.objects.create(user=user, project=project, can_view=True, can_edit=False)

    client.login(username=user.username, password="password")

    url = reverse(
        "projects:checklist:task_status_update",
        kwargs={"project_id": project.id, "step_id": project_step.id, "task_id": project_task.id},
    )
    response = client.post(url, {"status": "done"})

    assert response.status_code == 403


@pytest.mark.django_db
def test_update_project_task_mark_done(client, user, project, project_step, project_task):
    """Test marking task as done"""
    UserProjectPermissions.objects.create(user=user, project=project, can_view=True, can_edit=True)

    client.login(username=user.username, password="password")

    url = reverse(
        "projects:checklist:task_status_update",
        kwargs={"project_id": project.id, "step_id": project_step.id, "task_id": project_task.id},
    )
    response = client.post(url, {"status": "done"})

    assert response.status_code == 200

    project_task.refresh_from_db()
    assert project_task.status == "done"
    assert project_task.completed_by == user


@pytest.mark.django_db
def test_update_project_task_mark_na(client, user, project, project_step, project_task):
    """Test marking task as N/A"""
    UserProjectPermissions.objects.create(user=user, project=project, can_view=True, can_edit=True)

    client.login(username=user.username, password="password")

    url = reverse(
        "projects:checklist:task_status_update",
        kwargs={"project_id": project.id, "step_id": project_step.id, "task_id": project_task.id},
    )
    response = client.post(url, {"status": "na"})

    assert response.status_code == 200

    project_task.refresh_from_db()
    assert project_task.status == "na"


@pytest.mark.django_db
def test_update_project_task_toggle_status(client, user, project, project_step, project_task):
    """Test toggling task status back to pending"""
    UserProjectPermissions.objects.create(user=user, project=project, can_view=True, can_edit=True)

    # First mark as done
    project_task.mark_done(user)

    client.login(username=user.username, password="password")

    url = reverse(
        "projects:checklist:task_status_update",
        kwargs={"project_id": project.id, "step_id": project_step.id, "task_id": project_task.id},
    )
    # Post with same status should toggle back to pending
    response = client.post(url, {"status": "done"})

    assert response.status_code == 200

    project_task.refresh_from_db()
    assert project_task.status == "pending"


@pytest.mark.django_db
def test_update_project_task_invalid_status(client, user, project, project_step, project_task):
    """Test updating task with invalid status"""
    UserProjectPermissions.objects.create(user=user, project=project, can_view=True, can_edit=True)

    client.login(username=user.username, password="password")

    url = reverse(
        "projects:checklist:task_status_update",
        kwargs={"project_id": project.id, "step_id": project_step.id, "task_id": project_task.id},
    )
    response = client.post(url, {"status": "invalid"})

    assert response.status_code == 200

    project_task.refresh_from_db()
    assert project_task.status == "pending"  # Status unchanged


# DeleteProjectTaskView Tests


@pytest.mark.django_db
def test_delete_project_task_requires_edit_permission(client, user, project, project_step, project_task):
    """Test that deleting task requires edit permission"""
    UserProjectPermissions.objects.create(user=user, project=project, can_view=True, can_edit=False)

    client.login(username=user.username, password="password")

    url = reverse(
        "projects:checklist:task_delete",
        kwargs={"project_id": project.id, "step_id": project_step.id, "task_id": project_task.id},
    )
    response = client.delete(url)

    assert response.status_code == 403


@pytest.mark.django_db
def test_delete_manually_created_task(client, user, project, project_step):
    """Test deleting a manually created task"""
    UserProjectPermissions.objects.create(user=user, project=project, can_view=True, can_edit=True)

    # Create manually created task
    task = ProjectTask.objects.create(project_step=project_step, title="Manual Task", order=1, manually_created=True)

    client.login(username=user.username, password="password")

    url = reverse(
        "projects:checklist:task_delete", kwargs={"project_id": project.id, "step_id": project_step.id, "task_id": task.id}
    )
    response = client.delete(url)

    assert response.status_code == 200
    assert not ProjectTask.objects.filter(id=task.id).exists()


@pytest.mark.django_db
def test_delete_template_task_not_allowed(client, user, project, project_step, project_task):
    """Test that template-based tasks cannot be deleted"""
    UserProjectPermissions.objects.create(user=user, project=project, can_view=True, can_edit=True)

    # Ensure task is not manually created
    project_task.manually_created = False
    project_task.save()

    client.login(username=user.username, password="password")

    url = reverse(
        "projects:checklist:task_delete",
        kwargs={"project_id": project.id, "step_id": project_step.id, "task_id": project_task.id},
    )
    response = client.delete(url)

    assert response.status_code == 200
    # Task should still exist
    assert ProjectTask.objects.filter(id=project_task.id).exists()


# TaskCommentListView Tests


@pytest.mark.django_db
def test_task_comment_list_requires_read_permission(client, user, project, project_step, project_task):
    """Test that viewing comments requires read permission"""
    client.login(username=user.username, password="password")

    url = reverse(
        "projects:checklist:comment_list",
        kwargs={"project_id": project.id, "step_id": project_step.id, "task_id": project_task.id},
    )
    response = client.get(url)

    assert response.status_code == 403


@pytest.mark.django_db
def test_task_comment_list_view(client, user, project, project_step, project_task):
    """Test viewing task comments"""
    UserProjectPermissions.objects.create(user=user, project=project, can_view=True)

    # Create some comments
    TaskComment.objects.create(project_task=project_task, user=user, comment_text="First comment")
    TaskComment.objects.create(project_task=project_task, user=user, comment_text="Second comment")

    client.login(username=user.username, password="password")

    url = reverse(
        "projects:checklist:comment_list",
        kwargs={"project_id": project.id, "step_id": project_step.id, "task_id": project_task.id},
    )
    response = client.get(url)

    assert response.status_code == 200
    assert "comments" in response.context
    assert response.context["comments"].count() == 2


@pytest.mark.django_db
def test_task_comment_list_excludes_deleted(client, user, project, project_step, project_task):
    """Test that deleted comments are excluded from list"""
    UserProjectPermissions.objects.create(user=user, project=project, can_view=True)

    _ = TaskComment.objects.create(project_task=project_task, user=user, comment_text="Active comment")
    comment2 = TaskComment.objects.create(project_task=project_task, user=user, comment_text="Deleted comment")
    comment2.soft_delete()

    client.login(username=user.username, password="password")

    url = reverse(
        "projects:checklist:comment_list",
        kwargs={"project_id": project.id, "step_id": project_step.id, "task_id": project_task.id},
    )
    response = client.get(url)

    assert response.status_code == 200
    assert response.context["comments"].count() == 1


# TaskCommentCreateView Tests


@pytest.mark.django_db
def test_task_comment_create_requires_edit_permission(client, user, project, project_step, project_task):
    """Test that creating comment requires edit permission"""
    UserProjectPermissions.objects.create(user=user, project=project, can_view=True, can_edit=False)

    client.login(username=user.username, password="password")

    url = reverse(
        "projects:checklist:comment_create",
        kwargs={"project_id": project.id, "step_id": project_step.id, "task_id": project_task.id},
    )
    response = client.post(url, {"comment_text": "New comment"})

    assert response.status_code == 403


@pytest.mark.django_db
def test_task_comment_create_success(client, user, project, project_step, project_task):
    """Test successfully creating a comment"""
    UserProjectPermissions.objects.create(user=user, project=project, can_view=True, can_edit=True)

    client.login(username=user.username, password="password")

    url = reverse(
        "projects:checklist:comment_create",
        kwargs={"project_id": project.id, "step_id": project_step.id, "task_id": project_task.id},
    )
    response = client.post(url, {"comment_text": "New comment"})

    assert response.status_code == 200

    # Check comment was created
    comment = TaskComment.objects.get(project_task=project_task)
    assert comment.comment_text == "New comment"
    assert comment.user == user


# TaskCommentUpdateView Tests


@pytest.mark.django_db
def test_task_comment_update_own_comment(client, user, project, project_step, project_task):
    """Test updating own comment"""
    UserProjectPermissions.objects.create(user=user, project=project, can_view=True, can_edit=True)

    comment = TaskComment.objects.create(project_task=project_task, user=user, comment_text="Original comment")

    client.login(username=user.username, password="password")

    url = reverse(
        "projects:checklist:comment_edit",
        kwargs={"project_id": project.id, "step_id": project_step.id, "task_id": project_task.id, "comment_id": comment.id},
    )
    response = client.post(url, {"comment_text": "Updated comment"})

    assert response.status_code == 200

    comment.refresh_from_db()
    assert comment.comment_text == "Updated comment"


@pytest.mark.django_db
def test_task_comment_update_other_user_comment_denied(client, user, admin_user, project, project_step, project_task):
    """Test that users cannot update other users' comments"""
    UserProjectPermissions.objects.create(user=user, project=project, can_view=True, can_edit=True)

    # Create comment by admin_user
    comment = TaskComment.objects.create(project_task=project_task, user=admin_user, comment_text="Admin comment")

    # Try to update as regular user
    client.login(username=user.username, password="password")

    url = reverse(
        "projects:checklist:comment_edit",
        kwargs={"project_id": project.id, "step_id": project_step.id, "task_id": project_task.id, "comment_id": comment.id},
    )
    response = client.post(url, {"comment_text": "Updated comment"})
    # when a project is not found, return 403 because it can be jsute because the user does not have access
    assert response.status_code == 403


# TaskCommentDeleteView Tests


@pytest.mark.django_db
def test_task_comment_delete_own_comment(client, user, project, project_step, project_task):
    """Test deleting own comment"""
    UserProjectPermissions.objects.create(user=user, project=project, can_view=True, can_edit=True)

    comment = TaskComment.objects.create(project_task=project_task, user=user, comment_text="Test comment")

    client.login(username=user.username, password="password")

    url = reverse(
        "projects:checklist:comment_delete",
        kwargs={"project_id": project.id, "step_id": project_step.id, "task_id": project_task.id, "comment_id": comment.id},
    )
    response = client.delete(url)

    assert response.status_code == 200

    comment.refresh_from_db()
    assert comment.is_deleted is True


@pytest.mark.django_db
def test_task_comment_admin_can_delete_any_comment(
    client, user, admin_user, project, admin_permission, project_step, project_task
):
    """Test that admin can delete any comment"""
    # Create comment by regular user
    comment = TaskComment.objects.create(project_task=project_task, user=user, comment_text="User comment")

    client.login(username=admin_user.username, password="password")

    url = reverse(
        "projects:checklist:comment_delete",
        kwargs={"project_id": project.id, "step_id": project_step.id, "task_id": project_task.id, "comment_id": comment.id},
    )
    response = client.delete(url)

    assert response.status_code == 200

    comment.refresh_from_db()
    assert comment.is_deleted is True


# ListStepView Tests


@pytest.mark.django_db
def test_list_step_view_requires_read_permission(client, user, project):
    """Test that list steps requires read permission"""
    client.login(username=user.username, password="password")

    url = reverse("projects:checklist:list_steps", kwargs={"project_id": project.id})
    response = client.get(url)

    assert response.status_code == 403


@pytest.mark.django_db
def test_list_step_view(client, user, project, permission, project_step):
    """Test listing project steps"""
    client.login(username=user.username, password="password")

    url = reverse("projects:checklist:list_steps", kwargs={"project_id": project.id})
    response = client.get(url)

    assert response.status_code == 200
    assert "steps" in response.context
    assert project_step in response.context["steps"]
