def modulos_usuario(request):
    """Injeta set de slugs dos módulos permitidos no contexto de todos os templates."""
    if not hasattr(request, "user") or not request.user.is_authenticated:
        return {"modulos_usuario": set()}
    return {"modulos_usuario": request.user.get_modulos_slugs()}
