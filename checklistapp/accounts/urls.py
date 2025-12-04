from django.contrib.auth import views as auth_views
from django.urls import path
from . import views

app_name = "accounts"

urlpatterns = [
    path(
        "login/",
        # auth_views.LoginView.as_view(redirect_authenticated_user=True, next_page="projects:project_list"),
        views.login_view,
        name="login",
    ),
    path(
        "logout/",
        auth_views.LogoutView.as_view(next_page="home:homepage"),
        name="logout",
    ),
    path('register/', views.register_view, name='register'),
    path('', views.my_profile, name='profile'),
]
