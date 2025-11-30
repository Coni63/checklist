from django.shortcuts import redirect, render
from django.contrib.auth.forms import AuthenticationForm

# Create your views here.
def home(request):
    if request.user.is_authenticated:
        return redirect("projects:project_list")
        
    form = AuthenticationForm()
    return render(request, "homepage.html", {"form": form})