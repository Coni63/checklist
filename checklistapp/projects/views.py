from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import models, transaction
from django.db.models import Count, Max
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    UpdateView,
)
from django_htmx.http import reswap
from templates_management.models import StepTemplate

from .forms import ProjectCreationForm
from .models import Project, ProjectStep, ProjectTask


class ProjectListView(LoginRequiredMixin, ListView):
    """
    View to list all projects for the logged-in user,
    with optional filtering by status.
    """

    model = Project
    template_name = "projects/project_list.html"
    context_object_name = "projects"

    def get_queryset(self):
        qs = super().get_queryset()
        status = self.request.GET.get("status", "active")
        if status and status != "all":
            qs = qs.filter(status=status)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["status"] = self.request.GET.get("status", "active")  # Valeur par défaut si non précisé
        return context


class ProjectCreateView(LoginRequiredMixin, CreateView):
    """
    View to create a new project. Returns a page and a form.
    ️On success, redirects to the project edit page.
    """

    model = Project
    form_class = ProjectCreationForm
    template_name = "projects/project_create.html"

    def get_success_url(self):
        return reverse_lazy("projects:project_edit", kwargs={"project_id": self.object.pk})

    def form_valid(self, form):
        form.instance.owner = self.request.user
        messages.success(self.request, f'Project "{form.instance.name}" created successfully!')
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, "Please correct the errors below.")
        return super().form_invalid(form)


class ProjectEditView(LoginRequiredMixin, UpdateView):
    """
    View to edit an existing project, including its steps and tasks.
    It reuses the ProjectCreationForm for project info.
    Returns a page with the project form and step/task management.
    """

    model = Project
    form_class = ProjectCreationForm
    template_name = "projects/project_edit.html"
    context_object_name = "project"
    pk_url_kwarg = "project_id"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Get all available step templates
        context["available_templates"] = StepTemplate.objects.filter(is_active=True).order_by("default_order")

        # Get current project steps
        context["project_steps"] = (
            ProjectStep.objects.filter(project=self.object)
            .select_related("step_template")
            .prefetch_related("tasks")
            .order_by("order")
        )

        return context

    def get_success_url(self):
        messages.success(self.request, f'Project "{self.object.name}" updated successfully!')
        return reverse_lazy("projects:project_edit", kwargs={"project_id": self.object.pk})


