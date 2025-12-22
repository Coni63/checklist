from accounts.services import AccountService
from core.exceptions import RecordNotFoundError

from .models import Project


class ProjectService:
    @staticmethod
    def get(project_id, prefetch_related: list[str] | None = None):
        """Récupère un template d'inventaire actif."""
        try:
            qs = Project.objects.filter(id=project_id)

            if prefetch_related:
                qs = qs.prefetch_related(*prefetch_related)

            return qs.first()
        except Project.DoesNotExist:
            raise RecordNotFoundError("project not found.")

    @staticmethod
    def get_projects_for_user(user, status: str = "all"):
        project_ids = AccountService.get_all_permissions_for_user(user, True, False, False).values_list("project_id", flat=True)

        qs = Project.objects.filter(id__in=project_ids)

        if status != "all":
            qs = qs.filter(status=status)

        return qs
