from django.shortcuts import redirect, render


def home(request):
    if request.user.is_authenticated:
        return redirect("projects:project_list")

    return render(request, "homepage.html")
