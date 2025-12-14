from django.urls import path

from . import views

app_name = "checklist"

urlpatterns = [
    # Project Step URLs
    path(
        "step_add/",
        views.AddProjectStepView.as_view(),
        name="step_add",
    ),
    path(
        "setup/",
        views.ListProjectStepView.as_view(),
        name="checklist_setup",
    ),
    path("list/", views.ListStepView.as_view(), name="list_steps"),
    path(
        "",
        views.ProjectStepDetailView.as_view(),
        name="step_detail_default",
    ),
    path(
        "<int:step_id>/",
        views.ProjectStepDetailView.as_view(),
        name="step_detail",
    ),
    path(
        "<int:step_id>/delete/",
        views.RemoveProjectStepView.as_view(),
        name="step_delete",
    ),
    path(
        "reorder/",
        views.ReorderProjectStepsView.as_view(),
        name="step_reorder",
    ),
    # Task URLs
    path(
        "<int:step_id>/tasks/task_create/",
        views.AddProjectTaskView.as_view(),
        name="task_create",
    ),
    path(
        "<int:step_id>/tasks/<int:task_id>/task_status_update/",
        views.UpdateProjectTaskView.as_view(),
        name="task_status_update",
    ),
    path(
        "<int:step_id>/tasks/<int:task_id>/delete/",
        views.DeleteProjectTaskView.as_view(),
        name="task_delete",
    ),
    # Comments URLs
    path(
        "<int:step_id>/tasks/<int:task_id>/comments/",
        views.TaskCommentListView.as_view(),
        name="comment_list",
    ),
    path(
        "<int:step_id>/tasks/<int:task_id>/comments/create/",
        views.TaskCommentCreateView.as_view(),
        name="comment_create",
    ),
    path(
        "<int:step_id>/tasks/<int:task_id>/comments/<int:comment_id>/edit/",
        views.TaskCommentUpdateView.as_view(),
        name="comment_edit",
    ),
    path(
        "<int:step_id>/tasks/<int:task_id>/comments/<int:comment_id>/delete/",
        views.TaskCommentDeleteView.as_view(),
        name="comment_delete",
    ),
    # Helpers
    path(
        "<int:step_id>/tasks-btn/",
        views.toggle_task_form,
        name="toggle_task_form",
    ),


    path("<int:step_id>/header/", views.StepHeaderEditView.as_view(), name="step_header_edit"),
]
