from django.views.generic import ListView, CreateView, DetailView, DeleteView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.contrib import messages

from templates_management.models import StepTemplate
from .models import Project, ProjectStep, ProjectTask
from .forms import ProjectCreationForm
from core.mixins import UserOwnedMixin
from django.shortcuts import get_object_or_404
from django.views import View
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.db import models
from django.template.loader import render_to_string


class ProjectListView(UserOwnedMixin, ListView):
    model = Project
    template_name = "projects/project_list.html"
    context_object_name = "projects"
    paginate_by = 20

    def get_queryset(self):
        qs = super().get_queryset()
        status = self.request.GET.get("status", "active")
        if status and status != "all":
            qs = qs.filter(status=status)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["status"] = self.request.GET.get(
            "status", "active"
        )  # Valeur par défaut si non précisé
        return context


class ProjectCreateView(LoginRequiredMixin, CreateView):
    model = Project
    form_class = ProjectCreationForm
    template_name = "projects/project_create.html"

    def get_success_url(self):
        return reverse_lazy("projects:project_edit", kwargs={"pk": self.object.pk})

    def form_valid(self, form):
        form.instance.owner = self.request.user
        messages.success(
            self.request, f'Project "{form.instance.name}" created successfully!'
        )
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, "Please correct the errors below.")
        return super().form_invalid(form)


class ProjectEditView(LoginRequiredMixin, UpdateView):
    model = Project
    form_class = ProjectCreationForm
    template_name = "projects/project_edit.html"
    context_object_name = "project"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Get all available step templates
        context["available_templates"] = StepTemplate.objects.filter(
            is_active=True
        ).order_by("default_order")

        # Get current project steps
        context["project_steps"] = (
            ProjectStep.objects.filter(project=self.object)
            .select_related("step_template")
            .prefetch_related("tasks")
            .order_by("order")
        )

        return context
    
    def get_success_url(self):
        return reverse_lazy("projects:project_edit", kwargs={"pk": self.object.pk})


class AddProjectStepView(LoginRequiredMixin, View):
    """Handle adding a step to a project via HTMX"""

    def post(self, request, project_id):
        project = get_object_or_404(Project, pk=project_id)
        step_template_id = request.POST.get("step_template_id")
        override_name = request.POST.get("override_name", "").strip()

        try:
            step_template = get_object_or_404(
                StepTemplate, id=step_template_id, is_active=True
            )

            # Determine step order
            current_max_order = (
                ProjectStep.objects.filter(project=project).aggregate(
                    models.Max("order")
                )["order__max"]
                or 0
            )

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
            task_templates = step_template.tasks.filter(is_active=True).order_by(
                "order"
            )
            for j, task_template in enumerate(task_templates, start=1):
                ProjectTask.objects.create(
                    project_step=project_step,
                    task_template=task_template,
                    title=task_template.title,
                    info_url=getattr(task_template, "info_url", ""),
                    order=j,
                )

            # Return HTML fragment for the new step card
            return render(
                request,
                "projects/partials/step_card.html",
                {"step": project_step, "project": project},
            )

        except Exception as e:
            return HttpResponse(
                f'<div class="error-message">Error: {str(e)}</div>', status=400
            )


class ProjectStepView(LoginRequiredMixin, DetailView):
    model = ProjectStep
    template_name = "projects/partials/tasks_page.html"
    context_object_name = "step"

    def get_queryset(self):
        return super().get_queryset().prefetch_related("tasks")

    def get_object(self, queryset=None):
        # Get projectid and stepid from URL kwargs
        project_id = self.kwargs.get("project_id")
        step_id = self.kwargs.get("step_id")

        # Fetch the ProjectStep object based on both project_id and step_id
        # You might need to adjust the filtering logic based on your model relationships
        queryset = self.get_queryset().filter(project__id=project_id, id=step_id)
        obj = get_object_or_404(queryset, id=step_id)
        return obj


class RemoveProjectStepView(LoginRequiredMixin, View):
    """Handle removing a step from a project via HTMX"""

    def delete(self, request, project_id, step_id):
        project = get_object_or_404(Project, pk=project_id)
        project_step = get_object_or_404(ProjectStep, id=step_id, project=project)

        try:
            project_step.delete()

            # Check if there are any steps left
            remaining_steps = ProjectStep.objects.filter(project=project).exists()

            if not remaining_steps:
                # Return empty state HTML
                return HttpResponse("""
                    <div class="empty-state" id="emptyState">
                        <p>No steps added yet. Select templates from the left to get started.</p>
                    </div>
                """)
            else:
                # Return empty response (card will be removed by HTMX)
                return HttpResponse("")

        except Exception as e:
            return HttpResponse(
                f'<div class="error-message">Error: {str(e)}</div>', status=400
            )


class ProjectDetailView(UserOwnedMixin, DetailView):
    model = Project
    template_name = "projects/project_detail.html"
    context_object_name = "project"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["steps"] = self.object.steps.prefetch_related("tasks")
        context["completion"] = self.object.get_completion_percentage()
        return context


class ProjectDeleteView(UserOwnedMixin, DeleteView):
    model = Project
    success_url = reverse_lazy("projects:project_list")

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
        project_step = get_object_or_404(
            ProjectStep, id=step_id, project__id=project_id
        )
        title = request.POST.get("title", "").strip()
        info_url = request.POST.get("info_url", "").strip()

        if not title:
            return HttpResponse(
                '<div class="error-message">Error: Task title cannot be empty.</div>',
                status=400,
            )

        try:
            # Determine task order
            current_max_order = (
                ProjectTask.objects.filter(project_step=project_step).aggregate(
                    models.Max("order")
                )["order__max"]
                or 0
            )

            # Create the project task
            project_task = ProjectTask.objects.create(
                project_step=project_step,
                title=title,
                info_url=info_url,
                order=current_max_order + 1,
            )

            # Return HTML fragment for the new task row
            return render(
                request,
                "projects/partials/task_row.html",
                {"task": project_task},
            )

        except Exception as e:
            return HttpResponse(
                f'<div class="error-message">Error: {str(e)}</div>', status=400
            )


class UpdateProjectTaskView(LoginRequiredMixin, View):
    """Handle updating a task's status via HTMX"""

    def post(self, request, project_id, step_id, task_id):
        project_task = ProjectTask.objects.get(
            id=task_id,
            project_step__id=step_id,
            project_step__project__id=project_id,
        )
        step = ProjectStep.objects.get(
            id=step_id, project__id=project_id
        )

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

        # Handle OOB step update for other parts UI update
        badge_html = render_to_string("projects/partials/step-status-badge.html", {
            "oob": True,
            "status": step.get_status(),
            "id": step.id
        })
        progress_html = render_to_string(
            "projects/partials/step-progress-bar.html",
            {
                "oob": True,
                "completion": step.get_percentage_complete(),
                "text": step.get_progress_text(),
            }
        )

        return HttpResponse(row_html + badge_html + progress_html)


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
            return HttpResponse(
                f'<div class="error-message">Error: {str(e)}</div>', status=400
            )
