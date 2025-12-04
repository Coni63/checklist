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
        "<int:project_id>/steps/add_step/",
        views.AddProjectStepView.as_view(),
        name="add_step",
    ),
    path(
        "<int:project_id>/steps/<int:step_id>/",
        views.ProjectDetailView.as_view(),
        name="step_tasks",
    ),
    path(
        "<int:project_id>/steps/<int:step_id>/delete/",
        views.RemoveProjectStepView.as_view(),
        name="remove_step",
    ),
    # Project Task URLs
    path(
        "<int:project_id>/steps/<int:step_id>/tasks/add_task/",
        views.AddProjectTaskView.as_view(),
        name="add_task",
    ),
    path(
        "<int:project_id>/steps/<int:step_id>/tasks/<int:task_id>/set_status/",
        views.UpdateProjectTaskView.as_view(),
        name="set_status",
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
    path(
        "tasks/<int:task_id>/comments/",
        views.TaskCommentListView.as_view(),
        name="task_comment_list",
    ),
    path(
        "tasks/<int:task_id>/comments/create/",
        views.TaskCommentCreateView.as_view(),
        name="task_comment_create",
    ),
    path(
        "comments/<int:comment_id>/edit/",
        views.TaskCommentUpdateView.as_view(),
        name="task_comment_edit",
    ),
    path(
        "comments/<int:comment_id>/delete/",
        views.TaskCommentDeleteView.as_view(),
        name="task_comment_delete",
    ),
    # Helpers
    path(
        "<int:project_id>/steps/<int:step_id>/tasks-btn/",
        views.toggle_task_form,
        name="toggle_task_form",
    ),
]
