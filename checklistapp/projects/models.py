from accounts.models import UserProjectPermissions
from checklist.models import ProjectTask
from django.db import models


class ProjectQuerySet(models.QuerySet):
    def with_status(self, status: str):
        if status != "all":
            return self.filter(status=status)
        return self

    def for_user(self, user, read=True, write=False, admin=False):
        # La logique de permission reste la même
        project_ids = UserProjectPermissions.objects.get_projects_for_user(user, read, write, admin)

        # Le QuerySet actuel (self) est filtré par les IDs autorisés
        return self.filter(id__in=project_ids)

    def sorted(self):
        return self.order_by("-created_at")


class ProjectManager(models.Manager.from_queryset(ProjectQuerySet)):
    pass


class Project(models.Model):
    STATUS_CHOICES = [
        ("active", "Active"),
        ("completed", "Completed"),
        ("archived", "Archived"),
    ]

    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="active")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = ProjectManager()

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.name

    def __repr__(self):
        return f"Project(id={self.id}, name={self.name})"

    def get_completion_percentage(self) -> str:
        """Returns percentage of completed tasks as a string (e.g., '75%')"""
        completed_tasks, total_tasks = self._get_count_tasks()
        if total_tasks == 0:
            return "100%"
        return f"{(completed_tasks / total_tasks):.0%}"

    def _get_count_tasks(self) -> tuple[int, int]:
        """Returns a tuple (completed_tasks, total_tasks)"""
        total_tasks = ProjectTask.objects.filter(project_step__project=self).count()
        if total_tasks == 0:
            return 0, 0
        completed_tasks = ProjectTask.objects.filter(project_step__project=self, status__in=["done", "na"]).count()
        return completed_tasks, total_tasks

    def update_status(self):
        """
        Update project status based on task completion

        This is used by signal handlers to automatically update
        the project status when tasks are marked done or pending.
        """
        if self.status not in ["active", "completed"]:
            return  # Do not update if archived

        completed_tasks, total_tasks = self._get_count_tasks()
        self.status = "completed" if completed_tasks == total_tasks else "active"
        self.save()
