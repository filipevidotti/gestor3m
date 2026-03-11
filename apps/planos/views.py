from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from apps.clientes.models import Cliente
from apps.core.decorators import consultor_required
from .forms import PlanoAcaoForm, ItemPlanoForm
from .models import PlanoAcao, ItemPlano


@login_required
def listar(request, cliente_pk):
    cliente = get_object_or_404(Cliente, pk=cliente_pk)
    planos = PlanoAcao.objects.filter(cliente=cliente).prefetch_related("itens")
    return render(request, "planos/listar.html", {"cliente": cliente, "planos": planos})


@consultor_required
def criar(request, cliente_pk):
    cliente = get_object_or_404(Cliente, pk=cliente_pk)
    if request.method == "POST":
        form = PlanoAcaoForm(request.POST)
        if form.is_valid():
            plano = form.save(commit=False)
            plano.cliente = cliente
            plano.save()
            messages.success(request, "Plano criado.")
            return redirect("planos:detalhe", pk=plano.pk)
    else:
        form = PlanoAcaoForm(initial={"cliente": cliente})
    return render(request, "planos/form.html", {
        "form": form,
        "form_title": f"Novo Plano: {cliente.empresa}",
        "cancel_url": f"/planos/cliente/{cliente.pk}/",
    })


@login_required
def detalhe(request, pk):
    plano = get_object_or_404(PlanoAcao.objects.prefetch_related("itens__responsavel"), pk=pk)
    item_form = ItemPlanoForm()
    return render(request, "planos/detalhe.html", {
        "plano": plano,
        "item_form": item_form,
    })


@consultor_required
def adicionar_item(request, pk):
    plano = get_object_or_404(PlanoAcao, pk=pk)
    if request.method == "POST":
        form = ItemPlanoForm(request.POST)
        if form.is_valid():
            item = form.save(commit=False)
            item.plano = plano
            item.save()
            if request.htmx:
                return render(request, "planos/_item.html", {"item": item, "plano": plano})
            messages.success(request, "Item adicionado.")
    return redirect("planos:detalhe", pk=plano.pk)


@login_required
def toggle_item(request, pk, item_pk):
    item = get_object_or_404(ItemPlano, pk=item_pk, plano_id=pk)
    if item.status == "concluido":
        item.status = "pendente"
    else:
        item.status = "concluido"
    item.save()
    if request.htmx:
        plano = item.plano
        return render(request, "planos/_item.html", {"item": item, "plano": plano})
    return redirect("planos:detalhe", pk=pk)
