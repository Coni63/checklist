# apps/projects/forms.py

from django import forms
from django.core.exceptions import ValidationError

from .models import Project


class ProjectCreationForm(forms.ModelForm):
    """
    Form use to create or update a Project instance
    If defines the fields, widgets, labels and help_texts for the form
    This form only handle project information (name, status, description)
    and not the related steps or tasks.
    """

    class Meta:
        model = Project
        fields = ["name", "status", "description"]
        widgets = {
            "name": forms.TextInput(
                attrs={
                    "placeholder": "Enter project name (e.g., Dinner Party)",
                    "autofocus": True,
                }
            ),
            "description": forms.Textarea(
                attrs={
                    "placeholder": "Optional: Describe your project...",
                    "rows": 4,
                }
            ),
        }
        labels = {
            "name": "Project Name",
            "description": "Description",
            "status": "Status",
        }
        help_texts = {
            "name": "Give your project a clear, descriptive name",
            "description": "Add any notes or context about this project",
            "status": "Set the current status of your project",
        }

    def clean_name(self):
        """Validate project name"""
        name = self.cleaned_data.get("name").strip()
        if not name:
            raise ValidationError("Project name is required")
        if len(name) < 3:
            raise ValidationError("Project name must be at least 3 characters")
        if not self.instance.pk:
            duplicated_name = Project.objects.filter(name__iexact=name)
            if duplicated_name.exists():
                raise ValidationError("Project name already used")
        return name
