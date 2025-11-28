from django.urls import path

from . import views

app_name = "projects"

urlpatterns = [
    path("", views.ProjectListView.as_view(), name="project_list"),
    path("create/", views.ProjectCreateView.as_view(), name="project_create"),
    path("<int:pk>/setup/", views.ProjectSetupView.as_view(), name="project_setup"),
    path("<int:pk>/", views.ProjectDetailView.as_view(), name="project_detail"),
    path("<int:pk>/delete", views.ProjectDeleteView.as_view(), name="project_delete"),
    path(
        "project/<int:pk>/add-step/",
        views.AddProjectStepView.as_view(),
        name="add_step",
    ),
    path(
        "steps/<int:pk>",
        views.ProjectStepView.as_view(),
        name="step_tasks",
    ),
    path(
        "project/<int:pk>/remove-step/<int:step_id>/",
        views.RemoveProjectStepView.as_view(),
        name="remove_step",
    ),
]
