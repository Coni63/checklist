from accounts.models import UserProjectPermissions
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ImproperlyConfigured, PermissionDenied


class AbstractProjectAccessMixin(LoginRequiredMixin):
    """Mixin pour vérifier l'accès (read, write, admin) à un projet spécifique."""

    required_permission = None

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return super().dispatch(request, *args, **kwargs)  # Redirige vers login

        project_id = kwargs.get("project_id") or kwargs.get("pk")

        if not project_id:
            raise AttributeError("Le mixin ProjectAccessMixin requires a 'project_id' or 'pk' in URL parameters")

        # 1. Fetch permission
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
            raise PermissionDenied("Access denied.")

        return super().dispatch(request, *args, **kwargs)


class ProjectReadRequiredMixin(AbstractProjectAccessMixin):
    required_permission = "read"


class ProjectEditRequiredMixin(AbstractProjectAccessMixin):
    required_permission = "write"


class ProjectAdminRequiredMixin(AbstractProjectAccessMixin):
    required_permission = "admin"


class OwnerOrAdminMixin(LoginRequiredMixin):
    """
    Mixin to check if the user is the author or admin
    """

    object_model = None  # Set the class to be checked
    owner_field = "owner"  # Set the field in question of the user
    object_key_name = "pk"  # Set the nema of the primary key of the object

    def dispatch(self, request, *args, **kwargs):
        # 1. First checks
        if self.object_model is None:
            raise ImproperlyConfigured("Le mixin OwnerOrAdminMixin nécessite que 'object_model' soit défini.")

        object_id = kwargs.get(self.object_key_name)
        project_id = kwargs.get("project_id")
        has_permission = False

        if not object_id or not project_id:
            raise ImproperlyConfigured("Le mixin nécessite 'pk' (ID de l'objet) ET 'project_id' dans les kwargs de l'URL.")

        # Check first if it's the author
        try:
            # 2. Fetch the objects
            current_object = self.object_model.objects.get(pk=object_id)
        except self.object_model.DoesNotExist:
            raise PermissionDenied("Access denied.")

        # 3. Check the author
        object_owner = getattr(current_object, self.owner_field)
        has_permission = request.user == object_owner

        # 4. Check user permissions if it's not the author
        if not has_permission:
            user_permission = UserProjectPermissions.objects.get_user_permissions(request.user, project_id)

            if user_permission:
                has_permission = user_permission.is_admin

        if not has_permission:
            raise PermissionDenied("Access denied.")

        request.current_object = current_object

        return super().dispatch(request, *args, **kwargs)


class CommonContextMixin:
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["task_id"] = self.kwargs.get("task_id")
        context["step_id"] = self.kwargs.get("step_id")
        context["project_id"] = self.kwargs.get("project_id")
        context["comment_id"] = self.kwargs.get("comment_id")
        context["inventory_id"] = self.kwargs.get("inventory_id")
        context["field_id"] = self.kwargs.get("field_id")

        context["roles"] = self._compute_user_roles(self.request.user, context["project_id"])

        return context

    def _compute_user_roles(self, user, project_id):
        """
        Return a list of roles like ["read", "edit"]
        """
        if not user.is_authenticated or not project_id:
            return []

        permissions = UserProjectPermissions.objects.get_user_permissions(user=user, project_id=project_id)

        if permissions:
            if permissions.is_admin:
                return ["admin", "edit", "read"]
            elif permissions.can_edit:
                return ["edit", "read"]
            elif permissions.can_view:
                return ["read"]

        return []
