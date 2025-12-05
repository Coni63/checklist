from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.shortcuts import redirect, render

from .forms import BasicRegisterForm, UserEditForm


def login_view(request):
    if request.user.is_authenticated:
        return redirect("projects:project_list")

    if request.method == "GET":
        form = AuthenticationForm()
        return render(request, "accounts/login.html", {"form": form})
    else:
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect("projects:project_list")
        else:
            return render(request, "accounts/login.html", {"form": form})


def register_view(request):
    if request.method == "POST":
        form = BasicRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Connexion immédiate de l'utilisateur après l'inscription (optionnel)
            login(request, user)
            return redirect("projects:project_list")  # Redirigez vers une page d'accueil après l'inscription
        else:
            return render(request, "accounts/register.html", {"form": form})
    else:
        if request.user.is_authenticated:
            return redirect("projects:project_list")

        form = BasicRegisterForm()
        return render(request, "accounts/register.html", {"form": form})


@login_required  # Ensures only logged-in users can access this view
def my_profile(request):
    # The current logged-in user is request.user

    if request.method == "POST":
        # 1. Initialize the form with POST data AND the existing user instance
        form = UserEditForm(request.POST, instance=request.user)

        if form.is_valid():
            # 2. Save updates to the existing user
            form.save()
            # It's best practice to redirect after a successful POST
            return redirect("accounts:profile")  # Assuming you have a URL name 'my_profile'

        # If the form is NOT valid, fall through to render the template with errors

    else:  # This handles the initial GET request
        # 3. Initialize the form with the existing user instance so fields are pre-filled
        form = UserEditForm(instance=request.user)

    # 4. Render the correct template with the current user and the form
    return render(request, "accounts/profile.html", {"user": request.user, "form": form})
