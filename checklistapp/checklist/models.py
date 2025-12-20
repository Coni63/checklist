from django.db import models
from django.utils import timezone
from templates_management.models import StepTemplate, TaskTemplate

"""
Entity relation model:

Project 1---* ProjectStep 1---* ProjectTask

A project contains multiple steps, and each step contains multiple tasks.
A step is derived from a StepTemplate.
Every StepTemplate contains multiple TaskTemplates.
Every ProjectTask is derived from a TaskTemplate by cloning its data.
"""


class ProjectStep(models.Model):
    project = models.ForeignKey("projects.Project", on_delete=models.CASCADE, related_name="steps")
    step_template = models.ForeignKey(
        StepTemplate,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="Template this step was created from",
    )
    title = models.CharField(max_length=200, help_text="Custom title, overrides template name")
    description = models.TextField(blank=True, null=True)
    icon = models.CharField(max_length=10)
    order = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["order"]
        unique_together = ["project", "order"]

    def __str__(self):
        return self.title

    def __repr__(self):
        return f"ProjectStep(id={self.id}, title={self.title})"

    def get_status(self) -> str:
        """
        Determine step status based on task completion
        Returns one of: "Not Started", "In Progress", "Completed"
        """
        total = self.tasks.count()
        if total == 0:
            return "Not Started"
        completed = self.tasks.filter(status__in=["done", "na"]).count()
        if completed == 0:
            return "Not Started"
        elif completed == total:
            return "Completed"
        else:
            return "In Progress"

    def get_progress_text(self) -> str:
        """
        Returns progress text like "3 of 5 tasks" or "No tasks"
        """
        total = self.tasks.count()
        if total == 0:
            return "No tasks"

        completed = self.tasks.filter(status__in=["done", "na"]).count()
        if total > 1:
            return f"{completed} of {total} tasks"
        else:
            return f"{completed} of {total} task"

    def get_completion_percentage(self) -> str:
        """Returns percentage of completed tasks as a string (e.g., '75%')"""
        total = self.tasks.count()
        if total == 0:
            return 0
        completed = self.tasks.filter(status__in=["done", "na"]).count()
        return f"{(completed / total):.0%}"


class ProjectTask(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("done", "Done"),
        ("na", "N/A"),
    ]

    project_step = models.ForeignKey(ProjectStep, on_delete=models.CASCADE, related_name="tasks")
    task_template = models.ForeignKey(
        TaskTemplate,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="Template this task was created from",
    )
    title = models.CharField(max_length=500, help_text="Custom title, overrides template")
    info_text = models.TextField(null=True, blank=True)
    help_url = models.URLField(null=True, help_text="Link to documentation support to perform the task")
    work_url = models.URLField(null=True, help_text="Link to the source where the action must be applied (git, jira, ...)")
    order = models.IntegerField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="pending")
    completed_by = models.ForeignKey("accounts.User", on_delete=models.CASCADE, null=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    manually_created = models.BooleanField(
        default=False,
        help_text="Indicates if the task was created manually or from a template",
    )

    class Meta:
        ordering = ["order"]
        unique_together = ["project_step", "order"]

    def __str__(self):
        return f"{self.project_step.title} - Task {self.order}"

    def mark_done(self, user):
        self.status = "done"
        self.completed_at = timezone.now()
        self.completed_by = user
        self.save()

    def mark_na(self, user):
        self.status = "na"
        self.completed_at = timezone.now()
        self.completed_by = user
        self.save()

    def mark_pending(self):
        self.status = "pending"
        self.completed_at = None
        self.completed_by = None
        self.save()


class TaskComment(models.Model):
    project_task = models.ForeignKey(ProjectTask, on_delete=models.CASCADE, related_name="comments")
    user = models.ForeignKey("accounts.User", on_delete=models.CASCADE)
    comment_text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"Comment by {self.user.username} on {self.project_task}"

    def soft_delete(self):
        self.deleted_at = timezone.now()
        self.save()

    @property
    def is_deleted(self):
        return self.deleted_at is not None

    @property
    def active_comments_count(self):
        return self.comments.filter(deleted_at__isnull=True).count()
