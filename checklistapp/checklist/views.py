from accounts.models import UserProjectPermissions
from core.mixins import (
    CommonContextMixin,
    OwnerOrAdminMixin,
    ProjectAdminRequiredMixin,
    ProjectEditRequiredMixin,
    ProjectReadRequiredMixin,
)
from django.contrib import messages
from django.db import models, transaction
from django.db.models import Count, Max
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render
from django.template.loader import render_to_string
from django.views import View
from django.views.generic import (
    CreateView,
    DeleteView,
    ListView,
    UpdateView,
)
from django.views.generic.base import ContextMixin
from django_htmx.http import reswap
from projects.models import Project
from templates_management.models import StepTemplate

from .models import ProjectStep, ProjectTask, TaskComment


class AddProjectStepView(ProjectAdminRequiredMixin, View):
    """
    View to handle adding a new step to a project via HTMX.
    Expects POST data with 'step_template_id' and optional 'override_name'.
    Returns HTML fragment for the new step card that will be inserted via HTMX.
    If it's the first step, also returns the empty state replacement.
    """

    def post(self, request, project_id):
        project = Project.objects.get(pk=project_id)
        if not project:
            messages.error(request, "Project not found.")
            return reswap(HttpResponse(status=200), "none")

        step_template_id = request.POST.get("step_template_id")
        override_name = request.POST.get("override_name", "").strip()

        try:
            step_template = StepTemplate.objects.get(id=step_template_id, is_active=True)
            if not step_template:
                messages.error(request, "Step not found.")
                return reswap(HttpResponse(status=200), "none")

            # Determine step order and count
            result = ProjectStep.objects.filter(project=project).aggregate(max_order=Max("order"), total=Count("id"))

            current_max_order = result["max_order"] or 0
            count_step = result["total"]

            # Use override name or default template name
            step_title = override_name if override_name else step_template.title

            # Create the project step
            project_step = ProjectStep.objects.create(
                project=project,
                description=step_template.description,
                step_template=step_template,
                title=step_title,
                icon=getattr(step_template, "icon", "📋"),
                order=current_max_order + 1,
            )

            # Create tasks from template
            task_templates = step_template.tasks.filter(is_active=True).order_by("order")
            for j, task_template in enumerate(task_templates, start=1):
                ProjectTask.objects.create(
                    project_step=project_step,
                    task_template=task_template,
                    title=task_template.title,
                    info_text=task_template.info_text,
                    help_url=task_template.help_url,
                    work_url=task_template.work_url,
                    order=j,
                )
            messages.success(request, "Step added successfully.")

            # Compute new step counter HTML that will be updated OOB
            step_counter = render_to_string(
                "projects/partials/project_step_form.html#counter_step",
                {
                    "count": count_step + 1,
                },
            )

            # If it's the first step, change the hx-swap to replace the empty state div
            if current_max_order == 0:
                step_content = render_to_string(
                    "projects/partials/project_step_form.html#step_row",
                    {"step": project_step, "project": project},
                    request=request,
                )
                response = HttpResponse(step_counter + step_content)
                return reswap(response, "innerHTML")

            # Return HTML fragment for the new step card
            step_content = render_to_string(
                "projects/partials/project_step_form.html#step_row",
                {"step": project_step, "project": project},
                request=request,
            )
            return HttpResponse(step_counter + step_content)

        except Exception:
            messages.error(request, "Something went wrong when adding the step to the project.")
            return reswap(HttpResponse(status=200), "none")


class EditProjectStepsView(ProjectAdminRequiredMixin, View):
    def post(self, request, project_id, step_id):
        step = get_object_or_404(ProjectStep, pk=step_id)

        if step.project.id != project_id:
            messages.error("Invalid project ID")
            return reswap(HttpResponse(status=200), "none")

        new_title = request.POST.get("title", "").strip()
        if new_title:
            step.title = new_title
            step.save()
            return render(request, 'projects/partials/tasks_page.html#step_title_display', {'step': step})

        new_description = request.POST.get("description")
        if new_description is not None:
            step.description = new_description
            step.save()
            return render(request, 'projects/partials/tasks_page.html#step_description_display', {'step': step})

        return reswap(HttpResponse(status=200), "none")

class ReorderProjectStepsView(ProjectAdminRequiredMixin, View):
    """
    Handle reordering of project steps via HTMX.
    Expects POST data with 'step_order' as a list of step IDs in the new order.
    """

    def post(self, request, project_id):
        project = get_object_or_404(Project, pk=project_id)

        step_order = request.POST.getlist("step_order", [])
        step_order = [int(s) for s in step_order]  # Ensure int

        with transaction.atomic():
            # Fetch all steps in one query
            steps = ProjectStep.objects.filter(project=project, pk__in=step_order).in_bulk(field_name="pk")

            # Phase 1 : temporary order to avoid unique collision
            for tmp_idx, step in enumerate(steps.values(), start=10000):
                step.order = tmp_idx

            ProjectStep.objects.bulk_update(steps.values(), ["order"])

            # Phase 2 : assign final order
            for index, step_id in enumerate(step_order, start=1):
                steps[step_id].order = index

            ProjectStep.objects.bulk_update(steps.values(), ["order"])

        return HttpResponse("")


