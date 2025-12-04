from django.shortcuts import render, redirect
from django.contrib.auth import login
from .forms import BasicRegisterForm

from django.contrib.auth.forms import AuthenticationForm
from django.shortcuts import redirect, render


def login_view(request):
    if request.user.is_authenticated:
        return redirect("projects:project_list")

    if request.method == 'GET':
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
    if request.method == 'POST':
        form = BasicRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Connexion immédiate de l'utilisateur après l'inscription (optionnel)
            login(request, user)
            return redirect('projects:project_list') # Redirigez vers une page d'accueil après l'inscription
        else:
            return render(request, 'accounts/register.html', {'form': form})
    else:
        if request.user.is_authenticated:
            return redirect("projects:project_list")

        form = BasicRegisterForm()
        return render(request, 'accounts/register.html', {'form': form})


def my_profile(request):
    return render(request, 'accounts/profile.html')