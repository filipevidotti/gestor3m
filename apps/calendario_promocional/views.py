from datetime import date, timedelta

from django.contrib import messages
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from apps.clientes.models import Cliente
from apps.core.decorators import consultor_required, gestor_required

from .forms import DataPromocionalForm, PreparacaoForm
from .models import DataPromocional, PreparacaoPromocional


@consultor_required
def calendario(request):
    """Visão calendário das datas promocionais."""
    hoje = date.today()
    ano = int(request.GET.get("ano", hoje.year))

    datas = DataPromocional.objects.filter(
        data_inicio__year=ano, is_active=True
    ).order_by("data_inicio")

    # Agrupar por mês
    meses = {}
    for d in datas:
        mes = d.data_inicio.month
        if mes not in meses:
            meses[mes] = []
        meses[mes].append(d)

    NOMES_MES = {
        1: "Janeiro", 2: "Fevereiro", 3: "Março", 4: "Abril",
        5: "Maio", 6: "Junho", 7: "Julho", 8: "Agosto",
        9: "Setembro", 10: "Outubro", 11: "Novembro", 12: "Dezembro",
    }

    meses_lista = [
        {"numero": m, "nome": NOMES_MES[m], "datas": meses.get(m, [])}
        for m in range(1, 13)
    ]

    # Próximas datas (com preparo)
    proximas = DataPromocional.objects.filter(
        data_inicio__gte=hoje, is_active=True
    ).order_by("data_inicio")[:5]

    # Datas que precisam de preparo (dentro da janela de antecedência)
    alertas = []
    for d in DataPromocional.objects.filter(data_inicio__gte=hoje, is_active=True):
        dias_ate = (d.data_inicio - hoje).days
        if dias_ate <= d.antecedencia_preparo_dias:
            alertas.append(d)

    return render(request, "calendario_promocional/calendario.html", {
        "meses": meses_lista,
        "ano": ano,
        "proximas": proximas,
        "alertas": alertas,
        "hoje": hoje,
    })


@consultor_required
def detalhe_data(request, pk):
    """Detalhe de uma data promocional com preparações dos clientes."""
    data_promo = get_object_or_404(DataPromocional, pk=pk)

    if request.user.is_gestor:
        clientes = Cliente.objects.all()
    else:
        clientes = Cliente.objects.filter(consultor=request.user)

    preparacoes = PreparacaoPromocional.objects.filter(
        data_promocional=data_promo,
        cliente__in=clientes,
    ).select_related("cliente", "consultor")

    # Clientes sem preparação
    clientes_com_prep = preparacoes.values_list("cliente_id", flat=True)
    clientes_sem_prep = clientes.exclude(pk__in=clientes_com_prep)

    return render(request, "calendario_promocional/detalhe.html", {
        "data_promo": data_promo,
        "preparacoes": preparacoes,
        "clientes_sem_prep": clientes_sem_prep,
    })


@consultor_required
def iniciar_preparacao(request, pk, cliente_pk):
    """Inicia preparação de um cliente para uma data promocional."""
    data_promo = get_object_or_404(DataPromocional, pk=pk)
    cliente = get_object_or_404(Cliente, pk=cliente_pk)

    prep, created = PreparacaoPromocional.objects.get_or_create(
        data_promocional=data_promo,
        cliente=cliente,
        defaults={
            "consultor": request.user,
            "status": "preparando",
        },
    )
    if created:
        messages.success(request, f"Preparação iniciada para {cliente.empresa}!")
    return redirect("calendario_promocional:detalhe", pk=pk)


@consultor_required
def editar_preparacao(request, pk):
    """Edita preparação de um cliente."""
    prep = get_object_or_404(PreparacaoPromocional, pk=pk)

    if request.method == "POST":
        form = PreparacaoForm(request.POST, instance=prep)
        if form.is_valid():
            form.save()
            messages.success(request, "Preparação atualizada!")
            return redirect("calendario_promocional:detalhe", pk=prep.data_promocional.pk)
    else:
        form = PreparacaoForm(instance=prep)

    return render(request, "calendario_promocional/editar_preparacao.html", {
        "form": form,
        "prep": prep,
    })


@gestor_required
def criar_data(request):
    """Cria nova data promocional."""
    if request.method == "POST":
        form = DataPromocionalForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Data promocional criada!")
            return redirect("calendario_promocional:calendario")
    else:
        form = DataPromocionalForm()

    return render(request, "calendario_promocional/form_data.html", {
        "form": form,
        "form_title": "Nova Data Promocional",
    })


@gestor_required
def editar_data(request, pk):
    """Edita data promocional."""
    data_promo = get_object_or_404(DataPromocional, pk=pk)

    if request.method == "POST":
        form = DataPromocionalForm(request.POST, instance=data_promo)
        if form.is_valid():
            form.save()
            messages.success(request, "Data promocional atualizada!")
            return redirect("calendario_promocional:detalhe", pk=pk)
    else:
        form = DataPromocionalForm(instance=data_promo)

    return render(request, "calendario_promocional/form_data.html", {
        "form": form,
        "form_title": "Editar Data Promocional",
    })


@gestor_required
def excluir_data(request, pk):
    """Exclui data promocional."""
    data_promo = get_object_or_404(DataPromocional, pk=pk)
    if request.method == "POST":
        data_promo.soft_delete()
        messages.success(request, "Data promocional removida!")
        return redirect("calendario_promocional:calendario")
    return render(request, "components/_confirm_delete.html", {
        "object": data_promo,
        "cancel_url": "/calendario/",
    })
