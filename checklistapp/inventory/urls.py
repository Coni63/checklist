from django.urls import path

from . import views

app_name = "inventory"

urlpatterns = [
    # Project Inventory URLs
    path(
        "inventory_add/",
        views.AddProjectInventoryView.as_view(),
        name="inventory_add",
    ),
    path(
        "setup/",
        views.ListProjectInventoryView.as_view(),
        name="inventory_setup",
    ),
    path(
        "reorder/",
        views.ReorderProjectInventoryView.as_view(),
        name="inventory_reorder",
    ),
    path(
        "<int:inventory_id>/delete/",
        views.RemoveProjectInventoryView.as_view(),
        name="inventory_delete",
    ),
    path(
        "",
        views.ProjectInventoryDetailView.as_view(),
        name="inventory_detail_default",
    ),
    path(
        "<int:inventory_id>/",
        views.ProjectInventoryDetailView.as_view(),
        name="inventory_detail",
    ),
    path("<int:inventory_id>/field/<int:field_id>/download", views.download_inventory_file, name='download_inventory_file'),
]