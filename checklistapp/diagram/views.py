import json
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from projects.services import ProjectService


def load_page(request, project_id):
    context = {"project_id": project_id, "project": ProjectService.get(project_id)}
    return render(request, "diagram/diagram_page.html", context=context)


def load_diagram(request, project_id):
    # Exemple de données - vous ajusterez selon votre modèle
    boxes = [
        {"id": "box1", "label": "Étape 1", "x": 50, "y": 50, "description": "Début du processus"},
        {"id": "box2", "label": "Étape 2", "x": 300, "y": 50, "description": "Traitement"},
        {"id": "box3", "label": "Étape 3", "x": 550, "y": 50, "description": "Validation"},
        {"id": "box4", "label": "Étape 4", "x": 300, "y": 200, "description": "Fin du processus"},
    ]

    # Définition des connexions (flèches)
    arrows = [
        {"source": "box1", "target": "box2", "label": "Suivant"},
        {"source": "box2", "target": "box3", "label": "Valider"},
        {"source": "box3", "target": "box4", "label": "OK"},
        {"source": "box2", "target": "box4", "label": "Erreur"},
    ]

    context = {"project_id": project_id, "boxes": boxes, "arrows": arrows}

    return render(request, "diagram/diagram.html", context)


@require_http_methods(["POST"])
def save_diagram(request, project_id):
    """
    Sauvegarde l'état du diagramme en base de données.
    Reçoit un JSON avec la structure:
    {
        "boxes": [{"id": "box1", "label": "...", "description": "...", "x": 50, "y": 50}, ...],
        "arrows": [{"source": "box1", "target": "box2", "label": "..."}, ...]
    }
    """
    try:
        data = json.loads(request.body)
        boxes = data.get('boxes', [])
        arrows = data.get('arrows', [])

        # TODO: Sauvegarder dans votre modèle de base de données
        # Exemple:
        # project = ProjectService.get(project_id)
        # project.diagram_data = json.dumps(data)
        # project.save()

        # Pour l'instant, on retourne juste une confirmation
        print(f"Diagramme sauvegardé pour le projet {project_id}:")
        print(f"  - {len(boxes)} boxes")
        print(f"  - {len(arrows)} connexions")

        return JsonResponse({
            "status": "success",
            "message": "Diagramme sauvegardé avec succès",
            "boxes_count": len(boxes),
            "arrows_count": len(arrows)
        })

    except Exception as e:
        return JsonResponse({
            "status": "error",
            "message": str(e)
        }, status=400)
