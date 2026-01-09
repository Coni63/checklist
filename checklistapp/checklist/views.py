import logging

from accounts.services import AccountService
from common.views import editable_header_view
from core.exceptions import InvalidParameterError
from core.mixins import (
    CommonContextMixin,
    OwnerOrAdminMixin,
    ProjectAdminRequiredMixin,
    ProjectEditRequiredMixin,
    ProjectReadRequiredMixin,
)
from django.contrib import messages
from django.http import HttpResponse
from django.shortcuts import render
from django.template.loader import render_to_string
from django.urls import reverse
from django.views import View
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    UpdateView,
)
from django.views.generic.base import ContextMixin
from django_htmx.http import reswap
from projects.models import Project
from projects.services import ProjectService

from .models import ProjectStep, TaskComment
from .services import ChecklistService, CommentService, TaskService

logger = logging.getLogger(__name__)


class ListProjectStepView(ProjectAdminRequiredMixin, CommonContextMixin, DetailView):
    """
    View to display project details, including steps and tasks.
    Supports HTMX requests to load tasks for a specific step.
    """

    model = Project
    template_name = "checklist/partials/project_step_form.html"
    context_object_name = "project"
    pk_url_kwarg = "project_id"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["available_templates"] = ChecklistService.get_template(load_tasks=True)
        context["project_steps"] = ChecklistService.get_steps_for_project(self.object)
        return context


class ProjectStepDetailView(ProjectReadRequiredMixin, CommonContextMixin, DetailView):
    """
    View to display project details, including steps and tasks.
    Supports HTMX requests to load tasks for a specific step.
    """

    model = Project
    template_name = "checklist/checklist_detail.html"
    context_object_name = "project"
    pk_url_kwarg = "project_id"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["steps"] = ChecklistService.get_steps_for_project(self.object)
        context["completion"] = self.object.get_completion_percentage()

        # Si un step_id est dans l'URL, on charge ce step
        step_id = context.get("step_id")
        if step_id:
            context["edit_endpoint_base"] = reverse(
                "projects:checklist:step_header_edit", kwargs={"project_id": context["project_id"], "step_id": step_id}
            )
            context["can_edit"] = "edit" in context["roles"]
            step = ChecklistService.get_step(self.object.id, step_id, prefetch_related=["tasks"])
            context["active_step"] = step
            context["active_step_id"] = step_id
            context["tasks"] = step.tasks.all()

        return context

    def render_to_response(self, context, **response_kwargs):
        # Si c'est une requête HTMX, retourne seulement le partial des tâches
        if self.request.headers.get("HX-Request"):
            return render(self.request, "checklist/partials/tasks_page.html", context)

        # Sinon retourne la page complète
        return super().render_to_response(context, **response_kwargs)


class AddProjectStepView(ProjectAdminRequiredMixin, View):
    """
    View to handle adding a new step to a project via HTMX.
    Expects POST data with 'step_template_id' and optional 'override_name'.
    Returns HTML fragment for the new step card that will be inserted via HTMX.
    If it's the first step, also returns the empty state replacement.
    """

    def post(self, request, project_id):
        try:
            project = ProjectService.get(project_id)

            step_template_id = request.POST.get("step_template_id")
            override_name = request.POST.get("override_name", "").strip()

            result = ChecklistService.add_step_to_project(
                project=project, template_id=step_template_id, custom_title=override_name
            )

            project_step = result["project_step"]
            count_step = result["count_step"]

            # Compute new step counter HTML that will be updated OOB
            step_counter = render_to_string(
                "checklist/partials/project_step_form.html#counter_step",
                {"count": count_step + 1, "oob": True},
            )

            # If it's the first step, change the hx-swap to replace the empty state div
            step_content = render_to_string(
                "checklist/partials/project_step_form.html#step_row",
                {"step": project_step, "project": project},
                request=request,
            )

            messages.success(request, "Step added successfully.")

            response = HttpResponse(step_counter + step_content)

            # If it's the first step, change the hx-swap to replace the empty state div
            return reswap(response, "innerHTML") if count_step == 0 else response

        except Exception as e:
            logger.error(e)
            if hasattr(e, "custom"):
                messages.error(request, str(e))
            else:
                messages.error(request, "Something went wrong when adding the step to the project.")
            return reswap(HttpResponse(status=200), "none")


