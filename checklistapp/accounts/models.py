from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    pass




class UserProjectPermissions(models.Model):
    user = models.ForeignKey("accounts.User", on_delete=models.CASCADE, related_name="permissions")
    project = models.ForeignKey("projects.Project", on_delete=models.CASCADE, related_name="permissions")
    can_edit = models.BooleanField(default=False)
    can_view = models.BooleanField(default=True)
    is_admin = models.BooleanField(default=False)

    class Meta:
        unique_together = ("user", "project")

    def __str__(self):
        if self.is_admin:
            return f"{self.user.email} is admin of {self.project.name}"
        elif self.can_edit:
            return f"{self.user.email} can edit {self.project.name}"
        elif self.can_view:
            return f"{self.user.email} can view {self.project.name}"
        else:
            return f"{self.user.email} has no access to {self.project.name}"
