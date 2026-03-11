from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render


def _get_home_url(user):
    """Retorna URL inicial baseada no role do usuario."""
    if user.role in ("seller", "funcionario"):
        return "portal:dashboard"
    return "dashboard:index"


def login_view(request):
    if request.user.is_authenticated:
        return redirect(_get_home_url(request.user))
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            next_url = request.GET.get("next")
            if next_url:
                return redirect(next_url)
            return redirect(_get_home_url(user))
        return render(request, "accounts/login.html", {"error": "Credenciais inválidas"})
    return render(request, "accounts/login.html")


@login_required
def perfil(request):
    return render(request, "accounts/perfil.html")
