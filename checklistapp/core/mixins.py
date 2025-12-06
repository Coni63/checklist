from accounts.models import UserProjectPermissions
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied, ImproperlyConfigured

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


class OwnerOrAdminMixin(LoginRequiredMixin):
    """
    Mixin pour vérifier si l'utilisateur est :
    1. Administrateur du projet OU
    2. L'auteur (owner) de l'objet spécifique.
    """

    # 🚨 DÉFINIR CE CHAMP dans la vue qui utilise le mixin, ex: object_model = Item
    object_model = None 
    # Le nom du champ sur l'objet qui contient l'utilisateur (l'auteur/owner), ex: 'owner' ou 'created_by'
    owner_field = 'owner'
    object_key_name = "pk"

    def dispatch(self, request, *args, **kwargs):
        # 1. Vérifications initiales (projet_id et modèle)
        if self.object_model is None:
            raise ImproperlyConfigured(
                "Le mixin OwnerOrAdminMixin nécessite que 'object_model' soit défini."
            )

        object_id = kwargs.get(self.object_key_name)
        project_id = kwargs.get("project_id")
        
        if not object_id or not project_id:
            raise ImproperlyConfigured(
                "Le mixin nécessite 'pk' (ID de l'objet) ET 'project_id' dans les kwargs de l'URL."
            )

        try:
            # 2. Récupérer l'objet et son auteur
            current_object = self.object_model.objects.get(pk=object_id)
            object_owner = getattr(current_object, self.owner_field)
            
            # Vérifier si l'utilisateur est l'auteur de l'objet
            is_owner = (request.user == object_owner)
            
        except self.object_model.DoesNotExist:
            raise PermissionDenied("Access denied.") # Ou Http404, selon votre préférence

        # 3. Vérifier les permissions du projet
        user_permission = UserProjectPermissions.objects.get_user_permissions(request.user, project_id)

        if not user_permission:
             # Si l'utilisateur n'a aucune permission sur le projet, il faut au moins qu'il soit l'auteur.
             has_permission = is_owner
        else:
             # Autorisation si l'utilisateur est admin DU PROJET OU l'auteur de l'objet
             is_project_admin = user_permission.is_admin 
             has_permission = is_project_admin or is_owner


        # 4. Autorisation finale
        if not has_permission:
            # Lever une exception d'autorisation 403 si l'accès est refusé
            raise PermissionDenied("Access denied.")

        # L'objet est accessible dans la vue si nécessaire
        request.current_object = current_object 

        return super().dispatch(request, *args, **kwargs)


class CommonContextMixin:
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["task_id"] = self.kwargs.get("task_id")
        context["step_id"] = self.kwargs.get("step_id")
        context["project_id"] = self.kwargs.get("project_id")
        context["comment_id"] = self.kwargs.get("comment_id")

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
