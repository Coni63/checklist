
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
