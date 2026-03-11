from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render

from apps.core.decorators import consultor_required
from .forms import ReuniaoForm
from .models import Reuniao


@login_required
def listar(request):
    if request.user.is_gestor:
        reunioes = Reuniao.objects.select_related("cliente", "consultor").all()
    elif request.user.is_consultor:
        reunioes = Reuniao.objects.filter(consultor=request.user).select_related("cliente")
    else:
        reunioes = Reuniao.objects.filter(cliente__usuario=request.user).select_related("cliente")
    return render(request, "reunioes/listar.html", {"reunioes": reunioes})


@consultor_required
def criar(request):
    if request.method == "POST":
        form = ReuniaoForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Reuniao registrada.")
            return redirect("reunioes:listar")
    else:
        form = ReuniaoForm()
        if request.user.is_consultor:
            form.fields["consultor"].initial = request.user
    return render(request, "reunioes/form.html", {
        "form": form,
        "form_title": "Nova Reuniao",
        "cancel_url": "/reunioes/",
    })


@consultor_required
def editar(request, pk):
    reuniao = get_object_or_404(Reuniao, pk=pk)
    if request.method == "POST":
        form = ReuniaoForm(request.POST, instance=reuniao)
        if form.is_valid():
            form.save()
            messages.success(request, "Reuniao atualizada.")
            return redirect("reunioes:listar")
    else:
        form = ReuniaoForm(instance=reuniao)
    return render(request, "reunioes/form.html", {
        "form": form,
        "form_title": "Editar Reuniao",
        "cancel_url": "/reunioes/",
    })


@consultor_required
def excluir(request, pk):
    reuniao = get_object_or_404(Reuniao, pk=pk)
    if request.method == "POST":
        reuniao.delete()
        messages.success(request, "Reuniao removida.")
        return redirect("reunioes:listar")
    return render(request, "components/_confirm_delete.html", {
        "object": reuniao,
        "cancel_url": "/reunioes/",
    })


# ── Gravação + IA ──────────────────────────────────────


@consultor_required
def gravar_reuniao(request, pk):
    """Tela de gravação de reunião com transcrição ao vivo."""
    reuniao = get_object_or_404(Reuniao, pk=pk)
    return render(request, "reunioes/gravar.html", {"reuniao": reuniao})


@consultor_required
def salvar_gravacao(request, pk):
    """Recebe áudio gravado + transcrição rascunho via POST."""
    reuniao = get_object_or_404(Reuniao, pk=pk)

    if request.method == "POST":
        # Salvar áudio
        audio = request.FILES.get("audio")
        if audio:
            reuniao.audio_arquivo = audio

        # Salvar transcrição rascunho (Web Speech API)
        transcricao_rascunho = request.POST.get("transcricao_rascunho", "")
        if transcricao_rascunho:
            reuniao.transcricao_rascunho = transcricao_rascunho

        # Salvar duração
        duracao = request.POST.get("duracao_minutos")
        if duracao:
            try:
                reuniao.duracao_minutos = int(duracao)
            except (ValueError, TypeError):
                pass

        reuniao.transcricao_status = "pendente"
        reuniao.save()

        # Disparar task de processamento (Whisper + análise IA)
        from apps.ia.tasks import processar_reuniao
        processar_reuniao.delay(reuniao.id)

        messages.success(request, "Gravação salva! Transcrição e análise em processamento.")
        return redirect("reunioes:detalhe", pk=reuniao.pk)

    return HttpResponse(status=405)


@consultor_required
def status_transcricao(request, pk):
    """Retorna status da transcrição (HTMX poll)."""
    reuniao = get_object_or_404(Reuniao, pk=pk)

    if request.headers.get("HX-Request"):
        return render(request, "reunioes/partials/status_transcricao.html", {
            "reuniao": reuniao,
        })

    return JsonResponse({
        "status": reuniao.transcricao_status,
        "has_resumo": bool(reuniao.resumo_ia),
    })


@consultor_required
def detalhe(request, pk):
    """Detalhe da reunião com resultados de IA."""
    reuniao = get_object_or_404(
        Reuniao.objects.select_related("cliente", "consultor"),
        pk=pk,
    )
    return render(request, "reunioes/detalhe.html", {"reuniao": reuniao})