class ReorderProjectStepsView(ProjectAdminRequiredMixin, View):
    """
    Handle reordering of project steps via HTMX.
    Expects POST data with 'step_order' as a list of step IDs in the new order.
    """

    def post(self, request, project_id):
        try:
            project = ProjectService.get(project_id)
            try:
                order = request.POST.getlist("step_order", [])
                order = [int(s) for s in order]  # Ensure int
            except Exception:
                raise InvalidParameterError("Invalid 'order' input provided")

            ChecklistService.reorder_inventory(project, order)

            return HttpResponse("")

        except Exception as e:
            logger.error(e)
            if hasattr(e, "custom"):
                messages.error(request, str(e))
            else:
                messages.error(request, "Something went wrong when reordering the inventory.")
            return reswap(HttpResponse(status=200), "none")


class RemoveProjectStepView(ProjectAdminRequiredMixin, View):
    """Handle removing a step from a project via HTMX"""

    def delete(self, request, project_id, step_id):
        try:
            ChecklistService.delete_step(project_id, step_id)

            # Check if there are any steps left
            remaining_steps = ChecklistService.get_step(project_id).count()

            # Compute new step counter HTML that will be updated OOB
            step_counter = render_to_string(
                "checklist/partials/project_step_form.html#counter_step",
                {"count": remaining_steps, "oob": True},
            )

            messages.success(request, "Step deleted successfully.")
            if not remaining_steps:
                # Return empty state HTML
                empty_html = render_to_string("checklist/partials/project_step_form.html#step_empty")
                return HttpResponse(step_counter + empty_html)
            else:
                # Return empty response (card will be removed by HTMX)
                return HttpResponse(step_counter)

        except Exception as e:
            logger.error(e)
            if hasattr(e, "custom"):
                messages.error(request, str(e))
            else:
                messages.error(request, "Something went wrong when removing the step from the project.")
            return reswap(HttpResponse(status=200), "none")


class AddProjectTaskView(ProjectEditRequiredMixin, CommonContextMixin, ContextMixin, View):
    """Handle adding a task to a project step via HTMX"""

    def post(self, request, project_id, step_id):
        try:
            title = request.POST.get("title", "").strip()
            if not title:
                raise InvalidParameterError("Task title cannot be empty")

            context = self.get_context_data()
            context["task"] = TaskService.add_task_to_step(project_id, step_id, title)

            messages.success(request, "Task added successfully.")

            # Return HTML fragment for the new task row
            return render(
                request,
                "checklist/partials/task_row.html",
                context,
            )
        except Exception as e:
            logger.error(e)
            if hasattr(e, "custom"):
                messages.error(request, str(e))
            else:
                messages.error(request, "Something went wrong when adding the task to the step.")
            return reswap(HttpResponse(status=200), "none")


class UpdateProjectTaskView(ProjectEditRequiredMixin, CommonContextMixin, ContextMixin, View):
    """Handle updating a task's status via HTMX"""

    def post(self, request, project_id, step_id, task_id):
        try:
            context = self.get_context_data()
            new_status = request.POST.get("status", "").strip()
            if new_status not in ["done", "na"]:
                raise InvalidParameterError("Invalid status value.")

            context["task"] = TaskService.update_task_status(project_id, step_id, task_id, new_status, request.user)
            step = ChecklistService.get_step(project_id, step_id)

            row_html = render_to_string("checklist/partials/task_row.html", context)

            step_html = render_to_string(
                "checklist/partials/step_cards.html#step_item",
                {
                    **context,
                    "oob": True,
                    "project": step.project,
                    "step": step,
                    "active_step_id": step.id,
                },
            )
            progress_html = render_to_string(
                "checklist/partials/tasks_page.html#progress_bar",
                {
                    **context,
                    "oob": True,
                    "completion": step.get_completion_percentage(),
                    "text": step.get_progress_text(),
                },
            )

            return HttpResponse(row_html + step_html + progress_html)
        except Exception as e:
            logger.error(e)
            if hasattr(e, "custom"):
                messages.error(request, str(e))
            else:
                messages.error(request, "Something went wrong when updating the task status.")
            return reswap(HttpResponse(status=200), "none")


