from checklist.models import ProjectStep, ProjectTask
from django import forms
from django.contrib import admin
from django.db import models

from .models import InventoryTemplate, StepTemplate, TaskTemplate, TemplateField


class TaskTemplateInline(admin.TabularInline):
    model = TaskTemplate
    extra = 1
    fields = ["title", "help_url", "work_url", "info_text", "order", "is_active"]
    ordering = ["order"]


class StepTemplateAdminForm(forms.ModelForm):
    sync_tasks_to_active_projects = forms.BooleanField(
        initial=True,
        required=False,
        label="Sync tasks to active projects",
        help_text="If checked, added tasks will be appended to active projects, and deleted tasks will be removed from active projects.",
    )

    class Meta:
        model = StepTemplate
        fields = "__all__"


@admin.register(StepTemplate)
class StepTemplateAdmin(admin.ModelAdmin):
    form = StepTemplateAdminForm
    list_display = ["icon", "title", "task_count", "default_order", "is_active"]
    list_filter = ["is_active"]
    search_fields = ["title", "description"]
    ordering = ["default_order"]
    inlines = [TaskTemplateInline]

    def task_count(self, obj):
        return obj.tasks.filter(is_active=True).count()

    task_count.short_description = "Active Tasks"

    def save_related(self, request, form, formsets, change):
        sync = form.cleaned_data.get("sync_tasks_to_active_projects")

        if sync and change:
            # Handle deletions BEFORE super().save_related()
            active_project_steps = ProjectStep.objects.filter(step_template=form.instance, project__status="active")

            for formset in formsets:
                if formset.model == TaskTemplate:
                    for deleted_form in formset.deleted_forms:
                        if deleted_form.instance.pk:
                            # Delete tasks in active projects linked to this template
                            ProjectTask.objects.filter(
                                task_template=deleted_form.instance,
                                project_step__in=active_project_steps,
                            ).delete()

        super().save_related(request, form, formsets, change)

        if sync and change:
            # Handle synchronization of all tasks (new and previously missed)
            # We fetch fresh active_project_steps and current templates
            active_project_steps = ProjectStep.objects.filter(step_template=form.instance, project__status="active")
            # Get all current task templates for this step
            current_task_templates = form.instance.tasks.all()

            for p_step in active_project_steps:
                # Get IDs of task templates already present in this step
                existing_template_ids = set(
                    p_step.tasks.exclude(task_template__isnull=True).values_list("task_template_id", flat=True)
                )

                # Determine the current max order to append new tasks at the end
                current_max_order = p_step.tasks.aggregate(m=models.Max("order"))["m"] or 0

                tasks_to_create = []
                for task_template in current_task_templates:
                    if task_template.id not in existing_template_ids:
                        current_max_order += 1
                        tasks_to_create.append(
                            ProjectTask(
                                project_step=p_step,
                                task_template=task_template,
                                title=task_template.title,
                                info_text=task_template.info_text,
                                help_url=task_template.help_url,
                                work_url=task_template.work_url,
                                order=current_max_order,
                            )
                        )

                if tasks_to_create:
                    ProjectTask.objects.bulk_create(tasks_to_create)


class TemplateFieldInline(admin.TabularInline):
    model = TemplateField
    extra = 1

    fields = [
        "group_name",
        "group_order",
        "field_name",
        "field_order",
        "field_type",
        "is_secret",
    ]

    ordering = ["group_order", "field_order"]


@admin.register(InventoryTemplate)
class MetadataTemplateAdmin(admin.ModelAdmin):
    list_display = ["icon", "title", "description", "default_order", "is_active"]
    search_fields = ["title"]
    inlines = [TemplateFieldInline]
