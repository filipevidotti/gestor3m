import json

from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render

from apps.clientes.models import Cliente
from apps.core.decorators import consultor_required

from .models import AnaliseSwot


@consultor_required
def listar(request, cliente_pk):
    cliente = get_object_or_404(Cliente, pk=cliente_pk)
    analises = AnaliseSwot.objects.filter(cliente=cliente)
    return render(request, "swot/listar.html", {
        "cliente": cliente,
        "analises": analises,
    })


@consultor_required
def criar(request, cliente_pk):
    cliente = get_object_or_404(Cliente, pk=cliente_pk)

    if request.method == "POST":
        analise = AnaliseSwot.objects.create(
            cliente=cliente,
            consultor=request.user,
            data_analise=request.POST.get("data_analise"),
            forcas=json.loads(request.POST.get("forcas", "[]")),
            fraquezas=json.loads(request.POST.get("fraquezas", "[]")),
            oportunidades=json.loads(request.POST.get("oportunidades", "[]")),
            ameacas=json.loads(request.POST.get("ameacas", "[]")),
            segmento_mercado=request.POST.get("segmento_mercado", ""),
            publico_alvo=request.POST.get("publico_alvo", ""),
            concorrentes=request.POST.get("concorrentes", ""),
            diferencial=request.POST.get("diferencial", ""),
            observacoes_mercado=request.POST.get("observacoes_mercado", ""),
            produtos_principais=json.loads(request.POST.get("produtos_principais", "[]")),
            observacoes=request.POST.get("observacoes", ""),
        )
        messages.success(request, "Análise SWOT criada com sucesso.")
        return redirect("swot:detalhe", pk=analise.pk)

    return render(request, "swot/form.html", {
        "cliente": cliente,
        "editing": False,
    })


@consultor_required
def detalhe(request, pk):
    analise = get_object_or_404(
        AnaliseSwot.objects.select_related("cliente", "consultor"),
        pk=pk,
    )
    return render(request, "swot/detalhe.html", {
        "analise": analise,
        "cliente": analise.cliente,
    })


@consultor_required
def editar(request, pk):
    analise = get_object_or_404(
        AnaliseSwot.objects.select_related("cliente"),
        pk=pk,
    )

    if request.method == "POST":
        analise.data_analise = request.POST.get("data_analise")
        analise.forcas = json.loads(request.POST.get("forcas", "[]"))
        analise.fraquezas = json.loads(request.POST.get("fraquezas", "[]"))
        analise.oportunidades = json.loads(request.POST.get("oportunidades", "[]"))
        analise.ameacas = json.loads(request.POST.get("ameacas", "[]"))
        analise.segmento_mercado = request.POST.get("segmento_mercado", "")
        analise.publico_alvo = request.POST.get("publico_alvo", "")
        analise.concorrentes = request.POST.get("concorrentes", "")
        analise.diferencial = request.POST.get("diferencial", "")
        analise.observacoes_mercado = request.POST.get("observacoes_mercado", "")
        analise.produtos_principais = json.loads(request.POST.get("produtos_principais", "[]"))
        analise.observacoes = request.POST.get("observacoes", "")
        analise.save()
        messages.success(request, "Análise SWOT atualizada.")
        return redirect("swot:detalhe", pk=analise.pk)

    return render(request, "swot/form.html", {
        "cliente": analise.cliente,
        "analise": analise,
        "editing": True,
    })


@consultor_required
def excluir(request, pk):
    analise = get_object_or_404(AnaliseSwot, pk=pk)
    cliente_pk = analise.cliente_id
    if request.method == "POST":
        analise.soft_delete()
        messages.success(request, "Análise SWOT removida.")
    return redirect("swot:listar", cliente_pk=cliente_pk)


@consultor_required
def exportar_excel(request, pk):
    from .utils import gerar_excel

    analise = get_object_or_404(
        AnaliseSwot.objects.select_related("cliente", "consultor"),
        pk=pk,
    )
    return gerar_excel(analise)


@consultor_required
def exportar_pdf(request, pk):
    from .utils import gerar_pdf

    analise = get_object_or_404(
        AnaliseSwot.objects.select_related("cliente", "consultor"),
        pk=pk,
    )
    return gerar_pdf(analise)
