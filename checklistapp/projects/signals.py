from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import ProjectTask

@receiver(post_save, sender=ProjectTask)
def update_step_and_project_status(sender, instance: ProjectTask, **kwargs):
    instance.project_step.project.update_status()