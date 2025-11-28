from django.db import transaction
from .models import ProjectStep, ProjectTask


class ProjectService:
    @staticmethod
    @transaction.atomic
    def add_step_to_project(project, step_template, custom_title=None, order=None):
        """Add a step instance to a project"""
        if order is None:
            order = project.steps.count() + 1

        title = custom_title or step_template.name

        project_step = ProjectStep.objects.create(
            project=project,
            step_template=step_template,
            title=title,
            icon=step_template.icon,
            order=order,
        )

        # Create tasks from template
        for task_template in step_template.tasks.filter(is_active=True):
            ProjectTask.objects.create(
                project_step=project_step,
                task_template=task_template,
                title=task_template.title,
                info_url=task_template.info_url,
                order=task_template.order,
            )

        return project_step

    @staticmethod
    @transaction.atomic
    def remove_step_from_project(project_step):
        """Remove a step and all its tasks"""
        project_step.delete()

        # Reorder remaining steps
        remaining_steps = project_step.project.steps.all()
        for idx, step in enumerate(remaining_steps, start=1):
            if step.order != idx:
                step.order = idx
                step.save()

    @staticmethod
    @transaction.atomic
    def duplicate_step(project_step, custom_title=None):
        """Duplicate a step with all its tasks"""
        new_title = custom_title or f"{project_step.title} (Copy)"
        new_order = project_step.project.steps.count() + 1

        new_step = ProjectStep.objects.create(
            project=project_step.project,
            step_template=project_step.step_template,
            title=new_title,
            icon=project_step.icon,
            order=new_order,
        )

        # Duplicate tasks
        for task in project_step.tasks.all():
            ProjectTask.objects.create(
                project_step=new_step,
                task_template=task.task_template,
                title=task.title,
                info_url=task.info_url,
                order=task.order,
            )

        return new_step
