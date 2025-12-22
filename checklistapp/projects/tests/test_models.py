import pytest
from checklist.models import ProjectStep, ProjectTask

from projects.models import Project


@pytest.mark.django_db
def test_project_creation(project):
    """Test basic project creation"""
    assert project.name == "Test Project"
    assert project.status == "active"
    assert project.description == ""
    assert project.id is not None


@pytest.mark.django_db
def test_project_str_representation(project):
    """Test project string representation"""
    assert str(project) == "Test Project"


@pytest.mark.django_db
def test_project_repr(project):
    """Test project repr"""
    expected = f"Project(id={project.id}, name={project.name})"
    assert repr(project) == expected


@pytest.mark.django_db
def test_project_status_choices():
    """Test project status choices"""
    project = Project.objects.create(name="Test Project", status="active")
    assert project.status == "active"

    project.status = "completed"
    project.save()
    project.refresh_from_db()
    assert project.status == "completed"

    project.status = "archived"
    project.save()
    project.refresh_from_db()
    assert project.status == "archived"


@pytest.mark.django_db
def test_project_get_completion_percentage_no_tasks(project):
    """Test completion percentage with no tasks"""
    assert project.get_completion_percentage() == "100%"


@pytest.mark.django_db
def test_project_get_completion_percentage_with_tasks(project, user):
    """Test completion percentage with tasks"""
    # Create a step with tasks
    step = ProjectStep.objects.create(project=project, title="Test Step", icon="📝", order=1)

    # Create 4 tasks
    for i in range(4):
        ProjectTask.objects.create(project_step=step, title=f"Task {i + 1}", order=i + 1, status="pending")

    # No tasks completed
    assert project.get_completion_percentage() == "0%"

    # Mark 2 tasks as done
    tasks = ProjectTask.objects.filter(project_step=step)[:2]
    for task in tasks:
        task.mark_done(user)

    assert project.get_completion_percentage() == "50%"

    # Mark 1 more as N/A
    tasks = ProjectTask.objects.filter(project_step=step, status="pending").first()
    tasks.mark_na(user)

    assert project.get_completion_percentage() == "75%"

    # Mark last task as done
    tasks = ProjectTask.objects.filter(project_step=step, status="pending").first()
    tasks.mark_done(user)

    assert project.get_completion_percentage() == "100%"


@pytest.mark.django_db
def test_project_update_status_to_completed(project, user):
    """Test automatic status update to completed when all tasks are done"""
    step = ProjectStep.objects.create(project=project, title="Test Step", icon="📝", order=1)

    # Create 2 tasks
    task1 = ProjectTask.objects.create(project_step=step, title="Task 1", order=1, status="pending")
    task2 = ProjectTask.objects.create(project_step=step, title="Task 2", order=2, status="pending")

    # Initially active
    assert project.status == "active"

    # Mark both tasks as done
    task1.mark_done(user)
    task2.mark_done(user)

    # Update status
    project.update_status()

    assert project.status == "completed"


@pytest.mark.django_db
def test_project_update_status_to_active(project, user):
    """Test automatic status update to active when tasks are pending"""
    step = ProjectStep.objects.create(project=project, title="Test Step", icon="📝", order=1)

    task1 = ProjectTask.objects.create(project_step=step, title="Task 1", order=1, status="done")

    project.status = "completed"
    project.save()

    # Mark task as pending again
    task1.mark_pending()

    # Update status
    project.update_status()

    assert project.status == "active"


@pytest.mark.django_db
def test_project_update_status_archived_not_changed(project, user):
    """Test that archived projects don't change status"""
    step = ProjectStep.objects.create(project=project, title="Test Step", icon="📝", order=1)

    task = ProjectTask.objects.create(project_step=step, title="Task 1", order=1, status="pending")

    project.status = "archived"
    project.save()

    # Mark task as done
    task.mark_done(user)

    # Try to update status
    project.update_status()

    # Should remain archived
    assert project.status == "archived"
