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
    path(
        "<int:step_id>/edit/",
        views.EditProjectStepsView.as_view(),
        name="step_edit",
    ),
    path(
        "<int:step_id>/edit_step_title_form/",
        views.edit_step_title_form,
        name="edit_step_title_form",
    ),
    path(
        "<int:step_id>/edit_step_description_form/",
        views.edit_step_description_form,
        name="edit_step_description_form",
    ),
    path(
        "<int:step_id>/get_step_title_display/",
        views.get_step_title_display,
        name="get_step_title_display",
    ),
    path(
        "<int:step_id>/get_step_description_displa/y",
        views.get_step_description_display,
        name="get_step_description_display",
    ),
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
]
