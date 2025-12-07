from accounts.models import UserProjectPermissions
from checklist.models import ProjectStep
from core.mixins import CommonContextMixin, ProjectAdminRequiredMixin, ProjectReadRequiredMixin
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView
from templates_management.models import StepTemplate

from .forms import ProjectCreationForm
from .models import Project


class ProjectListView(LoginRequiredMixin, ListView):
    """
    View to list all projects for the logged-in user,
    with optional filtering by status.
    """

    model = Project
    template_name = "projects/project_list.html"
    context_object_name = "projects"

    def get_queryset(self):
        status = self.request.GET.get("status", "active")

        qs = (
            Project.objects.get_queryset()
            .for_user(user=self.request.user, read=True, write=False, admin=False)
            .with_status(status)
        )

        if status and status != "all":
            qs = qs.filter(status=status)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["status"] = self.request.GET.get("status", "active")  # Valeur par défaut si non précisé
        context["roles"] = self._compute_user_roles(self.request.user)
        return context

    def _compute_user_roles(self, user):
        """
        Return a dict of list of roles per projects  {
            1: ["read", "edit"],
            2: ["read"]
        }
        """
        project_roles = {}

        if not user.is_authenticated:
            return project_roles

        project_ids = [str(project.id) for project in self.object_list]

        permissions = UserProjectPermissions.objects.get_user_permissions(user=user, project_id=project_ids)

        for permission in permissions:
            # Priority : admin > edit > read
            roles = []
            if permission.is_admin:
                roles = ["admin", "edit", "read"]
            elif permission.can_edit:
                roles = ["edit", "read"]
            elif permission.can_view:
                roles = ["read"]

            project_roles[permission.project_id] = roles

        return project_roles


class ProjectCreateView(LoginRequiredMixin, CreateView):
    """
    View to create a new project. Returns a page and a form.
    On success, redirects to the project edit page.
    """

    model = Project
    form_class = ProjectCreationForm
    template_name = "projects/project_create.html"

    def get_success_url(self):
        return reverse_lazy("projects:project_edit", kwargs={"project_id": self.object.pk})

    def form_valid(self, form):
        # 1. Create the project instance
        response = super().form_valid(form)

        # 2. Create UserProjectPermissions for the creator
        UserProjectPermissions.objects.create(
            user=self.request.user,
            project=self.object,
            is_admin=True,
            can_edit=True,
            can_view=True,
        )

        # 3. Response with success message
        messages.success(self.request, f'Project "{self.object.name}" created successfully!')
        return response

    def form_invalid(self, form):
        messages.error(self.request, "Please correct the errors below.")
        return super().form_invalid(form)


class ProjectEditView(ProjectAdminRequiredMixin, UpdateView):
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


class ProjectDetailView(ProjectReadRequiredMixin, CommonContextMixin, DetailView):
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

        # Si un step_id est dans l'URL, on charge ce step
        step_id = context.get("step_id")
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


class ProjectDeleteView(ProjectAdminRequiredMixin, DeleteView):
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
