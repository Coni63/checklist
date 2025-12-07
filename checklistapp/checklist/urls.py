from django.urls import path

from . import views
from projects.views import ProjectDetailView

app_name = "checklist"

urlpatterns = [
    # Project Step URLs
    path(
        "steps/step_add/",
        views.AddProjectStepView.as_view(),
        name="step_add",
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
