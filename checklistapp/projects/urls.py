from django.urls import path

from . import views

app_name = "projects"

urlpatterns = [
    path("", views.ProjectListView.as_view(), name="project_list"),
    path("create/", views.ProjectCreateView.as_view(), name="project_create"),
    path(
        "<int:pk>/setup-v2/", views.ProjectSetupViewV2.as_view(), name="project_setup"
    ),
    path("<int:pk>/", views.ProjectDetailView.as_view(), name="project_detail"),
    path(
        "project/<int:pk>/add-step/",
        views.AddProjectStepView.as_view(),
        name="add_step",
    ),
    path(
        "project/<int:pk>/remove-step/<int:step_id>/",
        views.RemoveProjectStepView.as_view(),
        name="remove_step",
    ),
]
