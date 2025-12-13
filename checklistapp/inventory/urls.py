from django.urls import path

from . import views

app_name = "inventory"

urlpatterns = [
    # Configuration Inventory URLs
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
    # Project Inventory pages
    path(
        "",
        views.InventoryDetail.as_view(),
        name="inventory_page",
    ),
    path(
        "<int:inventory_id>/",
        views.InventoryDetail.as_view(),
        name="inventory_detail",
    ),
    path(
        "list_inventory/",
        views.InventoryList.as_view(),
        name="list_inventory",
    ),
    path("<int:inventory_id>/field/<int:field_id>/download", views.download_inventory_file, name="download_inventory_file"),
    path("<int:inventory_id>/header/", views.inventory_header_edit, name="inventory_header_edit"),
]
