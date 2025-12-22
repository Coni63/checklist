from projects.models import Project
from core.exceptions import RecordNotFoundError
from django.db import transaction
from .models import UserProjectPermissions, User


class AccountService:
    @staticmethod
    def get_all_users_having_permissions(project_id):
        return UserProjectPermissions.objects.filter(project_id=project_id).select_related("user").order_by("user__username")

    @staticmethod
    def get_users(user_ids: list[int] | None = None):
        if user_ids is None:
            return User.objects.all()
        return User.objects.filter(id__in=user_ids)

    @staticmethod
    def get_user(user_id: int) -> User:
        try:
            return User.objects.get(id=user_id)
        except User.DoesNotExist:
            raise RecordNotFoundError("User not found.")

    @staticmethod
    def get_permission(project_id, permission_id):
        try:
            return UserProjectPermissions.objects.get(pk=permission_id, project__id=project_id)
        except UserProjectPermissions.DoesNotExist:
            raise RecordNotFoundError("Permission not found.")

    @staticmethod
    def get_all_permissions_for_project(project: list[int] | Project):
        return UserProjectPermissions.objects.filter(project=project)

    @staticmethod
    def get_all_permissions_for_user(user, read=True, write=False, admin=False):
        qs = UserProjectPermissions.objects.filter(user=user)

        if admin:
            qs = qs.filter(is_admin=True)
        elif write:
            qs = qs.filter(can_edit=True)
        elif read:
            qs = qs.filter(can_view=True)
        else:
            # If we don't want any role, don't return anything
            qs = UserProjectPermissions.objects.none()

        return qs

    @staticmethod
    @transaction.atomic
    def create_permission(
        project, user, can_view: bool = False, can_edit: bool = False, is_admin: bool = False
    ) -> UserProjectPermissions:
        return UserProjectPermissions.objects.create(
            project=project,
            user=user,
            can_view=can_view,
            can_edit=can_edit,
            is_admin=is_admin,
        )

    @staticmethod
    @transaction.atomic
    def update_permission(project_id, permission_id, role: str, requestor: User) -> UserProjectPermissions:
        permission = AccountService.get_permission(project_id, permission_id)

        if permission.user == requestor:
            raise PermissionError("You cannot edit yourself")

        if role == "can_view":
            if permission.can_view:  # If we remove the read access, the user should lose all access
                permission.can_view = False
                permission.can_edit = False
                permission.is_admin = False
            else:
                permission.can_view = True
                permission.can_edit = False
                permission.is_admin = False

        elif role == "can_edit":  # If we remove the edit access, the user should lose admin access
            if permission.can_edit:
                permission.can_edit = False
                permission.is_admin = False
            else:
                permission.can_view = True
                permission.can_edit = True
                permission.is_admin = False

        elif role == "is_admin":
            if permission.is_admin:
                permission.is_admin = False
            else:
                permission.can_view = True
                permission.can_edit = True
                permission.is_admin = True

        permission.save()
        return permission
