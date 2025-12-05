from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm

User = get_user_model()


class BasicRegisterForm(UserCreationForm):
    # L'e-mail peut être utilisé comme nom d'utilisateur dans certains cas
    # ou simplement comme un champ supplémentaire.
    # Dans l'exemple suivant, on utilise le champ `username` par défaut de Django
    # pour ce que l'utilisateur pourrait percevoir comme son 'email' ou 'identifiant'.

    # Si vous voulez un champ 'email' séparé :
    email = forms.EmailField(required=True, label="Email")

    class Meta:
        model = User
        fields = ("email", "username")  # on va mapper l'email sur le champ 'username'

    # Surcharge de la méthode save pour utiliser le champ 'email' comme username
    def save(self, commit=True):
        user = super().save(commit=False)
        user.username = self.cleaned_data["username"]  # On utilise l'email comme identifiant unique
        user.email = self.cleaned_data["email"]  # On utilise l'email comme identifiant unique
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
        # Use the imported User model
        model = User
        # Select relevant User fields
        fields = ["first_name", "last_name", "email"]

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
            "email": forms.EmailInput(
                attrs={
                    "placeholder": "Enter your email address",
                    "readonly": "readonly",  # Make email read-only
                }
            ),
        }

        labels = {
            "first_name": "First Name",
            "last_name": "Last Name",
            "email": "Email Address",
        }

        help_texts = {
            "first_name": "Your given name.",
            "last_name": "Your family name.",
            "email": "Your primary contact email. Cannot be modified.",
        }
