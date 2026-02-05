from django import forms
from django.utils.safestring import mark_safe


class LockedFieldWidget(forms.Widget):
    template_name = "widgets/locked_field.html"

    def render(self, name, value, attrs=None, renderer=None):
        return mark_safe("""
            <div class="input input-bordered w-full">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 text-gray-600" viewBox="0 0 20 20" fill="currentColor">
                    <path fill-rule="evenodd" d="M5 9V7a5 5 0 0110 0v2a2 2 0 012 2v5a2 2 0 01-2 2H5a2 2 0 01-2-2v-5a2 2 0 012-2zm8-2v2H7V7a3 3 0 016 0z" clip-rule="evenodd" />
                </svg>
                <span class="text-gray-600 font-medium">Not allowed</span>
            </div>
        """)

    def value_from_datadict(self, data, files, name):
        return None  # Le champ est en lecture seule
