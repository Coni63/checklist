from django import forms
from django.conf import settings
from django.contrib.auth.models import User

from core.utils import default_midnight
from .models import InventoryField, ProjectInventory


class DynamicInventoryForm(forms.Form):
    """
    Form built dynamically from Inventory + existing instance.
    """

    def __init__(self, inventory, roles, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.instance = inventory

        # Make sure they’re sorted
        template_fields = (
            inventory.fields.all()
            .order_by("group_order", "field_order")
        )

        for inst_field in template_fields:
            field_name = f"field_{inst_field.id}"

            existing_value = inst_field.get_value()

            hide_value = (
                inst_field.field_template
                and getattr(inst_field.field_template, "is_secret", False)
                and existing_value not in (None, "", [])
                and "admin" not in roles
            )

            read_only = "edit" not in roles

            form_field = self.build_field(inst_field, hide_value, read_only)

            # store grouping metadata
            form_field.group_name = inst_field.group_name or "Other"
            form_field.group_order = inst_field.group_order
            form_field.is_password = (inst_field.field_type == "password") and not hide_value

            self.fields[field_name] = form_field

    def build_field(self, tf, hide_value=False, read_only=False):
        existing_value = tf.get_value()

        if hide_value:
            return forms.CharField(
                label=tf.field_name,
                required=False,
                read_only=read_only,
                initial="•••••• (secret set)",
                widget=forms.TextInput(attrs={
                    "placeholder": "•••••• (secret set)",
                    "readonly": True,
                    "class": "input input-bordered w-full bg-gray-100 cursor-not-allowed"
                })
            )

        match tf.field_type:
            case "text":
                return forms.CharField(
                    label=tf.field_name,
                    required=False,
                    disabled=read_only,
                    initial=existing_value,
                    widget=forms.TextInput(attrs={"class": "input input-bordered w-full"})
                )
            case "number":
                return forms.DecimalField(
                    label=tf.field_name,
                    required=False,
                    disabled=read_only,
                    initial=existing_value,
                    widget=forms.NumberInput(attrs={"class": "input input-bordered w-full"})
                )
            case "url":
                return forms.URLField(
                    label=tf.field_name,
                    required=False,
                    disabled=read_only,
                    initial=existing_value,
                    widget=forms.URLInput(attrs={"class": "input input-bordered w-full"})
                )
            case "file":
                return forms.FileField(
                    label=tf.field_name,
                    required=False,
                    disabled=read_only,
                    initial=existing_value,
                    widget=forms.ClearableFileInput(attrs={"class": "file-input file-input-bordered w-full"})
                )
            case "password":
                return forms.CharField(
                    label=tf.field_name,
                    required=False,
                    disabled=read_only,
                    initial=existing_value,
                    widget=forms.PasswordInput(
                        render_value=True,
                        attrs={
                            "class": "input input-bordered w-full",
                            "data-password-field": "true",
                        }
                    ),
                )
            case "datetime":
                help_text=f"TZ: {settings.TIME_ZONE}"


                return forms.DateTimeField(
                    label=tf.field_name,
                    help_text=help_text,
                    required=False,
                    disabled=read_only,
                    initial=existing_value,
                    input_formats=["%Y-%m-%dT%H:%M:%S"],
                    widget=forms.DateTimeInput(
                        attrs={
                            "type": "datetime-local",
                            "step": "1",  # autorise les secondes
                            "class": "input input-bordered w-full",
                        },
                        format="%Y-%m-%dT%H:%M:%S",
                    ),
                )

        # fallback
        return forms.CharField(
            label=tf.field_name,
            required=False,
            disabled=read_only,
            widget=forms.TextInput(attrs={"class": "input input-bordered w-full"})
        )
    
    def save(self, is_admin):
        """
        Store all posted dynamic values into InventoryField model entries.
        """

        for name, field in self.fields.items():
            # field_<id>
            if not name.startswith("field_"):
                continue

            field_id = int(name.split("_")[1])
            inst_field = self.instance.fields.get(id=field_id)
            new_value = self.cleaned_data.get(name)

            # SECRET FIELD: prevent non-admin from editing if there was already a value
            if (
                inst_field.field_template
                and getattr(inst_field.field_template, "is_secret", False)
                and not is_admin
            ):
                # If non-admin submitted ANYTHING, ignore it completely
                # (They see a read-only placeholder anyway)
                continue

            if not new_value:
                continue

            # Save based on type
            match inst_field.field_type:
                case "text" | "url":
                    inst_field.text_value = new_value or ""
                case "number":
                    inst_field.number_value = new_value
                case "file":
                    if new_value:
                        inst_field.file_value = new_value
                case "password":
                    # Stored encrypted
                    inst_field.password_value = new_value
                case "datetime":
                    inst_field.datetime_value = new_value

            inst_field.save()