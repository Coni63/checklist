from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    pass


class UserProjectPermissionsManager(models.Manager):
    def get_user_permissions(self, user, project_id: str | list[str]):
        try:
            if isinstance(project_id, list):
                return self.filter(user=user, project_id__in=project_id)
            else:
                return self.get(user=user, project_id=project_id)
        except UserProjectPermissions.DoesNotExist:
            return None

    def get_projects_for_user(self, user, read=True, write=False, admin=False) -> list[int]:
        """
        Return all project IDs where the user has read, edit or admin roles.
        In DB, admin has read & edit, edit has read
        """
        qs = self.filter(user=user)

        if admin:
            qs = qs.filter(is_admin=True)
        elif write:
            qs = qs.filter(can_edit=True)
        elif read:
            qs = qs.filter(can_view=True)
        else:
            # If we don't want any role, don't return anything
            return []

        return qs.values_list("project_id", flat=True)


class UserProjectPermissions(models.Model):
    user = models.ForeignKey("accounts.User", on_delete=models.CASCADE, related_name="permissions")
    project = models.ForeignKey("projects.Project", on_delete=models.CASCADE, related_name="permissions")
    can_edit = models.BooleanField(default=False)
    can_view = models.BooleanField(default=True)
    is_admin = models.BooleanField(default=False)

    objects = UserProjectPermissionsManager()

    class Meta:
        unique_together = ("user", "project")

    def __str__(self):
        if self.is_admin:
            return f"{self.user.email} / {self.project.name} : RWA"
        elif self.can_edit:
            return f"{self.user.email} / {self.project.name} : RW-"
        elif self.can_view:
            return f"{self.user.email} / {self.project.name} : R--"
        else:
            return f"{self.user.email} / {self.project.name} : ---"