class RemoveProjectStepView(ProjectAdminRequiredMixin, View):
    """Handle removing a step from a project via HTMX"""

    def delete(self, request, project_id, step_id):
        project = get_object_or_404(Project, pk=project_id)
        project_step = get_object_or_404(ProjectStep, id=step_id, project=project)

        try:
            project_step.delete()

            # Check if there are any steps left
            remaining_steps = ProjectStep.objects.filter(project=project).count()

            # Compute new step counter HTML that will be updated OOB
            step_counter = render_to_string(
                "projects/partials/project_step_form.html#counter_step",
                {
                    "count": remaining_steps,
                },
            )

            messages.success(request, "Step deleted successfully.")
            if not remaining_steps:
                # Return empty state HTML
                empty_html = render_to_string("projects/partials/project_step_form.html#step_empty")
                return HttpResponse(step_counter + empty_html)
            else:
                # Return empty response (card will be removed by HTMX)
                return HttpResponse(step_counter)

        except Exception:
            messages.error(request, "Something went wrong when deleting the step from the project.")
            return reswap(HttpResponse(status=200), "none")


class AddProjectTaskView(ProjectEditRequiredMixin, CommonContextMixin, ContextMixin, View):
    """Handle adding a task to a project step via HTMX"""

    def post(self, request, project_id, step_id):
        project_step = get_object_or_404(ProjectStep, id=step_id)
        title = request.POST.get("title", "").strip()

        if not title:
            messages.error(request, "Task title cannot be empty.")
            return reswap(HttpResponse(status=200), "none")

        try:
            context = self.get_context_data()

            # Determine task order
            current_max_order = (
                ProjectTask.objects.filter(project_step=project_step).aggregate(models.Max("order"))["order__max"] or 0
            )

            # Create the project task
            project_task = ProjectTask.objects.create(
                project_step=project_step,
                title=title,
                info_url=None,
                order=current_max_order + 1,
                manually_created=True,
            )
            context["task"] = project_task

            messages.success(request, "Task added successfully.")

            # Return HTML fragment for the new task row
            return render(
                request,
                "projects/partials/task_row.html",
                context,
            )

        except Exception:
            messages.error(request, "Something went wrong when adding the task to the step.")
            return reswap(HttpResponse(status=200), "none")


class UpdateProjectTaskView(ProjectEditRequiredMixin, CommonContextMixin, ContextMixin, View):
    """Handle updating a task's status via HTMX"""

    def post(self, request, project_id, step_id, task_id):
        project_task = ProjectTask.objects.get(
            id=task_id,
            project_step__id=step_id,
            project_step__project__id=project_id,
        )
        step = ProjectStep.objects.get(id=step_id, project__id=project_id)

        context = self.get_context_data()
        context["task"] = project_task

        if project_task is None:
            messages.error(request, "Task not found.")
            return render(
                request,
                "projects/partials/task_row.html",
                context,
            )

        new_status = request.POST.get("status", "").strip()

        if new_status not in ["done", "na"]:
            messages.error(request, "Invalid status value.")
            return render(
                request,
                "projects/partials/task_row.html",
                context,
            )

        try:
            if new_status == project_task.status:
                project_task.mark_pending()
            elif new_status == "done":
                project_task.mark_done(request.user)
            elif new_status == "na":
                project_task.mark_na(request.user)
        except Exception as e:
            messages.error(request, str(e))
            return reswap(HttpResponse(status=200), "none")

        row_html = render_to_string("projects/partials/task_row.html", context)

        step_html = render_to_string(
            "projects/partials/project_content.html#step_item",
            {
                **context,
                "oob": True,
                "project": step.project,
                "step": step,
                "active_step_id": step.id,
            },
        )
        progress_html = render_to_string(
            "projects/partials/tasks_page.html#progress_bar",
            {
                **context,
                "oob": True,
                "completion": step.get_completion_percentage(),
                "text": step.get_progress_text(),
            },
        )

        return HttpResponse(row_html + step_html + progress_html)