class DeleteProjectTaskView(ProjectEditRequiredMixin, CommonContextMixin, ContextMixin, View):
    """Handle deleting a task from a project step via HTMX"""

    def delete(self, request, project_id, step_id, task_id):
        try:
            TaskService.delete_task(project_id, step_id, task_id, request.user)
            return HttpResponse("")
        except Exception as e:
            logger.error(e)
            if hasattr(e, "custom"):
                messages.error(request, str(e))
            else:
                messages.error(request, "Something went wrong when deleting the task.")
            return reswap(HttpResponse(status=200), "none")


def toggle_task_form(request, project_id, step_id):
    """
    Toggle visibility of the new task form via HTMX.
    Used in the project detail view.
    """
    show_form = request.GET.get("show_form", "") == "1"

    return render(
        request,
        "checklist/partials/tasks_page.html#new_task_toggle",
        {"project_id": project_id, "step_id": step_id, "show_form": show_form},
    )


class ListStepView(ProjectReadRequiredMixin, CommonContextMixin, ListView):
    """
    View to display project details, including steps and tasks.
    Supports HTMX requests to load tasks for a specific step.
    """

    model = ProjectStep
    template_name = "checklist/partials/step_cards.html"
    context_object_name = "steps"
    pk_url_kwarg = "project_id"

    def get_queryset(self):
        project_id = self.kwargs.get(self.pk_url_kwarg)
        return ChecklistService.get_step(project_id)


class TaskCommentListView(ProjectReadRequiredMixin, CommonContextMixin, ListView):
    model = TaskComment
    template_name = "checklist/partials/comment_list.html"
    context_object_name = "comments"

    def get_queryset(self):
        project_id = self.kwargs.get("project_id")
        step_id = self.kwargs.get("step_id")
        task_id = self.kwargs.get("task_id")

        result = CommentService.get_comments_on_task(project_id, step_id, task_id)
        return result

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["task"] = TaskService.get_task(context.get("project_id"), context.get("step_id"), context.get("task_id"))
        return context


class TaskCommentCreateView(ProjectEditRequiredMixin, CommonContextMixin, CreateView):
    model = TaskComment
    fields = ["comment_text"]
    template_name = "checklist/partials/comment_form.html"

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

        html = render_to_string("checklist/partials/comment_item.html", context)
        return HttpResponse(html)


class TaskCommentUpdateView(OwnerOrAdminMixin, CommonContextMixin, UpdateView):
    model = TaskComment
    fields = ["comment_text"]
    pk_url_kwarg = "comment_id"
    template_name = "checklist/partials/comment_form_edit.html"
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
            "checklist/partials/comment_item.html",
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

        user_permission = AccountService.get_permission_for_user_project(requestor, project_id)

        # Admin can delete any non deleted comment
        if user_permission.is_admin:
            return TaskComment.objects.filter(deleted_at__isnull=True)

        # Only allow deleting own comments
        return TaskComment.objects.filter(user=self.request.user, deleted_at__isnull=True)

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.soft_delete()
        return HttpResponse("")


class StepHeaderEditView(
    ProjectReadRequiredMixin,
    CommonContextMixin,
    ContextMixin,
    View,
):
    def post(self, request, *args, **kwargs):
        return self._inner(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        return self._inner(request, *args, **kwargs)

    def _inner(self, request, *args, **kwargs):
        context = self.get_context_data()

        project_id = context["project_id"]
        step_id = context["step_id"]
        can_edit = "edit" in context["roles"]

        edit_endpoint_base = reverse(
            "projects:checklist:step_header_edit", kwargs={"project_id": project_id, "step_id": step_id}
        )

        return editable_header_view(
            request=request,
            model_class=ProjectStep,
            template_path="common/partials/editable_header.html",
            can_edit=can_edit,
            extra_context={"project_id": project_id, "step_id": step_id},
            filter_kwargs={"project__id": project_id, "pk": step_id},
            edit_endpoint_base=edit_endpoint_base,
        )
