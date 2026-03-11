from django.contrib import messages
from django.contrib.auth import get_user_model
from django.shortcuts import render, redirect, get_object_or_404

from apps.clientes.models import Cliente
from apps.core.decorators import gestor_required
from .forms import ConsultorForm, VendedorForm
from .models import Consultor

User = get_user_model()


@gestor_required
def listar(request):
    consultores = Consultor.objects.select_related("usuario").all()
    vendedores = User.objects.filter(role=User.Role.COMERCIAL, is_active=True)
    tab = request.GET.get("tab", "consultores")
    return render(request, "consultores/listar.html", {
        "consultores": consultores,
        "vendedores": vendedores,
        "tab": tab,
    })


def detalhe(request, pk):
    consultor = get_object_or_404(Consultor.objects.select_related("usuario"), pk=pk)
    clientes = Cliente.objects.filter(consultor=consultor.usuario)
    return render(request, "consultores/detalhe.html", {
        "consultor": consultor,
        "clientes": clientes,
    })


@gestor_required
def criar(request):
    if request.method == "POST":
        form = ConsultorForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Consultor criado com sucesso.")
            return redirect("consultores:listar")
    else:
        form = ConsultorForm()
    return render(request, "consultores/form.html", {
        "form": form,
        "form_title": "Novo Consultor",
        "cancel_url": "consultores:listar",
        "submit_label": "Criar Consultor",
    })


@gestor_required
def editar(request, pk):
    consultor = get_object_or_404(Consultor, pk=pk)
    if request.method == "POST":
        form = ConsultorForm(request.POST, instance=consultor)
        if form.is_valid():
            form.save()
            messages.success(request, "Consultor atualizado com sucesso.")
            return redirect("consultores:listar")
    else:
        form = ConsultorForm(instance=consultor)
    return render(request, "consultores/form.html", {
        "form": form,
        "form_title": "Editar Consultor",
        "cancel_url": "consultores:listar",
        "submit_label": "Salvar Alterações",
    })


@gestor_required
def excluir(request, pk):
    consultor = get_object_or_404(Consultor, pk=pk)
    consultor.soft_delete()
    messages.success(request, "Consultor removido com sucesso.")
    return redirect("consultores:listar")


# ── Vendedores ────────────────────────────────────────────────────────────────


@gestor_required
def criar_vendedor(request):
    if request.method == "POST":
        form = VendedorForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Vendedor criado com sucesso.")
            return redirect("consultores:listar")
    else:
        form = VendedorForm()
    return render(request, "consultores/form.html", {
        "form": form,
        "form_title": "Novo Vendedor",
        "cancel_url": "consultores:listar",
        "submit_label": "Criar Vendedor",
    })


@gestor_required
def editar_vendedor(request, pk):
    vendedor = get_object_or_404(User, pk=pk, role=User.Role.COMERCIAL)
    if request.method == "POST":
        form = VendedorForm(request.POST, instance=vendedor)
        if form.is_valid():
            form.save()
            messages.success(request, "Vendedor atualizado com sucesso.")
            return redirect("consultores:listar")
    else:
        form = VendedorForm(instance=vendedor)
    return render(request, "consultores/form.html", {
        "form": form,
        "form_title": f"Editar Vendedor: {vendedor.get_full_name()}",
        "cancel_url": "consultores:listar",
        "submit_label": "Salvar Alterações",
    })


@gestor_required
def excluir_vendedor(request, pk):
    vendedor = get_object_or_404(User, pk=pk, role=User.Role.COMERCIAL)
    vendedor.is_active = False
    vendedor.save(update_fields=["is_active"])
    messages.success(request, f"Vendedor '{vendedor.get_full_name()}' desativado.")
    return redirect("consultores:listar")
