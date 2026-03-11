from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from .models import Achievement, UserAchievement
from .services import get_ranking, get_total_pontos


@login_required
def ranking(request):
    role_filter = request.GET.get("role")

    ranking_consultores = get_ranking(role="consultor", limit=20)
    ranking_sellers = get_ranking(role="seller", limit=20)

    return render(request, "gamificacao/ranking.html", {
        "ranking_consultores": ranking_consultores,
        "ranking_sellers": ranking_sellers,
        "meus_pontos": get_total_pontos(request.user),
    })


@login_required
def conquistas(request):
    usuario = request.user
    desbloqueadas = UserAchievement.objects.filter(
        usuario=usuario
    ).select_related("achievement").order_by("-desbloqueado_em")

    if usuario.role in ("consultor", "gestor"):
        publicos = ["consultor", "ambos"]
    else:
        publicos = ["seller", "ambos"]

    todas = Achievement.objects.filter(publico__in=publicos)
    ids_desbloqueados = set(d.achievement_id for d in desbloqueadas)
    bloqueadas = todas.exclude(pk__in=ids_desbloqueados)

    return render(request, "gamificacao/conquistas.html", {
        "desbloqueadas": desbloqueadas,
        "bloqueadas": bloqueadas,
        "meus_pontos": get_total_pontos(usuario),
    })
