from unittest.mock import Mock

import pytest
from checklist.models import ProjectTask
from django.contrib.admin.sites import AdminSite
from django.forms import modelform_factory

from templates_management.admin import StepTemplateAdmin
from templates_management.models import StepTemplate, TaskTemplate


@pytest.mark.django_db
def test_task_count_only_active(step_template, task_template_1, task_template_2):
    task_template_2.is_active = False
    task_template_2.save()

    admin = StepTemplateAdmin(step_template.__class__, AdminSite())

    assert admin.task_count(step_template) == 1


def get_admin_form(step_template, sync=True):
    Form = modelform_factory(
        StepTemplate,
        fields="__all__",
    )
    form = Form(instance=step_template, data={"title": step_template.title})
    form.is_valid()

    # on injecte le champ custom
    form.cleaned_data["sync_tasks_to_active_projects"] = sync

    form.save_m2m = Mock()

    return form


class DummyFormset:
    def __init__(self, model, deleted_forms=None):
        self.model = model
        self.deleted_forms = deleted_forms or []

    def save(self, commit=True):
        return []


@pytest.mark.django_db
def test_save_related_creates_tasks_for_active_projects(
    admin_user,
    step_template,
    active_project_step,
    inactive_project_step,
    task_template_1,
):
    admin = StepTemplateAdmin(StepTemplate, AdminSite())
    form = get_admin_form(step_template, sync=True)

    admin.save_related(
        request=None,
        form=form,
        formsets=[],
        change=True,
    )

    # Active project got the task
    assert ProjectTask.objects.filter(
        project_step=active_project_step,
        task_template=task_template_1,
    ).exists()

    # Inactive project should not be synced
    assert not ProjectTask.objects.filter(
        project_step=inactive_project_step,
        task_template=task_template_1,
    ).exists()


@pytest.mark.django_db
def test_new_task_template_is_appended_at_end(
    step_template,
    active_project_step,
    task_template_1,
):
    # First sync
    admin = StepTemplateAdmin(StepTemplate, AdminSite())
    form = get_admin_form(step_template, sync=True)
    admin.save_related(None, form, [], True)

    ProjectTask.objects.get(project_step=active_project_step)

    # Add second template
    task2 = TaskTemplate.objects.create(
        step_template=step_template,
        title="Release",
        order=2,
        is_active=True,
    )

    admin.save_related(None, form, [], True)

    tasks = ProjectTask.objects.filter(project_step=active_project_step).order_by("order")

    assert tasks.count() == 2
    assert tasks[0].task_template == task_template_1
    assert tasks[1].task_template == task2


@pytest.mark.django_db
def test_deleted_task_template_is_removed_from_active_projects(
    step_template,
    active_project_step,
    task_template_1,
):
    admin = StepTemplateAdmin(StepTemplate, AdminSite())
    form = get_admin_form(step_template, sync=True)

    # Initial sync
    admin.save_related(None, form, [], True)

    project_task = ProjectTask.objects.get(
        project_step=active_project_step,
        task_template=task_template_1,
    )

    # Simule suppression via formset admin
    class DummyDeletedForm:
        def __init__(self, instance):
            self.instance = instance

    formset = DummyFormset(
        model=TaskTemplate,
        deleted_forms=[DummyDeletedForm(task_template_1)],
    )

    admin.save_related(None, form, [formset], True)

    assert not ProjectTask.objects.filter(pk=project_task.pk).exists()


@pytest.mark.django_db
def test_no_sync_does_nothing(
    step_template,
    active_project_step,
    task_template_1,
):
    admin = StepTemplateAdmin(StepTemplate, AdminSite())
    form = get_admin_form(step_template, sync=False)

    admin.save_related(None, form, [], True)

    assert ProjectTask.objects.count() == 0
