from accounts.models import UserProjectPermissions
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied  # Pour un 403 explicite


class AbstractProjectAccessMixin(LoginRequiredMixin):
    """Mixin pour vérifier l'accès (read, write, admin) à un projet spécifique."""

    required_permission = None

    def dispatch(self, request, *args, **kwargs):
        project_id = kwargs.get("project_id") or kwargs.get("pk")

        if not project_id:
            # S'assurer que le paramètre project_id ou pk est dans l'URL
            raise AttributeError("Le mixin ProjectAccessMixin nécessite 'project_id' ou 'pk' dans les kwargs de l'URL.")

        # 2. Vérifier les permissions
        user_permission = UserProjectPermissions.objects.get_user_permissions(request.user, project_id)

        if not user_permission:
            raise PermissionDenied("Access denied.")

        if self.required_permission == "admin":
            has_permission = user_permission.is_admin
        elif self.required_permission == "write":
            has_permission = user_permission.can_edit or user_permission.is_admin
        elif self.required_permission == "read":
            has_permission = user_permission.can_view or user_permission.can_edit or user_permission.is_admin

        if not has_permission:
            # Lever une exception d'autorisation 403 si l'accès est refusé
            raise PermissionDenied("Access denied.")

        return super().dispatch(request, *args, **kwargs)


class ProjectReadRequiredMixin(AbstractProjectAccessMixin):
    required_permission = "read"


class ProjectEditRequiredMixin(AbstractProjectAccessMixin):
    required_permission = "write"


class ProjectAdminRequiredMixin(AbstractProjectAccessMixin):
    required_permission = "admin"


class CommonContextMixin:
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["task_id"] = self.kwargs.get("task_id")
        context["step_id"] = self.kwargs.get("step_id")
        context["project_id"] = self.kwargs.get("project_id")

        context["roles"] = self._compute_user_roles(self.request.user, context["project_id"])

        return context

    def _compute_user_roles(self, user, project_id):
        # 3. Initialiser les rôles
        roles = set()

        # 4. Vérifier l'utilisateur et le project_id
        if not user.is_authenticated or not project_id:
            return []

        # Tenter de récupérer les permissions spécifiques à ce projet pour cet utilisateur
        permissions = UserProjectPermissions.objects.get_user_permissions(user=user, project_id=project_id)

        if permissions:
            # Les permissions sont hiérarchiques ou cumulatives
            if permissions.is_admin:
                roles.add("admin")
                roles.add("edit")
                roles.add("read")

            # Si non-admin, on vérifie edit
            if permissions.can_edit:
                roles.add("edit")
                roles.add("read")

            # Si non-edit, on vérifie view
            if permissions.can_view:
                roles.add("read")

        return list(roles)
