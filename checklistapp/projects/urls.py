from django.urls import include, path

from . import views

app_name = "projects"

urlpatterns = [
    # Project URLs
    path("", views.ProjectListView.as_view(), name="project_list"),
    path("create/", views.ProjectCreateView.as_view(), name="project_create"),
    path("<int:project_id>/edit/", views.ProjectEditView.as_view(), name="project_edit"),
    path(
        "<int:project_id>/delete/",
        views.ProjectDeleteView.as_view(),
        name="project_delete",
    ),
    path("<int:project_id>/steps/", include(("checklist.urls", "checklist"), namespace="checklist")),
    path("<int:project_id>/inventory/", include(("inventory.urls", "inventory"), namespace="inventory")),
]
