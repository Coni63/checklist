import logging

from core.exceptions import InvalidParameterError, RecordNotFoundError
from core.mixins import ProjectAdminRequiredMixin
from django.contrib import messages
from django.contrib.auth import get_user_model, login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.views.generic.base import View
from django_htmx.http import reswap
from projects.services import ProjectService

from .forms import BasicRegisterForm, UserEditForm
from .services import AccountService

User = get_user_model()
logger = logging.getLogger(__name__)


def login_view(request):
    if request.user.is_authenticated:
        return redirect("projects:project_list")

    if request.method == "GET":
        form = AuthenticationForm()
        return render(request, "accounts/login.html", {"form": form})
    else:
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect("projects:project_list")
        else:
            return render(request, "accounts/login.html", {"form": form})


def register_view(request):
    if request.user.is_authenticated:
        return redirect("projects:project_list")

    if request.method == "POST":
        form = BasicRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("projects:project_list")
        else:
            return render(request, "accounts/register.html", {"form": form})
    else:
        form = BasicRegisterForm()
        return render(request, "accounts/register.html", {"form": form})


@login_required  # Ensures only logged-in users can access this view
def my_profile(request):
    if request.method == "POST":
        form = UserEditForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Update saved !")
            return redirect("accounts:profile")
        else:
            messages.warning(request, "Invalid form")
            # If the form is NOT valid, fall through to render the template with errors

    else:  # This handles the initial GET request
        form = UserEditForm(instance=request.user)

    # 4. Render the correct template with the current user and the form
    return render(request, "accounts/profile.html", {"user": request.user, "form": form})


class ListUserForm(ProjectAdminRequiredMixin, View):
    """
    View to list all users in the system.
    Only accessible to project admins.
    """

    template_name = "accounts/user_list.html"

    def get(self, request, project_id, *args, **kwargs):
        current_permissions = AccountService.get_all_users_having_permissions(project_id)

        users_with_permissions = current_permissions.values_list("user_id", flat=True)
        all_users_without_permissions = AccountService.get_users().exclude(id__in=users_with_permissions)
        project = ProjectService.get(project_id)

        context = {
            "project": project,
            "project_id": project_id,
            "current_permissions": current_permissions,
            "other_users": all_users_without_permissions,
        }

        return render(request, "accounts/partials/permission_table.html", context)


class UpdateUserPermissionForm(ProjectAdminRequiredMixin, View):
    """
    Met à jour les niveaux de permission d'un utilisateur sur un projet.
    """

    def post(self, request, project_id, permission_id):
        # 1. Fetch existing permission if exist
        try:
            field_name = request.POST.get("field_name")
            index = request.POST.get("index", "#")

            permission = AccountService.update_permission(project_id, permission_id, field_name, request.user)

            return render(
                request, "accounts/partials/permission_table.html#user_row", {"index": index, "permission": permission}
            )

        except Exception as e:
            logger.error(e)
            if hasattr(e, "custom"):
                messages.error(request, str(e))
            else:
                messages.error(request, "Something went wrong when updating user permissions.")
            return reswap(HttpResponse(status=200), "none")

    def delete(self, request, project_id, permission_id):
        try:
            permission = AccountService.get_permission(project_id, permission_id)

            if permission.user == request.user:
                raise PermissionError("You cannot delete yourself")

            permission.delete()

            return HttpResponse(status=200)
        except Exception as e:
            logger.error(e)
            if hasattr(e, "custom"):
                messages.error(request, str(e))
            else:
                messages.error(request, "Something went wrong when deleting user permissions.")
            return reswap(HttpResponse(status=200), "none")


class AddUserPermissionForm(ProjectAdminRequiredMixin, View):
    """
    View to handle the creation of a new UserProjectPermissions record.
    """

    def post(self, request, project_id):
        try:
            # 1. Fetch existing project if exist
            project = ProjectService.get(project_id)

            user_id = request.POST.get("user_id")
            if not user_id:
                raise InvalidParameterError("Please select a user.")

            user_to_add = AccountService.get_user(user_id)

            # 3. Create the permission with no access, user will adjust afterward
            permissions = AccountService.get_all_permissions_for_project(project)
            index = permissions.count() + 1

            if permissions.filter(user=user_to_add).exists():
                raise RecordNotFoundError(f"Permission for {user_to_add.username} already exists.")

            permission = AccountService.create_permission(project=project, user=user_to_add)

            return render(
                request, "accounts/partials/permission_table.html#user_row", {"index": index, "permission": permission}
            )

        except Exception as e:
            logger.error(e)
            if hasattr(e, "custom"):
                messages.error(request, str(e))
            else:
                messages.error(request, "Something went wrong when deleting user permissions.")
            return reswap(HttpResponse(status=200), "none")
