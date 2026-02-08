import base64
from datetime import datetime

from django.core.exceptions import ValidationError
from django.core.validators import URLValidator


class InventoryFieldValidator:
    """Validateurs pour les champs d'inventaire"""

    @staticmethod
    def validate_text(value: str, max_length: int = 255) -> str:
        """Valide un champ texte"""
        if not isinstance(value, str):
            raise ValueError("Text value must be a string")

        if len(value.strip()) == 0:
            return None

        if len(value) > max_length:
            raise ValueError(f"Text too long. Maximum {max_length} characters")

        return value.strip()

    @staticmethod
    def validate_url(value: str) -> str:
        """Valide une URL"""
        if not value or len(value.strip()) == 0:
            return None

        url_validator = URLValidator()
        try:
            url_validator(value.strip())
        except ValidationError:
            raise ValueError("Invalid URL format")

        if len(value) > 2048:
            raise ValueError("URL too long. Maximum 2048 characters")

        return value.strip()

    @staticmethod
    def validate_number(value: str) -> float:
        """Valide un nombre"""
        if value.strip() == "":
            return None

        try:
            num = float(value)
        except (ValueError, TypeError):
            raise ValueError("Invalid number format")

        # Limites optionnelles
        if abs(num) > 1e15:  # Limite arbitraire
            raise ValueError("Number too large")

        return num

    @staticmethod
    def validate_datetime(value: str) -> datetime:
        """Valide une datetime"""
        if not value or len(value.strip()) == 0:
            return None

        # Essayer différents formats
        formats = [
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d %H:%M",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%dT%H:%M",
            "%Y-%m-%d",
            "%d/%m/%Y %H:%M:%S",
            "%d/%m/%Y %H:%M",
            "%d/%m/%Y",
        ]

        for fmt in formats:
            try:
                return datetime.strptime(value.strip(), fmt)
            except ValueError:
                continue

        raise ValueError("Invalid date/time format. Expected YYYY-MM-DD HH:MM:SS or similar")

    @staticmethod
    def validate_password(value: str, min_length: int = 1) -> str:
        if not value.strip():
            return None

        cleaned_value = value.strip()

        if len(cleaned_value) < min_length:
            raise ValueError("Password is too short")

        return cleaned_value

    @staticmethod
    def validate_file(file_content: bytes, filename: str, max_size: int = 100 * 1024) -> tuple[str, str]:
        """Valide un fichier et retourne (base64_content, filename)"""
        if not filename or len(filename.strip()) == 0:
            raise ValueError("Filename cannot be empty")

        if len(filename) > 255:
            raise ValueError("Filename too long. Maximum 255 characters")

        if not file_content:
            return None, None

        if len(file_content) > max_size:
            raise ValueError(f"File too large. Maximum {max_size // 1024} KB")

        # Valider l'extension (optionnel)
        allowed_extensions = [".pdf", ".jpg", ".jpeg", ".png", ".doc", ".docx", ".txt", ".csv"]
        if not any(filename.lower().endswith(ext) for ext in allowed_extensions):
            raise ValueError(f"File type not allowed. Allowed: {', '.join(allowed_extensions)}")

        b64_content = base64.b64encode(file_content).decode("utf-8")
        return b64_content, filename.strip()
