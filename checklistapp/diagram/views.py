from django.http import HttpResponse
from django.shortcuts import render

from projects.services import ProjectService


# Create your views here.
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
