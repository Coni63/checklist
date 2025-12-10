from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm

User = get_user_model()


class BasicRegisterForm(UserCreationForm):
    email = forms.EmailField(required=True, label="Email")

    class Meta:
        model = User
        fields = ("email", "username")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Cleanup help text to clean the form
        self.fields["username"].help_text = ""
        if "password1" in self.fields:
            self.fields["password1"].help_text = ""
        if "password2" in self.fields:
            self.fields["password2"].help_text = ""

    def save(self, commit=True):
        user = super().save(commit=False)
        user.username = self.cleaned_data["username"]
        user.email = self.cleaned_data["email"]
        if commit:
            user.save()
        return user


class UserEditForm(forms.ModelForm):
    """
    Form used to update an existing Django User instance's profile information.
    Defines the fields, widgets, labels, and help_texts for the form,
    focusing on basic user details like name and email.
    """

    class Meta:
        model = User
        fields = ["first_name", "last_name"]

        widgets = {
            "first_name": forms.TextInput(
                attrs={
                    "placeholder": "Enter your first name",
                    "autofocus": True,
                }
            ),
            "last_name": forms.TextInput(
                attrs={
                    "placeholder": "Enter your last name",
                }
            ),
        }

        labels = {
            "first_name": "First Name",
            "last_name": "Last Name",
        }

        help_texts = {
            "first_name": None,
            "last_name": None,
        }
