import json

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from apps.core.decorators import consultor_required, gestor_required
from .forms import TarefaForm, TipoTarefaForm
from .models import Tarefa, TipoTarefa


def _get_tarefas_qs(user):
    if user.is_gestor:
        return Tarefa.objects.select_related("cliente", "responsavel", "tipo").all()
    elif user.is_consultor:
        return Tarefa.objects.filter(responsavel=user).select_related("cliente", "tipo")
    else:
        return Tarefa.objects.filter(cliente__usuario=user).select_related("cliente", "tipo")


@login_required
def listar(request):
    tarefas = _get_tarefas_qs(request.user)

    status_filter = request.GET.get("status")
    if status_filter:
        tarefas = tarefas.filter(status=status_filter)

    prioridade_filter = request.GET.get("prioridade")
    if prioridade_filter:
        tarefas = tarefas.filter(prioridade=prioridade_filter)

    tipo_filter = request.GET.get("tipo")
    if tipo_filter:
        tarefas = tarefas.filter(tipo_id=tipo_filter)

    cliente_filter = request.GET.get("cliente")
    if cliente_filter:
        tarefas = tarefas.filter(cliente_id=cliente_filter)

    from apps.clientes.models import Cliente
    if request.user.is_gestor:
        clientes = Cliente.objects.all()
    elif request.user.is_consultor:
        clientes = Cliente.objects.filter(consultor=request.user)
    else:
        clientes = Cliente.objects.none()

    context = {
        "tarefas": tarefas,
        "status_choices": Tarefa.Status.choices,
        "prioridade_choices": Tarefa.Prioridade.choices,
        "tipos": TipoTarefa.objects.all(),
        "clientes": clientes,
    }
    if request.htmx:
        return render(request, "tarefas/_tabela.html", context)
    return render(request, "tarefas/listar.html", context)


@login_required
def kanban(request):
    tarefas = _get_tarefas_qs(request.user)

    tipo_filter = request.GET.get("tipo")
    if tipo_filter:
        tarefas = tarefas.filter(tipo_id=tipo_filter)

    cliente_filter = request.GET.get("cliente")
    if cliente_filter:
        tarefas = tarefas.filter(cliente_id=cliente_filter)

    colunas = []
    for status_value, status_label in Tarefa.Status.choices:
        cards = [t for t in tarefas if t.status == status_value]
        colunas.append({
            "status": status_value,
            "label": status_label,
            "tarefas": cards,
        })

    from apps.clientes.models import Cliente
    if request.user.is_gestor:
        clientes = Cliente.objects.all()
    elif request.user.is_consultor:
        clientes = Cliente.objects.filter(consultor=request.user)
    else:
        clientes = Cliente.objects.none()

    return render(request, "tarefas/kanban.html", {
        "colunas": colunas,
        "tipos": TipoTarefa.objects.all(),
        "clientes": clientes,
    })


@login_required
@require_POST
def kanban_mover(request):
    try:
        data = json.loads(request.body)
        tarefa_id = data.get("tarefa_id")
        novo_status = data.get("status")
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({"error": "Dados invalidos"}, status=400)

    tarefa = get_object_or_404(Tarefa, pk=tarefa_id)

    if novo_status in dict(Tarefa.Status.choices):
        tarefa.status = novo_status
        if novo_status == "concluido":
            tarefa.concluido_em = timezone.now()
        tarefa.save(update_fields=["status", "concluido_em"])

    return JsonResponse({"ok": True})


@consultor_required
def criar(request):
    if request.method == "POST":
        form = TarefaForm(request.POST)
        if form.is_valid():
            tarefa = form.save(commit=False)
            tarefa.criado_por = request.user
            tarefa.save()
            messages.success(request, "Tarefa criada com sucesso.")
            return redirect("tarefas:listar")
    else:
        form = TarefaForm()
        if not request.user.is_gestor:
            form.fields["responsavel"].initial = request.user
    return render(request, "tarefas/form.html", {
        "form": form,
        "form_title": "Nova Tarefa",
        "cancel_url": "/tarefas/",
    })


@consultor_required
def editar(request, pk):
    tarefa = get_object_or_404(Tarefa, pk=pk)
    if request.method == "POST":
        form = TarefaForm(request.POST, instance=tarefa)
        if form.is_valid():
            form.save()
            messages.success(request, "Tarefa atualizada.")
            return redirect("tarefas:listar")
    else:
        form = TarefaForm(instance=tarefa)
    return render(request, "tarefas/form.html", {
        "form": form,
        "form_title": "Editar Tarefa",
        "cancel_url": "/tarefas/",
    })


@login_required
def alterar_status(request, pk):
    tarefa = get_object_or_404(Tarefa, pk=pk)
    novo_status = request.POST.get("status")
    if novo_status in dict(Tarefa.Status.choices):
        tarefa.status = novo_status
        if novo_status == "concluido":
            tarefa.concluido_em = timezone.now()
        tarefa.save()
        if request.htmx:
            return render(request, "tarefas/_linha.html", {"tarefa": tarefa})
    return redirect("tarefas:listar")


@consultor_required
def excluir(request, pk):
    tarefa = get_object_or_404(Tarefa, pk=pk)
    if request.method == "POST":
        tarefa.soft_delete()
        messages.success(request, "Tarefa removida.")
        return redirect("tarefas:listar")
    return render(request, "components/_confirm_delete.html", {
        "object": tarefa,
        "cancel_url": "/tarefas/",
    })


# ── Tipo Tarefa Config ──────────────────────────────────────


@gestor_required
def tipo_config(request):
    tipos = TipoTarefa.objects.all()
    if request.method == "POST":
        form = TipoTarefaForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Tipo criado.")
            return redirect("tarefas:tipo_config")
    else:
        form = TipoTarefaForm()
    return render(request, "tarefas/tipo_config.html", {"tipos": tipos, "form": form})


@gestor_required
def tipo_config_editar(request, pk):
    tipo = get_object_or_404(TipoTarefa, pk=pk)
    if request.method == "POST":
        form = TipoTarefaForm(request.POST, instance=tipo)
        if form.is_valid():
            form.save()
            messages.success(request, "Tipo atualizado.")
            return redirect("tarefas:tipo_config")
    else:
        form = TipoTarefaForm(instance=tipo)
    return render(request, "tarefas/tipo_config_form.html", {"form": form, "tipo": tipo})


@gestor_required
@require_POST
def tipo_config_excluir(request, pk):
    tipo = get_object_or_404(TipoTarefa, pk=pk)
    tipo.delete()
    messages.success(request, f"Tipo '{tipo.nome}' removido.")
    return redirect("tarefas:tipo_config")
