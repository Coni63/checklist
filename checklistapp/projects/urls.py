from django.urls import path

from . import views

app_name = "projects"

urlpatterns = [
    # Project URLs
    path("", views.ProjectListView.as_view(), name="project_list"),
    path("create/", views.ProjectCreateView.as_view(), name="project_create"),
    path("<int:pk>/edit/", views.ProjectEditView.as_view(), name="project_edit"),
    path("<int:pk>/", views.ProjectDetailView.as_view(), name="project_detail"),
    path("<int:pk>/delete/", views.ProjectDeleteView.as_view(), name="project_delete"),
    # Project Step URLs
    path(
        "project/<int:project_id>/steps/create/",
        views.AddProjectStepView.as_view(),
        name="add_step",
    ),
    path(
        "project/<int:project_id>/steps/<int:step_id>/",
        views.ProjectStepView.as_view(),
        name="step_tasks",
    ),
    path(
        "project/<int:project_id>/steps/<int:step_id>/delete/",
        views.RemoveProjectStepView.as_view(),
        name="remove_step",
    ),
    # Project Task URLs
    path(
        "project/<int:project_id>/steps/<int:step_id>/tasks/create/",
        views.AddProjectTaskView.as_view(),
        name="add_task",
    ),
    path(
        "project/<int:project_id>/steps/<int:step_id>/tasks/<int:task_id>/edit/",
        views.UpdateProjectTaskView.as_view(),
        name="update_task",
    ),
    path(
        "project/<int:project_id>/steps/<int:step_id>/tasks/<int:task_id>/delete/",
        views.DeleteProjectTaskView.as_view(),
        name="delete_task",
    ),
]
