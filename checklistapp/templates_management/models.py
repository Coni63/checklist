from django.db import models


class StepTemplate(models.Model):
    name = models.CharField(max_length=200)
    icon = models.CharField(max_length=10)
    description = models.TextField(blank=True)
    default_order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["default_order"]
        verbose_name = "Step Template"
        verbose_name_plural = "Step Templates"

    def __str__(self):
        return f"{self.icon} {self.name}"


class TaskTemplate(models.Model):
    step_template = models.ForeignKey(StepTemplate, on_delete=models.CASCADE, related_name="tasks")
    title = models.CharField(max_length=500)
    order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    info_text = models.TextField(null=True, blank=True)
    help_url = models.URLField(null=True, help_text="Link to documentation support to perform the task")
    work_url = models.URLField(null=True, help_text="Link to the source where the action must be applied (git, jira, ...)")

    class Meta:
        ordering = ["order"]
        verbose_name = "Task Template"
        verbose_name_plural = "Task Templates"

    def __str__(self):
        return self.title


class InventoryTemplate(models.Model):
    name = models.CharField(max_length=200)
    icon = models.CharField(max_length=10)
    description = models.TextField(blank=True, null=True)
    default_order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Inventory Template"
        verbose_name_plural = "Inventory Templates"
        ordering = ["default_order"]

    def __str__(self):
        return self.name


class TemplateField(models.Model):
    FIELD_TYPES = [
        ("text", "Text"),
        ("number", "Number"),
        ("url", "URL"),
        ("file", "File"),
        ("password", "Password"),
        ("datetime", "Datetime"),
    ]

    template = models.ForeignKey(InventoryTemplate, related_name="fields", on_delete=models.CASCADE)

    # Grouping
    group_name = models.CharField(max_length=100)
    group_order = models.PositiveIntegerField(default=1)

    # Field definition
    field_name = models.CharField(max_length=200)
    field_order = models.PositiveIntegerField(default=1)
    field_type = models.CharField(max_length=20, choices=FIELD_TYPES)
    is_secret = models.BooleanField(default=False, help_text="Only allow admin to see the value")
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Template Field"
        verbose_name_plural = "Template Fields"
        ordering = ["group_order", "field_order"]
        constraints = [
            models.UniqueConstraint(fields=["template", "group_name", "field_name"], name="unique_field_name_and_group_name")
        ]

    def __str__(self):
        return f"{self.group_name} / {self.field_name}"

    def save(self, *args, **kwargs):
        self.group_name = self.group_name.upper().strip()
        super().save(*args, **kwargs)
