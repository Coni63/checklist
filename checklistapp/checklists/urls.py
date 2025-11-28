from django.urls import path
from . import views

app_name = "checklists"

urlpatterns = [
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
]
