from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model

User = get_user_model()

class BasicRegisterForm(UserCreationForm):
    # L'e-mail peut être utilisé comme nom d'utilisateur dans certains cas
    # ou simplement comme un champ supplémentaire.
    # Dans l'exemple suivant, on utilise le champ `username` par défaut de Django
    # pour ce que l'utilisateur pourrait percevoir comme son 'email' ou 'identifiant'.

    # Si vous voulez un champ 'email' séparé :
    email = forms.EmailField(required=True, label='Email')

    class Meta:
        model = User
        fields = ("email", "username") # on va mapper l'email sur le champ 'username'

    # Surcharge de la méthode save pour utiliser le champ 'email' comme username
    def save(self, commit=True):
        user = super().save(commit=False)
        user.username = self.cleaned_data["username"] # On utilise l'email comme identifiant unique
        user.email = self.cleaned_data["email"] # On utilise l'email comme identifiant unique
        if commit:
            user.save()
        return user
