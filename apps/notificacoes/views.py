from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render

from .models import Notificacao


@login_required
def listar(request):
    notificacoes = Notificacao.objects.filter(
        destinatario=request.user
    ).order_by("-created_at")[:50]
    return render(request, "notificacoes/listar.html", {"notificacoes": notificacoes})


@login_required
def marcar_lida(request, pk):
    notificacao = get_object_or_404(Notificacao, pk=pk, destinatario=request.user)
    notificacao.lida = True
    notificacao.save(update_fields=["lida", "updated_at"])
    if request.htmx:
        return render(request, "notificacoes/_item.html", {"notificacao": notificacao})
    return JsonResponse({"ok": True})
