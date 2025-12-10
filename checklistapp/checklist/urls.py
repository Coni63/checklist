from django.urls import path
from projects.views import ProjectDetailView

from . import views

app_name = "checklist"

urlpatterns = [
    # Project Step URLs
    path(
        "steps/step_add/",
        views.AddProjectStepView.as_view(),
        name="step_add",
    ),
    path(
        "steps/<int:step_id>/edit/",
        views.EditProjectStepsView.as_view(),
        name="step_edit",
    ),
    path(
        "steps/<int:step_id>/edit_step_title_form",
        views.edit_step_title_form,
        name="edit_step_title_form",
    ),
    path(
        "steps/<int:step_id>/edit_step_description_form",
        views.edit_step_description_form,
        name="edit_step_description_form",
    ),
    path(
        "steps/<int:step_id>/get_step_title_display",
        views.get_step_title_display,
        name="get_step_title_display",
    ),
    path(
        "steps/<int:step_id>/get_step_description_display",
        views.get_step_description_display,
        name="get_step_description_display",
    ),
    path(
        "steps/<int:step_id>/",
        ProjectDetailView.as_view(),
        name="step_detail",
    ),
    path(
        "steps/<int:step_id>/delete/",
        views.RemoveProjectStepView.as_view(),
        name="step_delete",
    ),
    path(
        "steps/reorder/",
        views.ReorderProjectStepsView.as_view(),
        name="step_reorder",
    ),
    # Task URLs
    path(
        "steps/<int:step_id>/tasks/task_create/",
        views.AddProjectTaskView.as_view(),
        name="task_create",
    ),
    path(
        "steps/<int:step_id>/tasks/<int:task_id>/task_status_update/",
        views.UpdateProjectTaskView.as_view(),
        name="task_status_update",
    ),
    path(
        "steps/<int:step_id>/tasks/<int:task_id>/delete/",
        views.DeleteProjectTaskView.as_view(),
        name="task_delete",
    ),
    # Comments URLs
    path(
        "steps/<int:step_id>/tasks/<int:task_id>/comments/",
        views.TaskCommentListView.as_view(),
        name="comment_list",
    ),
    path(
        "steps/<int:step_id>/tasks/<int:task_id>/comments/create/",
        views.TaskCommentCreateView.as_view(),
        name="comment_create",
    ),
    path(
        "steps/<int:step_id>/tasks/<int:task_id>/comments/<int:comment_id>/edit/",
        views.TaskCommentUpdateView.as_view(),
        name="comment_edit",
    ),
    path(
        "steps/<int:step_id>/tasks/<int:task_id>/comments/<int:comment_id>/delete/",
        views.TaskCommentDeleteView.as_view(),
        name="comment_delete",
    ),
    # Helpers
    path(
        "steps/<int:step_id>/tasks-btn/",
        views.toggle_task_form,
        name="toggle_task_form",
    ),
]
