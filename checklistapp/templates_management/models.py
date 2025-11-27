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
        ordering = ['default_order']
        verbose_name = 'Step Template'
        verbose_name_plural = 'Step Templates'
    
    def __str__(self):
        return f"{self.icon} {self.name}"


class TaskTemplate(models.Model):
    step_template = models.ForeignKey(
        StepTemplate,
        on_delete=models.CASCADE,
        related_name='tasks'
    )
    title = models.CharField(max_length=500)
    info_url = models.URLField(blank=True, null=True)
    order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['order']
        verbose_name = 'Task Template'
        verbose_name_plural = 'Task Templates'
    
    def __str__(self):
        return self.title