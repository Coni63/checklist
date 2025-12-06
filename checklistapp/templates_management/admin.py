from django.contrib import admin

from .models import StepTemplate, TaskTemplate


class TaskTemplateInline(admin.TabularInline):
    model = TaskTemplate
    extra = 1
    fields = ["title", "info_url", "order", "is_active"]
    ordering = ["order"]


@admin.register(StepTemplate)
class StepTemplateAdmin(admin.ModelAdmin):
    list_display = ["icon", "name", "task_count", "default_order", "is_active"]
    list_filter = ["is_active"]
    search_fields = ["name", "description"]
    ordering = ["default_order"]
    inlines = [TaskTemplateInline]

    def task_count(self, obj):
        return obj.tasks.filter(is_active=True).count()

    task_count.short_description = "Active Tasks"


@admin.register(TaskTemplate)
class TaskTemplateAdmin(admin.ModelAdmin):
    list_display = ["title", "step_template", "order", "has_info", "is_active"]
    list_filter = ["step_template", "is_active"]
    search_fields = ["title"]
    ordering = ["step_template", "order"]

    def has_info(self, obj):
        return bool(obj.info_url)

    has_info.boolean = True
    has_info.short_description = "Has Info Link"
