from django.contrib.auth import views as auth_views
from django.urls import path

from . import views

app_name = "accounts"

urlpatterns = [
    path(
        "login/",
        views.login_view,
        name="login",
    ),
    path(
        "logout/",
        auth_views.LogoutView.as_view(next_page="home:homepage"),
        name="logout",
    ),
    path("register/", views.register_view, name="register"),
    path("", views.my_profile, name="profile"),
    path("user_permissions/<int:project_id>/permissions/", views.ListUserForm.as_view(), name="user_permissions_list"),
    path(
        "user_permissions/<int:project_id>/permissions/<int:permission_id>/edit/",
        views.UpdateUserPermissionForm.as_view(),
        name="user_permissions_update",
    ),
    path(
        "user_permissions/<int:project_id>/permissions/add/", views.AddUserPermissionForm.as_view(), name="user_permissions_add"
    ),
]
