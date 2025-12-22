import logging

from accounts.models import UserProjectPermissions
from checklist.models import ProjectStep
from accounts.services import AccountService
from inventory.services import InventoryService
from projects.services import ProjectService
from core.mixins import ProjectAdminRequiredMixin
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, UpdateView
from inventory.models import ProjectInventory
from templates_management.models import InventoryTemplate, StepTemplate

from .forms import ProjectCreationForm
from .models import Project

logger = logging.getLogger(__name__)


class ProjectListView(LoginRequiredMixin, ListView):
    """
    View to list all projects for the logged-in user,
    with optional filtering by status.
    """

    model = Project
    template_name = "projects/project_list.html"
    context_object_name = "projects"

    def get_queryset(self):
        status = self.request.GET.get("status", "active")  # context is computed afterward so we duplicate

        return ProjectService.get_projects_for_user(self.request.user, status)

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
        permissions = AccountService.get_all_permissions_for_user(user, True, False, False)

        project_roles = {}
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
        AccountService.create_permission(self.object, self.request.user, True, True, True)

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

        # TODO: refactor after checklistService

        # Get all available step templates
        context["available_templates"] = StepTemplate.objects.filter(is_active=True).order_by("default_order")
        context["inventory_templates"] = InventoryService.get_template()

        # Get current project steps
        context["project_steps"] = (
            ProjectStep.objects.filter(project=self.object)
            .select_related("step_template")
            .prefetch_related("tasks")
            .order_by("order")
        )
        context["project_inventory"] = InventoryService.get_inventory_for_project(self.object)

        return context

    def get_success_url(self):
        messages.success(self.request, f'Project "{self.object.name}" updated successfully!')
        return reverse_lazy("projects:project_edit", kwargs={"project_id": self.object.pk})


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

        except Exception as e:
            logger.error(e)
            messages.error(request, "Something went wrong deleting the project.")

        return redirect(self.success_url)
