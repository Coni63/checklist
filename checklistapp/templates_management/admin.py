from django.contrib import admin

from .models import InventoryTemplate, StepTemplate, TaskTemplate, TemplateField


class TaskTemplateInline(admin.TabularInline):
    model = TaskTemplate
    extra = 1
    fields = ["title", "help_url", "work_url", "info_text", "order", "is_active"]
    ordering = ["order"]


@admin.register(StepTemplate)
class StepTemplateAdmin(admin.ModelAdmin):
    list_display = ["icon", "title", "task_count", "default_order", "is_active"]
    list_filter = ["is_active"]
    search_fields = ["title", "description"]
    ordering = ["default_order"]
    inlines = [TaskTemplateInline]

    def task_count(self, obj):
        return obj.tasks.filter(is_active=True).count()

    task_count.short_description = "Active Tasks"


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