class DeleteProjectTaskView(ProjectEditRequiredMixin, CommonContextMixin, ContextMixin, View):
    """Handle deleting a task from a project step via HTMX"""

    def delete(self, request, project_id, step_id, task_id):
        context = self.get_context_data()

        project_task = get_object_or_404(
            ProjectTask,
            id=task_id,
            project_step__id=step_id,
            project_step__project__id=project_id,
        )
        context["task"] = project_task

        if not project_task.manually_created:
            messages.error(request, "Only manually created tasks can be deleted.")
            return reswap(HttpResponse(status=200), "none")

        try:
            project_task.delete()
            return HttpResponse("")

        except Exception:
            messages.error(request, "Something went wrong when deleting the task from the step.")
            return reswap(HttpResponse(status=200), "none")


def toggle_task_form(request, project_id, step_id):
    """
    Toggle visibility of the new task form via HTMX.
    Used in the project detail view.
    """
    show_form = request.GET.get("show_form", "") == "1"

    return render(
        request,
        "projects/partials/tasks_page.html#new_task_toggle",
        {"project_id": project_id, "step_id": step_id, "show_form": show_form},
    )


class TaskCommentListView(ProjectReadRequiredMixin, CommonContextMixin, ListView):
    model = TaskComment
    template_name = "projects/partials/comment_list.html"
    context_object_name = "comments"

    def get_queryset(self):
        task_id = self.kwargs.get("task_id")
        result = TaskComment.objects.filter(
            project_task_id=task_id,
            deleted_at__isnull=True,
        ).select_related("user", "project_task")

        return result

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["task"] = get_object_or_404(ProjectTask, id=context.get("task_id"))
        return context


class TaskCommentCreateView(ProjectEditRequiredMixin, CommonContextMixin, CreateView):
    model = TaskComment
    fields = ["comment_text"]
    template_name = "projects/partials/comment_form.html"

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        return data

    def form_valid(self, form):
        context = self.get_context_data()

        form.instance.user = self.request.user
        form.instance.project_task_id = context.get("task_id")
        self.object = form.save()

        context["comment"] = self.object
        context["user"] = self.request.user

        html = render_to_string("projects/partials/comment_item.html", context)
        return HttpResponse(html)


class TaskCommentUpdateView(OwnerOrAdminMixin, CommonContextMixin, UpdateView):
    model = TaskComment
    fields = ["comment_text"]
    pk_url_kwarg = "comment_id"
    template_name = "projects/partials/comment_form_edit.html"
    object_model = TaskComment  # object used to check if we are owner
    owner_field = "user"
    object_key_name = "comment_id"

    def get_queryset(self):
        # Only allow editing own comments
        return TaskComment.objects.filter(user=self.request.user, deleted_at__isnull=True)

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        return data

    def form_valid(self, form):
        self.object = form.save()

        html = render_to_string(
            "projects/partials/comment_item.html",
            {
                **self.get_context_data(),
                "comment": self.object,
                "user": self.request.user,
            },
        )
        return HttpResponse(html)


class TaskCommentDeleteView(ProjectEditRequiredMixin, DeleteView):
    model = TaskComment
    pk_url_kwarg = "comment_id"

    def get_queryset(self):
        requestor = self.request.user
        project_id = self.kwargs.get("project_id")

        user_permission = UserProjectPermissions.objects.get_user_permissions(requestor, project_id)

        if user_permission.is_admin:
            return TaskComment.objects.filter(deleted_at__isnull=True)

        # Only allow deleting own comments
        return TaskComment.objects.filter(user=self.request.user, deleted_at__isnull=True)

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.soft_delete()
        return HttpResponse("")

# View to return inline form
def edit_step_description_form(request, project_id, step_id):
    step = ProjectStep.objects.filter(pk=step_id, project__id=project_id).first()

    if not step:
        messages.error(request, "Task or Project not found.")
        return reswap(HttpResponse(status=200), "none")

    return render(request, "projects/partials/tasks_page.html#step_description_form", context={
        "step": step
    })

def edit_step_title_form(request, project_id, step_id):
    step = ProjectStep.objects.filter(pk=step_id, project__id=project_id).first()

    if not step:
        messages.error(request, "Task or Project not found.")
        return reswap(HttpResponse(status=200), "none")

    return render(request, "projects/partials/tasks_page.html#step_title_form", context={
        "step": step
    })


def get_step_title_display(request, project_id, step_id):
    step = ProjectStep.objects.filter(pk=step_id, project__id=project_id).first()

    if not step:
        messages.error(request, "Task or Project not found.")
        return reswap(HttpResponse(status=200), "none")

    return render(request, "projects/partials/tasks_page.html#step_title_display", context={
        "step": step
    })

def get_step_description_display(request, project_id, step_id):
    step = ProjectStep.objects.filter(pk=step_id, project__id=project_id).first()

    if not step:
        messages.error(request, "Task or Project not found.")
        return reswap(HttpResponse(status=200), "none")

    return render(request, "projects/partials/tasks_page.html#step_description_display", context={
        "step": step
    })