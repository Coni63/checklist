from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404
from projects.models import Project


class UserOwnedMixin(LoginRequiredMixin):
    """Mixin to filter querysets by owner"""

    def get_queryset(self):
        return super().get_queryset().filter(owner=self.request.user)


class ProjectAccessMixin(LoginRequiredMixin):
    """Mixin to check project access"""

    def dispatch(self, request, *args, **kwargs):
        project_id = kwargs.get("project_id") or kwargs.get("pk")
        self.project = get_object_or_404(Project, id=project_id, owner=request.user)
        return super().dispatch(request, *args, **kwargs)
