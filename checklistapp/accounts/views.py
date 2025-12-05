from core.mixins import ProjectAdminRequiredMixin
from django.contrib import messages
from django.contrib.auth import get_user_model, login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.views.generic.base import View
from django_htmx.http import reswap

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
            # Connexion immédiate de l'utilisateur après l'inscription (optionnel)
            login(request, user)
            return redirect("projects:project_list")  # Redirigez vers une page d'accueil après l'inscription
        else:
            return render(request, "accounts/register.html", {"form": form})
    else:
        if request.user.is_authenticated:
            return redirect("projects:project_list")

        form = BasicRegisterForm()
        return render(request, "accounts/register.html", {"form": form})


@login_required  # Ensures only logged-in users can access this view
def my_profile(request):
    # The current logged-in user is request.user

    if request.method == "POST":
        # 1. Initialize the form with POST data AND the existing user instance
        form = UserEditForm(request.POST, instance=request.user)

        if form.is_valid():
            # 2. Save updates to the existing user
            form.save()
            # It's best practice to redirect after a successful POST
            return redirect("accounts:profile")  # Assuming you have a URL name 'my_profile'

        # If the form is NOT valid, fall through to render the template with errors

    else:  # This handles the initial GET request
        # 3. Initialize the form with the existing user instance so fields are pre-filled
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
        current_permissions = UserProjectPermissions.objects.filter(project_id=project_id).select_related("user")

        users_with_permissions = current_permissions.values_list("user_id", flat=True)
        all_users_without_permissions = User.objects.all().exclude(id__in=users_with_permissions)

        context = {
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
        # 2. Récupérez la Permission spécifique
        try:
            permission = UserProjectPermissions.objects.get(pk=permission_id, project__id=project_id)
        except UserProjectPermissions.DoesNotExist:
            # Réponse 404 si la permission n'existe pas dans ce projet
            messages.error(request, "The permission does not exist.")
            return reswap(HttpResponse(status=200), "none")

        if permission.user == request.user:
            messages.error(request, "You cannot delete yourself")
            return reswap(HttpResponse(status=200), "none")

        # 3. Récupérez les données du formulaire
        # Les checkboxes non cochées n'apparaissent pas dans request.POST,
        # donc on vérifie leur présence.

        field_name = request.POST.get("field_name")
        index = request.POST.get("index", "#")

        if field_name == "can_view":
            if permission.can_view:
                permission.can_view = False
                permission.can_edit = False
                permission.is_admin = False
            else:
                permission.can_view = True

        elif field_name == "can_edit":
            if permission.can_edit:
                permission.can_edit = False
                permission.is_admin = False
            else:
                permission.can_edit = True

        elif field_name == "is_admin":
            permission.is_admin = not permission.is_admin

        # 3. Update la permission
        # permission.save() # TODO: uncomment

        return render(request, "projects/partials/permission_table.html#user_row", {"index": index, "permission": permission})

    def delete(self, request, project_id, permission_id):
        # 2. Récupérez la Permission spécifique
        try:
            permission = UserProjectPermissions.objects.get(pk=permission_id, project__id=project_id)
        except UserProjectPermissions.DoesNotExist:
            # Réponse 404 si la permission n'existe pas dans ce projet
            messages.error(request, "The permission does not exist.")
            return reswap(HttpResponse(status=200), "none")

        if permission.user == request.user:
            messages.error(request, "You cannot delete yourself")
            return reswap(HttpResponse(status=200), "none")

        # 3. Supprimez la Permission
        # permission.delete() # TODO: uncomment

        return HttpResponse(status=200)
