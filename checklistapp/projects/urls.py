from django.contrib import admin
from django.urls import path

from projects.views import ProjectListView, ProjectCreateView, ProjectSetupViewV2, ProjectDetailView

app_name = "projects"

urlpatterns = [
    path('', ProjectListView.as_view(), name='project_list'),
    path('create/', ProjectCreateView.as_view(), name='project_create'),
    path('<int:pk>/setup/', ProjectSetupViewV2.as_view(), name='project_setup'),
    path('<int:pk>/', ProjectDetailView.as_view(), name='project_detail'),
]