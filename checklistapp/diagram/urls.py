from django.urls import path

from . import views

app_name = "diagram"

urlpatterns = [
    path(
        "",
        views.load_page,
        name="diagram_page",
    ),
    path(
        "diagram/",
        views.load_diagram,
        name="diagram_content",
    ),
]
