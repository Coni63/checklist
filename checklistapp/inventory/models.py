from django.db import models
from encrypted_fields.fields import EncryptedTextField
from templates_management.models import InventoryTemplate, TemplateField


class ProjectInventory(models.Model):
    project = models.ForeignKey("projects.Project", on_delete=models.CASCADE, related_name="inventories")
    inventory_template = models.ForeignKey(
        InventoryTemplate,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="Template this step was created from",
    )
    name = models.CharField(max_length=200, help_text="Custom title, overrides template name")
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=10)
    order = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["order"]
        unique_together = ["project", "order"]

    def __str__(self):
        return self.name

    def __repr__(self):
        return f"ProjectInventory(id={self.id}, name={self.name})"

    def to_str(self):
        if self.icon:
            return (
                "<span class='inline-flex items-center min-w-10 justify-center'>"
                f"{self.icon}"
                "</span>"
                f"{self.name}"
            )
        return (
            "<span class='inline-flex items-center min-w-10'></span>"
            f"{self.name}"
        )

class InventoryField(models.Model):
    inventory = models.ForeignKey(ProjectInventory, on_delete=models.CASCADE, related_name="fields")
    field_template = models.ForeignKey(
        TemplateField,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="Template this task was created from",
    )

    group_name = models.CharField(max_length=100)
    group_order = models.PositiveIntegerField(default=1)

    field_name = models.CharField(max_length=200)
    field_order = models.PositiveIntegerField(default=1)
    field_type = models.CharField(max_length=20, choices=TemplateField.FIELD_TYPES)

    text_value = models.CharField(
        max_length=500,  # Augmenté la taille pour être plus flexible pour les URL/texte long
        blank=True,
        default="",
    )
    number_value = models.IntegerField(null=True, blank=True)
    file_value = models.TextField(  # store b64 file
        blank=True,
        default="",
    )
    # Requires https://pypi.org/project/django-fernet-encrypted-fields/
    password_value = EncryptedTextField(max_length=500, null=True, blank=True)
    datetime_value = models.DateTimeField(null=True, blank=True)

    def get_value(self):
        """
        Return the proper value based on type
        """
        if self.field_type in ["text", "url"]:
            return self.text_value
        elif self.field_type == "number":
            return self.number_value
        elif self.field_type == "file":
            return self.file_value
        elif self.field_type == "password":
            return self.password_value
        elif self.field_type == "datetime":
            return self.datetime_value
        return None
