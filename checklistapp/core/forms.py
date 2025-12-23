import base64

from django import forms
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import UploadedFile

# Définition de la limite de taille
MAX_FILE_SIZE = 1024 * 100  # 100 KB


class Base64FileField(forms.FileField):
    uploaded_filename = None

    def clean(self, data, initial=None):
        # Aucun nouveau fichier → conserver l'existant
        if data is None:
            return initial

        # Validation standard Django
        f = super().clean(data, initial)

        if not isinstance(f, UploadedFile):
            return initial

        # Validation taille
        if f.size > MAX_FILE_SIZE:
            max_size_kb = MAX_FILE_SIZE / 1024
            raise ValidationError(f"File is too large. Maximum: {max_size_kb:.0f} KB.")

        self.uploaded_filename = f.name

        content = f.read()
        return base64.b64encode(content).decode("utf-8")
