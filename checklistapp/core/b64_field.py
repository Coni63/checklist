import base64

from django import forms
from django.core.exceptions import ValidationError

# Définition de la limite de taille
MAX_FILE_SIZE = 1024 * 100  # 100 KB


class Base64FileField(forms.FileField):
    """
    Accepte un fichier en entrée, valide sa taille, et renvoie son contenu
    encodé en Base64.
    """

    uploaded_filename = None

    def clean(self, data, initial=None):
        # La validation standard de FileField se fait ici
        f = super().clean(data, initial)

        # Si aucun fichier n'a été uploadé (champ vide), on peut retourner None.
        if f is None:
            return None

        # 1. Validation de la Taille
        if f.size > MAX_FILE_SIZE:
            # Utilisez un format lisible pour l'erreur
            max_size_kb = MAX_FILE_SIZE / 1024
            raise ValidationError(f"Le fichier est trop volumineux. La taille maximale autorisée est de {max_size_kb:.0f} KB.")

        self.uploaded_filename = f.name

        # 2. Conversion en Base64
        # Lisez le contenu du fichier
        file_content = f.read()

        # Encodez le contenu en Base64
        b64_content = base64.b64encode(file_content).decode("utf-8")

        # Retournez la chaîne B64
        return b64_content
