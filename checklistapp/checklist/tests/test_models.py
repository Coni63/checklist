import pytest
from django.utils import timezone

from checklist.models import ProjectStep, ProjectTask, TaskComment


@pytest.mark.django_db
def test_project_step_creation(project):
    """Test basic project step creation"""
    step = ProjectStep.objects.create(project=project, title="Test Step", icon="📝", order=1)

    assert step.title == "Test Step"
    assert step.icon == "📝"
    assert step.order == 1
    assert step.project == project
    assert step.description is None


@pytest.mark.django_db
def test_project_step_str_representation(project):
    """Test project step string representation"""
    step = ProjectStep.objects.create(project=project, title="Test Step", icon="📝", order=1)

    assert str(step) == "Test Step"


@pytest.mark.django_db
def test_project_step_repr(project):
    """Test project step repr"""
    step = ProjectStep.objects.create(project=project, title="Test Step", icon="📝", order=1)

    expected = f"ProjectStep(id={step.id}, title={step.title})"
    assert repr(step) == expected


@pytest.mark.django_db
def test_project_step_unique_order_per_project(project, project2):
    from django.db import IntegrityError, transaction

    ProjectStep.objects.create(project=project, title="Step 1", icon="📝", order=1)

    # Isoler la violation de contrainte
    with transaction.atomic():
        with pytest.raises(IntegrityError):
            ProjectStep.objects.create(project=project, title="Step 2", icon="📝", order=1)

    # La transaction principale est saine ici
    step = ProjectStep.objects.create(project=project2, title="Step 1", icon="📝", order=1)
    assert step.order == 1


@pytest.mark.django_db
def test_project_step_get_status_not_started_no_tasks(project):
    """Test step status when no tasks exist"""
    step = ProjectStep.objects.create(project=project, title="Test Step", icon="📝", order=1)

    assert step.get_status() == "Not Started"


@pytest.mark.django_db
def test_project_step_get_status_not_started_with_tasks(project):
    """Test step status when tasks exist but none completed"""
    step = ProjectStep.objects.create(project=project, title="Test Step", icon="📝", order=1)

    ProjectTask.objects.create(project_step=step, title="Task 1", order=1, status="pending")

    assert step.get_status() == "Not Started"


@pytest.mark.django_db
def test_project_step_get_status_in_progress(project, user):
    """Test step status when some tasks are completed"""
    step = ProjectStep.objects.create(project=project, title="Test Step", icon="📝", order=1)

    task1 = ProjectTask.objects.create(project_step=step, title="Task 1", order=1, status="pending")
    task2 = ProjectTask.objects.create(project_step=step, title="Task 2", order=2, status="pending")

    # Mark one task as done
    task1.mark_done(user)

    assert step.get_status() == "In Progress"


@pytest.mark.django_db
def test_project_step_get_status_completed(project, user):
    """Test step status when all tasks are completed"""
    step = ProjectStep.objects.create(project=project, title="Test Step", icon="📝", order=1)

    task1 = ProjectTask.objects.create(project_step=step, title="Task 1", order=1, status="pending")
    task2 = ProjectTask.objects.create(project_step=step, title="Task 2", order=2, status="pending")

    # Mark both tasks as done
    task1.mark_done(user)
    task2.mark_na(user)

    assert step.get_status() == "Completed"


@pytest.mark.django_db
def test_project_step_get_progress_text_no_tasks(project):
    """Test progress text with no tasks"""
    step = ProjectStep.objects.create(project=project, title="Test Step", icon="📝", order=1)

    assert step.get_progress_text() == "No tasks"


@pytest.mark.django_db
def test_project_step_get_progress_text_single_task(project, user):
    """Test progress text with single task"""
    step = ProjectStep.objects.create(project=project, title="Test Step", icon="📝", order=1)

    task = ProjectTask.objects.create(project_step=step, title="Task 1", order=1, status="pending")

    assert step.get_progress_text() == "0 of 1 task"

    task.mark_done(user)
    assert step.get_progress_text() == "1 of 1 task"


