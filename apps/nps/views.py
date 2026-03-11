import json

from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from apps.clientes.models import Cliente
from apps.core.decorators import gestor_required

from .models import PesquisaNPS, RespostaNPS


@gestor_required
def listar(request):
    """Lista pesquisas NPS."""
    pesquisas = PesquisaNPS.objects.all().order_by("-created_at")
    return render(request, "nps/listar.html", {"pesquisas": pesquisas})


@gestor_required
def criar(request):
    """Cria nova pesquisa NPS."""
    if request.method == "POST":
        titulo = request.POST.get("titulo", "").strip()
        descricao = request.POST.get("descricao", "").strip()

        if not titulo:
            messages.error(request, "Título é obrigatório.")
            return render(request, "nps/form.html", {"dados": request.POST})

        pesquisa = PesquisaNPS.objects.create(
            titulo=titulo,
            descricao=descricao,
            criado_por=request.user,
        )

        # Criar respostas pendentes para todos os clientes ativos
        clientes = Cliente.objects.filter(status="ativo")
        respostas = [
            RespostaNPS(pesquisa=pesquisa, cliente=c, nota=0)
            for c in clientes
        ]
        RespostaNPS.objects.bulk_create(respostas)

        messages.success(request, f"Pesquisa criada com {len(respostas)} convites.")
        return redirect("nps:detalhe", pk=pesquisa.pk)

    return render(request, "nps/form.html", {"dados": {}})


@gestor_required
def detalhe(request, pk):
    """Detalhe da pesquisa com resultados NPS."""
    pesquisa = get_object_or_404(PesquisaNPS, pk=pk)
    respostas = pesquisa.respostas.select_related("cliente").order_by("-respondido_em")

    respondidas = respostas.exclude(respondido_em=None)
    pendentes = respostas.filter(respondido_em=None)

    dist = pesquisa.distribuicao
    nps = pesquisa.nps_score

    # Dados para gráfico
    notas_dist = [0] * 11
    for r in respondidas:
        notas_dist[r.nota] += 1

    context = {
        "pesquisa": pesquisa,
        "respondidas": respondidas,
        "pendentes": pendentes,
        "distribuicao": dist,
        "nps": nps,
        "notas_dist_json": json.dumps(notas_dist),
    }
    return render(request, "nps/detalhe.html", context)


@gestor_required
def enviar(request, pk):
    """Envia (ou reenvia) pesquisa NPS via WhatsApp para pendentes."""
    pesquisa = get_object_or_404(PesquisaNPS, pk=pk)

    if request.method == "POST":
        from apps.core.services.evolution import enviar_mensagem

        pendentes = pesquisa.respostas.filter(
            respondido_em=None
        ).select_related("cliente__usuario")

        count = 0
        for resp in pendentes:
            seller = getattr(resp.cliente, "usuario", None)
            if seller and seller.telefone:
                texto = (
                    f"Ola {seller.first_name}! 📊\n\n"
                    f"Gostaríamos de saber sua opinião sobre nosso trabalho.\n\n"
                    f"*{pesquisa.titulo}*\n\n"
                    f"Responda em 1 minuto:\n"
                    f"👉 {{BASE_URL}}/nps/responder/{resp.token}/\n\n"
                    f"_3M Consultoria_"
                )
                if enviar_mensagem(seller.telefone, texto):
                    count += 1

        messages.success(request, f"Pesquisa enviada para {count} clientes via WhatsApp.")

    return redirect("nps:detalhe", pk=pk)


def responder(request, token):
    """Página pública onde o seller responde à pesquisa NPS."""
    resp = get_object_or_404(RespostaNPS.objects.select_related("pesquisa", "cliente"), token=token)

    if resp.respondido_em:
        return render(request, "nps/ja_respondido.html", {"resposta": resp})

    if request.method == "POST":
        nota = request.POST.get("nota")
        comentario = request.POST.get("comentario", "").strip()

        if nota is not None:
            resp.nota = int(nota)
            resp.comentario = comentario
            resp.respondido_em = timezone.now()
            resp.save()
            return render(request, "nps/agradecimento.html", {"resposta": resp})

    return render(request, "nps/responder.html", {
        "resposta": resp,
        "pesquisa": resp.pesquisa,
    })
