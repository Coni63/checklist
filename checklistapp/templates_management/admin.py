from django.contrib import admin

from .models import StepTemplate, TaskTemplate


class TaskTemplateInline(admin.TabularInline):
    model = TaskTemplate
    extra = 1
    fields = ["title", "help_url", "work_url", "info_text", "order", "is_active"]
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
    list_display = ["title", "step_template", "order", "has_help_url", "has_work_url", "has_info_text", "is_active"]
    list_filter = ["step_template", "is_active"]
    search_fields = ["title"]
    ordering = ["step_template", "order"]

    def has_help_url(self, obj):
        return bool(obj.help_url)

    def has_work_url(self, obj):
        return bool(obj.work_url)

    def has_info_text(self, obj):
        return bool(obj.info_text)

    has_help_url.boolean = True
    has_help_url.short_description = "Has Help Link"

    has_work_url.boolean = True
    has_work_url.short_description = "Has Work Link"

    has_info_text.boolean = True
    has_info_text.short_description = "Has Info Text"