@pytest.mark.django_db
def test_project_step_get_progress_text_multiple_tasks(project, user):
    """Test progress text with multiple tasks"""
    step = ProjectStep.objects.create(project=project, title="Test Step", icon="📝", order=1)

    for i in range(5):
        ProjectTask.objects.create(project_step=step, title=f"Task {i + 1}", order=i + 1, status="pending")

    assert step.get_progress_text() == "0 of 5 tasks"

    # Mark 3 tasks as done
    tasks = ProjectTask.objects.filter(project_step=step)[:3]
    for task in tasks:
        task.mark_done(user)

    assert step.get_progress_text() == "3 of 5 tasks"


@pytest.mark.django_db
def test_project_step_get_completion_percentage(project, user):
    """Test completion percentage calculation"""
    step = ProjectStep.objects.create(project=project, title="Test Step", icon="📝", order=1)

    # No tasks
    assert step.get_completion_percentage() == 0

    # Create 4 tasks
    for i in range(4):
        ProjectTask.objects.create(project_step=step, title=f"Task {i + 1}", order=i + 1, status="pending")

    assert step.get_completion_percentage() == "0%"

    # Mark 2 tasks as done
    tasks = ProjectTask.objects.filter(project_step=step)[:2]
    for task in tasks:
        task.mark_done(user)

    assert step.get_completion_percentage() == "50%"


@pytest.mark.django_db
def test_project_task_creation(project):
    """Test basic project task creation"""
    step = ProjectStep.objects.create(project=project, title="Test Step", icon="📝", order=1)

    task = ProjectTask.objects.create(project_step=step, title="Test Task", order=1)

    assert task.title == "Test Task"
    assert task.order == 1
    assert task.status == "pending"
    assert task.project_step == step
    assert task.manually_created is False


@pytest.mark.django_db
def test_project_task_str_representation(project):
    """Test project task string representation"""
    step = ProjectStep.objects.create(project=project, title="Test Step", icon="📝", order=1)

    task = ProjectTask.objects.create(project_step=step, title="Test Task", order=1)

    assert str(task) == "Test Step - Task 1"


@pytest.mark.django_db
def test_project_task_unique_order_per_step(project):
    """Test that order must be unique per step"""
    step = ProjectStep.objects.create(project=project, title="Test Step", icon="📝", order=1)

    ProjectTask.objects.create(project_step=step, title="Task 1", order=1)

    # Can't create another task with same order in same step
    from django.db import IntegrityError

    with pytest.raises(IntegrityError):
        ProjectTask.objects.create(project_step=step, title="Task 2", order=1)


@pytest.mark.django_db
def test_project_task_mark_done(project, user):
    """Test marking a task as done"""
    step = ProjectStep.objects.create(project=project, title="Test Step", icon="📝", order=1)

    task = ProjectTask.objects.create(project_step=step, title="Test Task", order=1, status="pending")

    assert task.status == "pending"
    assert task.completed_by is None
    assert task.completed_at is None

    task.mark_done(user)

    assert task.status == "done"
    assert task.completed_by == user
    assert task.completed_at is not None


@pytest.mark.django_db
def test_project_task_mark_na(project, user):
    """Test marking a task as N/A"""
    step = ProjectStep.objects.create(project=project, title="Test Step", icon="📝", order=1)

    task = ProjectTask.objects.create(project_step=step, title="Test Task", order=1, status="pending")

    task.mark_na(user)

    assert task.status == "na"
    assert task.completed_by == user
    assert task.completed_at is not None


@pytest.mark.django_db
def test_project_task_mark_pending(project, user):
    """Test marking a task back to pending"""
    step = ProjectStep.objects.create(project=project, title="Test Step", icon="📝", order=1)

    task = ProjectTask.objects.create(project_step=step, title="Test Task", order=1, status="pending")

    # Mark as done first
    task.mark_done(user)
    assert task.status == "done"

    # Mark back to pending
    task.mark_pending()

    assert task.status == "pending"
    assert task.completed_by is None
    assert task.completed_at is None


