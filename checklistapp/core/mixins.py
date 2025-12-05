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
