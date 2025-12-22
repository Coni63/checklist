from core.exceptions import RecordNotFoundError
from django.db import models, transaction
from django.db.models import Count, Max, Prefetch
from templates_management.models import StepTemplate, TaskTemplate

from .models import ProjectStep, ProjectTask, TaskComment


class ChecklistService:
    @staticmethod
    def get_template(template_id: int | None = None, load_tasks=False):
        qs = StepTemplate.objects.filter(is_active=True).order_by("default_order")
        if load_tasks:
            qs = qs.prefetch_related(Prefetch("tasks", queryset=TaskTemplate.objects.order_by("order")))
        if template_id:
            template = qs.filter(id=template_id).first()
            if not template:
                raise RecordNotFoundError("Inventory template not found.")
            return template
        return qs

    @staticmethod
    def get_step(project_id, step_id: int | None = None, prefetch_related: list[str] | None = None):
        qs = ProjectStep.objects.filter(project__id=project_id)

        if prefetch_related:
            qs = qs.prefetch_related(*prefetch_related)

        if step_id:
            qs = qs.filter(id=step_id).first()
            if not qs:
                raise RecordNotFoundError(f"Step {step_id} not found in project {project_id}.")

        return qs

    @staticmethod
    def get_steps_for_project(project):
        return (
            ProjectStep.objects.filter(project=project)  # i need the project Id that is in url
            .select_related("step_template")
            .prefetch_related("tasks")
            .order_by("order")
        )

    @staticmethod
    @transaction.atomic
    def add_step_to_project(project, template_id, custom_title: str | None = None) -> int:
        step_template = ChecklistService.get_template(template_id, load_tasks=True)

        # Determine inventory order and count
        result = ProjectStep.objects.filter(project=project).aggregate(max_order=Max("order"), total=Count("id"))

        # Reorder does not follow the count, for example we can have task 1, 2, 3. Delete the 2, add a task and we have 1, 3, 4.
        # Max Order is 3 avec the delete but count is 2
        current_max_order = result["max_order"] or 0
        count_step = result["total"]

        # Create the project inventory
        project_step = ProjectStep.objects.create(
            project=project,
            description=step_template.description,
            step_template=step_template,
            title=custom_title or step_template.title,
            icon=getattr(step_template, "icon", "📋"),
            order=current_max_order + 1,
        )

        # Create fields from template
        fields_to_create = [
            ProjectTask(
                project_step=project_step,
                task_template=task_template,
                title=task_template.title,
                info_text=task_template.info_text,
                help_url=task_template.help_url,
                work_url=task_template.work_url,
                order=j,
            )
            for j, task_template in enumerate(step_template.tasks.all())
        ]

        if fields_to_create:
            ProjectTask.objects.bulk_create(fields_to_create)

        return {"project_step": project_step, "count_step": count_step}

    @staticmethod
    @transaction.atomic
    def reorder_inventory(project, ids: list[int]):
        """
        Take a list of ids and change their order to match the index.

        [1, 42, 3] means that step 1 is 1st, 42 is order 2, 3 is order 3
        """
        steps = ProjectStep.objects.filter(project=project, pk__in=ids).in_bulk(field_name="pk")

        # Phase 1 : temporary order to avoid unique collision
        for tmp_idx, step in enumerate(steps.values(), start=10000):
            step.order = tmp_idx

        ProjectStep.objects.bulk_update(steps.values(), ["order"])

        # Phase 2 : assign final order
        for index, step_id in enumerate(ids, start=1):
            steps[step_id].order = index

        ProjectStep.objects.bulk_update(steps.values(), ["order"])

    @staticmethod
    @transaction.atomic
    def delete_step(project_id, step_id):
        inventory = ChecklistService.get_step(project_id, step_id)

        inventory.delete()


class TaskService:
    @staticmethod
    def get_task(project_id, step_id, task_id):
        try:
            return ProjectTask.objects.get(id=task_id, project_step__id=step_id, project_step__project__id=project_id)
        except ProjectTask.DoesNotExist:
            raise RecordNotFoundError("Task not found.")

    @staticmethod
    @transaction.atomic
    def add_task_to_step(project_id, step_id, title):
        project_step = ChecklistService.get_step(project_id, step_id, prefetch_related=["tasks"])

        # Determine task order
        current_max_order = project_step.tasks.aggregate(models.Max("order"))["order__max"] or 0

        # Create the project task
        project_task = ProjectTask.objects.create(
            project_step=project_step,
            title=title,
            order=current_max_order + 1,
            manually_created=True,
        )

        return project_task

    @staticmethod
    @transaction.atomic
    def update_task_status(project_id, step_id, task_id, status, requestor):
        task = TaskService.get_task(project_id, step_id, task_id)

        if status == task.status:
            task.mark_pending()
        elif status == "done":
            task.mark_done(requestor)
        elif status == "na":
            task.mark_na(requestor)

    @staticmethod
    @transaction.atomic
    def delete_task(project_id, step_id, task_id, requestor):
        task = TaskService.get_task(project_id, step_id, task_id)

        if not task.manually_created:
            raise PermissionError("Impossible to delete this task. Only tasks manually created can be deleted")

        task.delete()


class CommentService:
    @staticmethod
    def get_comments_on_task(project_id, step_id, task_id):
        return TaskComment.objects.filter(
            project_task_id=task_id,
            deleted_at__isnull=True,
            project_task__project_step__id=step_id,
            project_task__project_step__project__id=project_id,
        ).select_related("user", "project_task")
