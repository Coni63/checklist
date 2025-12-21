from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import Group

from .models import User, UserProjectPermissions

admin.site.register(User, UserAdmin)


class UserProjectPermissionsAdmin(admin.ModelAdmin):
    list_display = ("user", "project", "is_admin", "can_edit", "can_view")
    list_filter = ("is_admin", "can_edit", "can_view", "project")
    search_fields = ("user__username", "user__email", "project__name")
    list_editable = ("is_admin", "can_edit", "can_view")

    # Organiser les champs dans le formulaire
    fieldsets = (
        ("Association", {"fields": ("user", "project")}),
        (
            "Permissions",
            {
                "fields": ("is_admin", "can_edit", "can_view"),
                "description": "Note: is_admin active automatiquement can_edit et can_view. can_edit active automatiquement can_view.",
            },
        ),
    )

    # Actions groupées
    actions = ["make_admin", "make_editor", "make_viewer", "remove_edit_rights"]

    @admin.action(description="Rendre admin (active tous les droits)")
    def make_admin(self, request, queryset):
        queryset.update(is_admin=True, can_edit=True, can_view=True)
        self.message_user(request, f"{queryset.count()} permission(s) mise(s) à jour en admin.")

    @admin.action(description="Rendre éditeur (peut éditer et voir)")
    def make_editor(self, request, queryset):
        queryset.update(is_admin=False, can_edit=True, can_view=True)
        self.message_user(request, f"{queryset.count()} permission(s) mise(s) à jour en éditeur.")

    @admin.action(description="Rendre viewer (peut seulement voir)")
    def make_viewer(self, request, queryset):
        queryset.update(is_admin=False, can_edit=False, can_view=True)
        self.message_user(request, f"{queryset.count()} permission(s) mise(s) à jour en viewer.")

    @admin.action(description="Retirer droits d'édition")
    def remove_edit_rights(self, request, queryset):
        queryset.update(is_admin=False, can_edit=False)
        self.message_user(request, f"Droits d'édition retirés pour {queryset.count()} permission(s).")

    def save_model(self, request, obj, form, change):
        # Appliquer la logique de dépendances
        if obj.is_admin:
            obj.can_edit = True
            obj.can_view = True
        elif obj.can_edit:
            obj.can_view = True

        super().save_model(request, obj, form, change)

    class Media:
        js = ("admin/js/permissions_logic.js",)


admin.site.register(UserProjectPermissions, UserProjectPermissionsAdmin)
admin.site.unregister(Group)
