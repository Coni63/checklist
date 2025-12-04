from django.urls import path

from . import views

app_name = "projects"

urlpatterns = [
    # Project URLs
    path("", views.ProjectListView.as_view(), name="project_list"),
    path("create/", views.ProjectCreateView.as_view(), name="project_create"),
    path("<int:project_id>/edit/", views.ProjectEditView.as_view(), name="project_edit"),
    path("<int:project_id>/", views.ProjectDetailView.as_view(), name="project_detail"),
    path(
        "<int:project_id>/delete/",
        views.ProjectDeleteView.as_view(),
        name="project_delete",
    ),
    # Project Step URLs
    path(
        "<int:project_id>/steps/step_add/",
        views.AddProjectStepView.as_view(),
        name="step_add",
    ),
    path(
        "<int:project_id>/steps/<int:step_id>/",
        views.ProjectDetailView.as_view(),
        name="step_detail",
    ),
    path(
        "<int:project_id>/steps/<int:step_id>/delete/",
        views.RemoveProjectStepView.as_view(),
        name="step_delete",
    ),
    path(
        "<int:project_id>/reorder-steps/",
        views.ReorderProjectStepsView.as_view(),
        name="step_reorder",
    ),
    # Project Task URLs
    path(
        "<int:project_id>/steps/<int:step_id>/tasks/task_create/",
        views.AddProjectTaskView.as_view(),
        name="task_create",
    ),
    path(
        "<int:project_id>/steps/<int:step_id>/tasks/<int:task_id>/task_status_update/",
        views.UpdateProjectTaskView.as_view(),
        name="task_status_update",
    ),
    path(
        "<int:project_id>/steps/<int:step_id>/tasks/<int:task_id>/delete/",
        views.DeleteProjectTaskView.as_view(),
        name="task_delete",
    ),
    path(
        "<int:project_id>/steps/<int:step_id>/tasks/<int:task_id>/comments/",
        views.TaskCommentListView.as_view(),
        name="comment_list",
    ),
    path(
        "<int:project_id>/steps/<int:step_id>/tasks/<int:task_id>/comments/create/",
        views.TaskCommentCreateView.as_view(),
        name="comment_create",
    ),
    path(
        "<int:project_id>/steps/<int:step_id>/tasks/<int:task_id>/comments/<int:comment_id>/edit/",
        views.TaskCommentUpdateView.as_view(),
        name="comment_edit",
    ),
    path(
        "<int:project_id>/steps/<int:step_id>/tasks/<int:task_id>/comments/<int:comment_id>/delete/",
        views.TaskCommentDeleteView.as_view(),
        name="comment_delete",
    ),
    # Helpers
    path(
        "<int:project_id>/steps/<int:step_id>/tasks-btn/",
        views.toggle_task_form,
        name="toggle_task_form",
    ),
]
