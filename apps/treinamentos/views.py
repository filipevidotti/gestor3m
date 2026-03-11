from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string

from apps.clientes.models import Cliente
from apps.core.decorators import consultor_required, gestor_required
from .forms import RegistrarTreinamentoForm, TreinamentoForm
from .models import Treinamento, TreinamentoRealizado


@login_required
def listar(request):
    treinamentos = Treinamento.objects.all()
    return render(request, "treinamentos/listar.html", {"treinamentos": treinamentos})


@gestor_required
def criar(request):
    if request.method == "POST":
        form = TreinamentoForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, "Treinamento criado.")
            return redirect("treinamentos:listar")
    else:
        form = TreinamentoForm()
    return render(request, "treinamentos/form.html", {
        "form": form,
        "form_title": "Novo Treinamento",
        "cancel_url": "/treinamentos/",
    })


@gestor_required
def editar(request, pk):
    treinamento = get_object_or_404(Treinamento, pk=pk)
    if request.method == "POST":
        form = TreinamentoForm(request.POST, request.FILES, instance=treinamento)
        if form.is_valid():
            form.save()
            messages.success(request, "Treinamento atualizado.")
            return redirect("treinamentos:listar")
    else:
        form = TreinamentoForm(instance=treinamento)
    return render(request, "treinamentos/form.html", {
        "form": form,
        "form_title": f"Editar: {treinamento.titulo}",
        "cancel_url": "/treinamentos/",
    })


@gestor_required
def excluir(request, pk):
    treinamento = get_object_or_404(Treinamento, pk=pk)
    if request.method == "POST":
        treinamento.delete()
        messages.success(request, "Treinamento removido.")
        return redirect("treinamentos:listar")
    return render(request, "components/_confirm_delete.html", {
        "object": treinamento,
        "cancel_url": "/treinamentos/",
    })


@consultor_required
def registrar_realizado(request, cliente_pk):
    """Consultor registra treinamento como realizado para um cliente."""
    cliente = get_object_or_404(Cliente, pk=cliente_pk)

    if request.method == "POST":
        form = RegistrarTreinamentoForm(request.POST, request.FILES, cliente=cliente)
        if form.is_valid():
            form.save()
            messages.success(request, "Treinamento registrado com sucesso.")
            return redirect("clientes:detalhe", pk=cliente_pk)
    else:
        from django.utils import timezone
        form = RegistrarTreinamentoForm(cliente=cliente, initial={"data": timezone.now().date()})

    return render(request, "treinamentos/_registrar_form.html", {
        "form": form,
        "cliente": cliente,
    })


@consultor_required
def remover_realizado(request, pk):
    """Remove registro de treinamento realizado."""
    realizado = get_object_or_404(TreinamentoRealizado, pk=pk)
    cliente_pk = realizado.cliente_id
    if request.method == "POST":
        realizado.delete()
        messages.success(request, "Registro removido.")
    return redirect("clientes:detalhe", pk=cliente_pk)
