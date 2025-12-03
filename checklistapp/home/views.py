from django.contrib.auth.forms import AuthenticationForm
from django.shortcuts import redirect, render


def home(request):
    if request.user.is_authenticated:
        return redirect("projects:project_list")

    form = AuthenticationForm()
    return render(request, "homepage.html", {"form": form})
