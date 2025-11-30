from django.urls import path
from django.contrib.auth import views as auth_views

app_name = "accounts"

urlpatterns = [
    path("login/", auth_views.LoginView.as_view(
        redirect_authenticated_user=True, 
        next_page="projects:project_list"
    ), name="login"),
    path("logout/", auth_views.LogoutView.as_view(next_page="home:homepage"), name="logout"),
]
