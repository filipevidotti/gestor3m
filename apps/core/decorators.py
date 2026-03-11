from functools import wraps

from django.http import HttpResponseForbidden
from django.shortcuts import redirect


def role_required(*roles):
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect("accounts:login")
            if request.user.role not in roles:
                return HttpResponseForbidden("Acesso negado.")
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


def gestor_required(view_func):
    return role_required("gestor")(view_func)


def consultor_required(view_func):
    return role_required("gestor", "consultor")(view_func)


def comercial_required(view_func):
    return role_required("gestor", "comercial")(view_func)


def seller_required(view_func):
    return role_required("gestor", "consultor", "seller", "funcionario", "comercial")(view_func)


def modulo_required(slug):
    """Verifica se o usuário tem acesso ao módulo pelo slug.

    Uso: @modulo_required("propostas")
    Gestores sempre têm acesso. Outros roles precisam do módulo atribuído.
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect("accounts:login")
            if not request.user.tem_modulo(slug):
                return HttpResponseForbidden(
                    "Você não tem acesso a este módulo."
                )
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator
