from django.urls import include, path

from . import views

app_name = "projects"

urlpatterns = [
    # Project URLs
    path("", views.ProjectListView.as_view(), name="project_list"),
    path("create/", views.ProjectCreateView.as_view(), name="project_create"),
    path("<int:project_id>/edit/", views.ProjectEditView.as_view(), name="project_edit"),
    path("<int:project_id>/detail/", views.ProjectDetailView.as_view(), name="project_detail"),
    path(
        "<int:project_id>/delete/",
        views.ProjectDeleteView.as_view(),
        name="project_delete",
    ),
    path("<int:project_id>/", include(("checklist.urls", "checklist"), namespace="checklist")),
]