@pytest.mark.django_db
def test_project_task_status_choices(project):
    """Test task status choices"""
    step = ProjectStep.objects.create(project=project, title="Test Step", icon="📝", order=1)

    # Test pending
    task1 = ProjectTask.objects.create(project_step=step, title="Task 1", order=1, status="pending")
    assert task1.status == "pending"

    # Test done
    task2 = ProjectTask.objects.create(project_step=step, title="Task 2", order=2, status="done")
    assert task2.status == "done"

    # Test na
    task3 = ProjectTask.objects.create(project_step=step, title="Task 3", order=3, status="na")
    assert task3.status == "na"


@pytest.mark.django_db
def test_task_comment_creation(project, user):
    """Test basic task comment creation"""
    step = ProjectStep.objects.create(project=project, title="Test Step", icon="📝", order=1)

    task = ProjectTask.objects.create(project_step=step, title="Test Task", order=1)

    comment = TaskComment.objects.create(project_task=task, user=user, comment_text="This is a test comment")

    assert comment.project_task == task
    assert comment.user == user
    assert comment.comment_text == "This is a test comment"
    assert comment.deleted_at is None


@pytest.mark.django_db
def test_task_comment_str_representation(project, user):
    """Test task comment string representation"""
    step = ProjectStep.objects.create(project=project, title="Test Step", icon="📝", order=1)

    task = ProjectTask.objects.create(project_step=step, title="Test Task", order=1)

    comment = TaskComment.objects.create(project_task=task, user=user, comment_text="This is a test comment")

    expected = f"Comment by {user.username} on {task}"
    assert str(comment) == expected


@pytest.mark.django_db
def test_task_comment_soft_delete(project, user):
    """Test soft deleting a comment"""
    step = ProjectStep.objects.create(project=project, title="Test Step", icon="📝", order=1)

    task = ProjectTask.objects.create(project_step=step, title="Test Task", order=1)

    comment = TaskComment.objects.create(project_task=task, user=user, comment_text="This is a test comment")

    assert comment.deleted_at is None
    assert comment.is_deleted is False

    comment.soft_delete()

    assert comment.deleted_at is not None
    assert comment.is_deleted is True


@pytest.mark.django_db
def test_task_comment_is_deleted_property(project, user):
    """Test is_deleted property"""
    step = ProjectStep.objects.create(project=project, title="Test Step", icon="📝", order=1)

    task = ProjectTask.objects.create(project_step=step, title="Test Task", order=1)

    comment = TaskComment.objects.create(project_task=task, user=user, comment_text="Test comment")

    assert comment.is_deleted is False

    comment.deleted_at = timezone.now()
    comment.save()

    assert comment.is_deleted is True


@pytest.mark.django_db
def test_task_comment_ordering(project, user):
    """Test that comments are ordered by created_at"""
    step = ProjectStep.objects.create(project=project, title="Test Step", icon="📝", order=1)

    task = ProjectTask.objects.create(project_step=step, title="Test Task", order=1)

    comment1 = TaskComment.objects.create(project_task=task, user=user, comment_text="First comment")

    comment2 = TaskComment.objects.create(project_task=task, user=user, comment_text="Second comment")

    comments = TaskComment.objects.filter(project_task=task)
    assert list(comments) == [comment1, comment2]


@pytest.mark.django_db
def test_project_step_cascade_delete(project):
    """Test that deleting a step deletes its tasks"""
    step = ProjectStep.objects.create(project=project, title="Test Step", icon="📝", order=1)

    task1 = ProjectTask.objects.create(project_step=step, title="Task 1", order=1)
    task2 = ProjectTask.objects.create(project_step=step, title="Task 2", order=2)

    step.delete()

    assert not ProjectTask.objects.filter(id=task1.id).exists()
    assert not ProjectTask.objects.filter(id=task2.id).exists()


@pytest.mark.django_db
def test_project_task_cascade_delete_comments(project, user):
    """Test that deleting a task deletes its comments"""
    step = ProjectStep.objects.create(project=project, title="Test Step", icon="📝", order=1)

    task = ProjectTask.objects.create(project_step=step, title="Test Task", order=1)

    comment1 = TaskComment.objects.create(project_task=task, user=user, comment_text="Comment 1")
    comment2 = TaskComment.objects.create(project_task=task, user=user, comment_text="Comment 2")

    task.delete()

    assert not TaskComment.objects.filter(id=comment1.id).exists()
    assert not TaskComment.objects.filter(id=comment2.id).exists()
