from core.mixins import ProjectAdminRequiredMixin
from django.contrib import messages
from django.contrib.auth import get_user_model, login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.generic.base import View
from django_htmx.http import reswap
from projects.models import Project

from accounts.models import UserProjectPermissions

from .forms import BasicRegisterForm, UserEditForm

User = get_user_model()


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
    if request.method == "POST":
        form = BasicRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("projects:project_list")
        else:
            return render(request, "accounts/register.html", {"form": form})
    else:
        if request.user.is_authenticated:
            return redirect("projects:project_list")

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
        current_permissions = (
            UserProjectPermissions.objects.filter(project_id=project_id).select_related("user").order_by("user__username")
        )

        users_with_permissions = current_permissions.values_list("user_id", flat=True)
        all_users_without_permissions = User.objects.all().exclude(id__in=users_with_permissions)
        project = get_object_or_404(Project, pk=project_id)

        context = {
            "project": project,
            "project_id": project_id,
            "current_permissions": current_permissions,
            "other_users": all_users_without_permissions,
        }

        return render(request, "projects/partials/permission_table.html", context)


class UpdateUserPermissionForm(ProjectAdminRequiredMixin, View):
    """
    Met à jour les niveaux de permission d'un utilisateur sur un projet.
    """

    def post(self, request, project_id, permission_id):
        # 1. Fetch existing permission if exist
        try:
            permission = UserProjectPermissions.objects.get(pk=permission_id, project__id=project_id)
        except UserProjectPermissions.DoesNotExist:
            # If not exist, don't change something
            messages.error(request, "The permission does not exist.")
            return reswap(HttpResponse(status=200), "none")

        if permission.user == request.user:
            messages.error(request, "You cannot delete yourself")
            return reswap(HttpResponse(status=200), "none")

        # 2. Get data
        field_name = request.POST.get("field_name")
        index = request.POST.get("index", "#")

        if field_name == "can_view":
            if permission.can_view:  # If we remove the read access, the user should lose all access
                permission.can_view = False
                permission.can_edit = False
                permission.is_admin = False
            else:
                permission.can_view = True

        elif field_name == "can_edit":  # If we remove the edit access, the user should lose admin access
            if permission.can_edit:
                permission.can_edit = False
                permission.is_admin = False
            else:
                permission.can_edit = True

        elif field_name == "is_admin":
            permission.is_admin = not permission.is_admin

        # 3. Update
        permission.save()

        return render(request, "projects/partials/permission_table.html#user_row", {"index": index, "permission": permission})

    def delete(self, request, project_id, permission_id):
        # 1. Fetch existing permission if exist
        try:
            permission = UserProjectPermissions.objects.get(pk=permission_id, project__id=project_id)
        except UserProjectPermissions.DoesNotExist:
            # If not exist, don't change something
            messages.error(request, "The permission does not exist.")
            return reswap(HttpResponse(status=200), "none")

        if permission.user == request.user:
            messages.error(request, "You cannot delete yourself")
            return reswap(HttpResponse(status=200), "none")

        # 2. Delete the permission
        permission.delete()

        return HttpResponse(status=200)


class AddUserPermissionForm(ProjectAdminRequiredMixin, View):
    """
    View to handle the creation of a new UserProjectPermissions record.
    """

    def post(self, request, project_id):
        # 1. Fetch existing project if exist
        project = Project.objects.get(pk=project_id)
        if not project:
            messages.error(request, "Project not found.")
            return reswap(HttpResponse(status=200), "none")

        # 2. Fetch user
        user_id = request.POST.get("user_id")
        if not user_id:
            messages.error(request, "Please select a user.")
            return reswap(HttpResponse(status=200), "none")

        user_to_add = User.objects.get(pk=user_id)
        if not user_to_add:
            messages.error(request, "User not found.")
            return reswap(HttpResponse(status=200), "none")

        # 3. Create the permission with no access, user will adjust afterward
        qs = UserProjectPermissions.objects.filter(project=project)
        index = qs.count() + 1

        if qs.filter(user=user_to_add).exists():
            messages.error(request, f"Permission for {user_to_add.username} already exists.")
            return reswap(HttpResponse(status=200), "none")

        permission = UserProjectPermissions.objects.create(
            project=project,
            user=user_to_add,
            can_view=False,
            can_edit=False,
            is_admin=False,
        )

        return render(request, "projects/partials/permission_table.html#user_row", {"index": index, "permission": permission})
