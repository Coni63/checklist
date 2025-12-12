from django.urls import path

from . import views

app_name = "inventory"

urlpatterns = [
    # Project Inventory URLs
    path(
        "add/",
        views.AddProjectInventoryView.as_view(),
        name="inventory_add",
    ),
    path(
        "reorder/",
        views.ReorderProjectInventoryView.as_view(),
        name="inventory_reorder",
    ),
    path(
        "inventory/<int:inventory_id>/delete",
        views.RemoveProjectInventoryView.as_view(),
        name="inventory_delete",
    ),
    path(
        "/",
        views.ListProjectInventoryView.as_view(),
        name="inventory_setup",
    ),
]