class AddProjectStepView(LoginRequiredMixin, View):
    """
    View to handle adding a new step to a project via HTMX.
    Expects POST data with 'step_template_id' and optional 'override_name'.
    Returns HTML fragment for the new step card that will be inserted via HTMX.
    If it's the first step, also returns the empty state replacement.
    """

    def post(self, request, project_id):
        project = get_object_or_404(Project, pk=project_id)
        step_template_id = request.POST.get("step_template_id")
        override_name = request.POST.get("override_name", "").strip()

        try:
            step_template = get_object_or_404(StepTemplate, id=step_template_id, is_active=True)

            # Determine step order and count
            result = ProjectStep.objects.filter(project=project).aggregate(max_order=Max("order"), total=Count("id"))

            current_max_order = result["max_order"] or 0
            count_step = result["total"]

            # Use override name or default template name
            step_title = override_name if override_name else step_template.title

            # Create the project step
            project_step = ProjectStep.objects.create(
                project=project,
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
                    info_url=getattr(task_template, "info_url", ""),
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

        except Exception as e:
            messages.error(request, "Something went wrong when adding the step to the project.")
            # TODO: return proper HTMX error response
            return HttpResponse(f'<div class="error-message">Error: {str(e)}</div>', status=400)


class ReorderProjectStepsView(LoginRequiredMixin, View):
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


class RemoveProjectStepView(LoginRequiredMixin, View):
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

        except Exception as e:
            messages.error(request, "Something went wrong when deleting the step from the project.")
            # TODO: return proper HTMX error response
            return HttpResponse(f'<div class="error-message">Error: {str(e)}</div>', status=400)


class ProjectDetailView(LoginRequiredMixin, DetailView):
    """
    View to display project details, including steps and tasks.
    Supports HTMX requests to load tasks for a specific step.
    """

    model = Project
    template_name = "projects/project_detail.html"
    context_object_name = "project"
    pk_url_kwarg = "project_id"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["steps"] = self.object.steps.prefetch_related("tasks")
        context["completion"] = self.object.get_completion_percentage()
        context["project_id"] = self.kwargs.get("project_id")
        context["step_id"] = self.kwargs.get("step_id")

        # Si un step_id est dans l'URL, on charge ce step
        step_id = self.kwargs.get("step_id")
        if step_id:
            step = get_object_or_404(
                ProjectStep.objects.prefetch_related("tasks"),
                id=step_id,
                project=self.object,
            )
            context["active_step"] = step
            context["active_step_id"] = step_id
            context["tasks"] = step.tasks.all()

        return context

    def render_to_response(self, context, **response_kwargs):
        # Si c'est une requête HTMX, retourne seulement le partial des tâches
        if self.request.headers.get("HX-Request"):
            return render(self.request, "projects/partials/tasks_page.html", context)

        # Sinon retourne la page complète
        return super().render_to_response(context, **response_kwargs)


class ProjectDeleteView(LoginRequiredMixin, DeleteView):
    """View to delete a project."""

    model = Project
    success_url = reverse_lazy("projects:project_list")
    pk_url_kwarg = "project_id"

    def delete(self, request, *args, **kwargs):
        """Override delete to add success/error messages."""
        self.object = self.get_object()

        try:
            self.object.delete()
            messages.success(request, "Project deleted successfully.")

        except Exception:
            messages.error(request, "Something went wrong deleting the project.")

        return redirect(self.success_url)

    # Optional: allow "GET" request to delete (dangerous but sometimes needed for a simple link)
    def get(self, request, *args, **kwargs):
        return self.delete(request, *args, **kwargs)


class AddProjectTaskView(LoginRequiredMixin, View):
    """Handle adding a task to a project step via HTMX"""

    # TODO: adjust & test when developped

    def post(self, request, project_id, step_id):
        project_step = get_object_or_404(ProjectStep, id=step_id)
        title = request.POST.get("title", "").strip()

        if not title:
            messages.error(request, "Task title cannot be empty.")
            # TODO: return proper HTMX error response
            return HttpResponse("", status=400)

        try:
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
            messages.success(request, "Task added successfully.")

            # Return HTML fragment for the new task row
            return render(
                request,
                "projects/partials/task_row.html",
                {"task": project_task},
            )

        except Exception as e:
            messages.error(request, "Something went wrong when adding the task to the step.")
            # TODO: return proper HTMX error response
            return HttpResponse(f'<div class="error-message">Error: {str(e)}</div>', status=400)


class UpdateProjectTaskView(LoginRequiredMixin, View):
    """Handle updating a task's status via HTMX"""

    def post(self, request, project_id, step_id, task_id):
        project_task = ProjectTask.objects.get(
            id=task_id,
            project_step__id=step_id,
            project_step__project__id=project_id,
        )
        step = ProjectStep.objects.get(id=step_id, project__id=project_id)

        if project_task is None:
            messages.error(request, "Task not found.")
            return render(
                request,
                "projects/partials/task_row.html",
                {"task": project_task},
            )

        new_status = request.POST.get("status", "").strip()

        if new_status not in ["unna", "undone", "done", "na"]:
            messages.error(request, "Invalid status value.")
            return render(
                request,
                "projects/partials/task_row.html",
                {"task": project_task},
            )

        try:
            if new_status.startswith("un"):
                project_task.mark_pending()
            elif new_status == "done":
                project_task.mark_done()
            elif new_status == "na":
                project_task.mark_na()
        except Exception as e:
            messages.error(request, str(e))

        row_html = render_to_string("projects/partials/task_row.html", {"task": project_task})

        step_html = render_to_string(
            "projects/partials/project_content.html#step_item",
            {
                "oob": True,
                "project": step.project,
                "step": step,
                "active_step_id": step.id,
            },
        )
        progress_html = render_to_string(
            "projects/partials/tasks_page.html#progress_bar",
            {
                "oob": True,
                "completion": step.get_completion_percentage(),
                "text": step.get_progress_text(),
            },
        )

        return HttpResponse(row_html + step_html + progress_html)


class DeleteProjectTaskView(LoginRequiredMixin, View):
    """Handle deleting a task from a project step via HTMX"""

    # TODO: adjust & test when developped

    def delete(self, request, project_id, step_id, task_id):
        project_task = get_object_or_404(
            ProjectTask,
            id=task_id,
            project_step__id=step_id,
            project_step__project__id=project_id,
        )

        try:
            project_task.delete()
            # Return empty response (row will be removed by HTMX)
            return HttpResponse("")

        except Exception as e:
            messages.error(request, "Something went wrong when deleting the task from the step.")
            # TODO: return proper HTMX error response
            return HttpResponse(f'<div class="error-message">Error: {str(e)}</div>', status=400)


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
