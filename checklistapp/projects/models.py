from django.utils import timezone
from django.db import models

from accounts.models import User
from templates_management.models import StepTemplate, TaskTemplate


class Project(models.Model):
    STATUS_CHOICES = [
        ("active", "Active"),
        ("completed", "Completed"),
        ("archived", "Archived"),
    ]

    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name="projects")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="active")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.name

    def get_completion_percentage(self):
        total_tasks = ProjectTask.objects.filter(project_step__project=self).count()
        if total_tasks == 0:
            return 0
        completed_tasks = ProjectTask.objects.filter(
            project_step__project=self, status__in=["done", "na"]
        ).count()
        return int((completed_tasks / total_tasks) * 100)


class ProjectStep(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="steps")
    step_template = models.ForeignKey(
        StepTemplate,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="Template this step was created from",
    )
    title = models.CharField(
        max_length=200, help_text="Custom title, overrides template name"
    )
    icon = models.CharField(max_length=10)
    order = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["order"]
        unique_together = ["project", "order"]

    def __str__(self):
        return f"{self.project.name} - {self.title}"

    def get_status(self):
        """Returns: 'not-started', 'in-progress', or 'completed'"""
        total = self.tasks.count()
        if total == 0:
            return "not-started"
        completed = self.tasks.filter(status__in=["done", "na"]).count()
        if completed == 0:
            return "not-started"
        elif completed == total:
            return "completed"
        else:
            return "in-progress"

    def get_progress_text(self):
        total = self.tasks.count()
        completed = self.tasks.filter(status__in=["done", "na"]).count()
        return f"{completed} of {total} tasks"
    
    def get_percentage_complete(self):
        total = self.tasks.count()
        if total == 0:
            return 0
        completed = self.tasks.filter(status__in=["done", "na"]).count()
        # return int((completed / total) * 100)
        return f"{(completed / total):.2%}"

    def get_badge_text(self):
        total = self.tasks.count()
        completed = self.tasks.filter(status__in=["done", "na"]).count()
        if completed == 0:
            return "Not Started"
        elif completed == total:
            return "Completed"
        else:
            return "In progress"
    
class ProjectTask(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("done", "Done"),
        ("na", "N/A"),
    ]

    project_step = models.ForeignKey(
        ProjectStep, on_delete=models.CASCADE, related_name="tasks"
    )
    task_template = models.ForeignKey(
        TaskTemplate,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="Template this task was created from",
    )
    title = models.CharField(
        max_length=500, help_text="Custom title, overrides template"
    )
    info_url = models.URLField(blank=True, null=True)
    order = models.IntegerField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="pending")
    comment = models.TextField(blank=True, help_text="Simple comment field (Phase 1)")
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["order"]
        unique_together = ["project_step", "order"]

    def __str__(self):
        return f"{self.project_step.title} - Task {self.order}"

    def mark_done(self):
        self.status = "done"
        self.completed_at = timezone.now()
        self.save()

    def mark_na(self):
        self.status = "na"
        self.completed_at = timezone.now()
        self.save()

    def mark_pending(self):
        self.status = "pending"
        self.completed_at = None
        self.save()

    def get_classname(self):
        if self.status == "done":
            return "completed"
        elif self.status == "na":
            return "na-status"
        else:
            return ""
        
    def has_comment(self):
        return bool(self.comment.strip())