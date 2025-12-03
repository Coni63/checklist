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
        "<int:project_id>/steps/create/",
        views.AddProjectStepView.as_view(),
        name="add_step",
    ),
    path(
        "<int:project_id>/steps/<int:step_id>/",
        views.ProjectStepView.as_view(),
        name="step_tasks",
    ),
    path(
        "<int:project_id>/steps/<int:step_id>/delete/",
        views.RemoveProjectStepView.as_view(),
        name="remove_step",
    ),
    # Project Task URLs
    path(
        "<int:project_id>/steps/<int:step_id>/tasks/create/",
        views.AddProjectTaskView.as_view(),
        name="add_task",
    ),
    path(
        "<int:project_id>/steps/<int:step_id>/tasks-form/",
        views.NewTaskFormView.as_view(),
        name="new_task_form",
    ),
    path(
        "<int:project_id>/steps/<int:step_id>/tasks/<int:task_id>/edit/",
        views.UpdateProjectTaskView.as_view(),
        name="update_task",
    ),
    path(
        "<int:project_id>/steps/<int:step_id>/tasks/<int:task_id>/delete/",
        views.DeleteProjectTaskView.as_view(),
        name="delete_task",
    ),
    path(
        "<int:project_id>/reorder-steps/",
        views.ReorderProjectStepsView.as_view(),
        name="reorder_steps",
    ),
    path("<int:project_id>/steps/<int:step_id>/tasks-btn/", views.new_task_button, name="new_task_button")
]
