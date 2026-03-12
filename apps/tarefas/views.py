import json

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from apps.core.decorators import gestor_required

from .forms import (
    ComentarioForm,
    EtapaTarefaForm,
    EtiquetaTarefaForm,
    SubTarefaForm,
    TarefaForm,
    TipoTarefaForm,
)
from .models import (
    AtividadeTarefa,
    EtapaTarefa,
    EtiquetaTarefa,
    SubTarefa,
    Tarefa,
    TipoTarefa,
)


def _get_tarefas_qs(user):
    qs = Tarefa.objects.select_related(
        "cliente", "responsavel", "tipo", "etapa", "criado_por"
    ).prefetch_related("etiquetas", "subtarefas")
    if user.is_gestor:
        return qs.all()
    return qs.filter(Q(responsavel=user) | Q(criado_por=user)).distinct()


# ── Lista ────────────────────────────────────────────────────


@login_required
def listar(request):
    tarefas = _get_tarefas_qs(request.user)

    # Filtros
    etapa_filter = request.GET.get("etapa")
    if etapa_filter:
        tarefas = tarefas.filter(etapa_id=etapa_filter)

    prioridade_filter = request.GET.get("prioridade")
    if prioridade_filter:
        tarefas = tarefas.filter(prioridade=prioridade_filter)

    tipo_filter = request.GET.get("tipo")
    if tipo_filter:
        tarefas = tarefas.filter(tipo_id=tipo_filter)

    cliente_filter = request.GET.get("cliente")
    if cliente_filter:
        tarefas = tarefas.filter(cliente_id=cliente_filter)

    etiqueta_filter = request.GET.get("etiqueta")
    if etiqueta_filter:
        tarefas = tarefas.filter(etiquetas__id=etiqueta_filter).distinct()

    busca = request.GET.get("busca", "").strip()
    if busca:
        tarefas = tarefas.filter(
            Q(titulo__icontains=busca) | Q(descricao__icontains=busca)
        )

    from apps.clientes.models import Cliente

    if request.user.is_gestor:
        clientes = Cliente.objects.all()
    elif hasattr(request.user, "is_consultor") and request.user.is_consultor:
        clientes = Cliente.objects.filter(consultor=request.user)
    else:
        clientes = Cliente.objects.none()

    context = {
        "tarefas": tarefas,
        "etapas": EtapaTarefa.objects.all(),
        "prioridade_choices": Tarefa.Prioridade.choices,
        "tipos": TipoTarefa.objects.all(),
        "clientes": clientes,
        "etiquetas": EtiquetaTarefa.objects.all(),
    }
    if request.htmx:
        return render(request, "tarefas/_tabela.html", context)
    return render(request, "tarefas/listar.html", context)


# ── Kanban ───────────────────────────────────────────────────


@login_required
def kanban(request):
    tarefas = _get_tarefas_qs(request.user)

    tipo_filter = request.GET.get("tipo")
    if tipo_filter:
        tarefas = tarefas.filter(tipo_id=tipo_filter)

    cliente_filter = request.GET.get("cliente")
    if cliente_filter:
        tarefas = tarefas.filter(cliente_id=cliente_filter)

    prioridade_filter = request.GET.get("prioridade")
    if prioridade_filter:
        tarefas = tarefas.filter(prioridade=prioridade_filter)

    etiqueta_filter = request.GET.get("etiqueta")
    if etiqueta_filter:
        tarefas = tarefas.filter(etiquetas__id=etiqueta_filter).distinct()

    etapas = EtapaTarefa.objects.all()
    colunas = []
    for etapa in etapas:
        cards = [t for t in tarefas if t.etapa_id == etapa.pk]
        cards.sort(key=lambda t: t.ordem_kanban)
        colunas.append(
            {
                "etapa": etapa,
                "tarefas": cards,
            }
        )

    from apps.clientes.models import Cliente

    if request.user.is_gestor:
        clientes = Cliente.objects.all()
    elif hasattr(request.user, "is_consultor") and request.user.is_consultor:
        clientes = Cliente.objects.filter(consultor=request.user)
    else:
        clientes = Cliente.objects.none()

    return render(
        request,
        "tarefas/kanban.html",
        {
            "colunas": colunas,
            "tipos": TipoTarefa.objects.all(),
            "clientes": clientes,
            "etiquetas": EtiquetaTarefa.objects.all(),
            "prioridade_choices": Tarefa.Prioridade.choices,
            "hoje": timezone.now().date(),
        },
    )


@login_required
@require_POST
def kanban_mover(request):
    try:
        data = json.loads(request.body)
        tarefa_id = data.get("tarefa_id")
        etapa_id = data.get("etapa_id")
        ordem = data.get("ordem", 0)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({"error": "Dados invalidos"}, status=400)

    tarefa = get_object_or_404(Tarefa, pk=tarefa_id)
    old_etapa = tarefa.etapa

    etapa = get_object_or_404(EtapaTarefa, pk=etapa_id)
    tarefa.etapa = etapa
    tarefa.ordem_kanban = ordem
    tarefa.save()

    # Log activity if etapa changed
    if old_etapa != etapa:
        old_nome = old_etapa.nome if old_etapa else "Sem etapa"
        AtividadeTarefa.objects.create(
            tarefa=tarefa,
            autor=request.user,
            tipo="mudanca_etapa",
            descricao=f"Moveu de '{old_nome}' para '{etapa.nome}'",
        )

    return JsonResponse({"ok": True})


# ── CRUD ─────────────────────────────────────────────────────


@login_required
def criar(request):
    if request.method == "POST":
        form = TarefaForm(request.POST)
        if form.is_valid():
            tarefa = form.save(commit=False)
            tarefa.criado_por = request.user
            if not tarefa.etapa_id:
                tarefa.etapa = EtapaTarefa.objects.filter(is_concluido=False).first()
            tarefa.save()
            form.save_m2m()
            AtividadeTarefa.objects.create(
                tarefa=tarefa,
                autor=request.user,
                tipo="criacao",
                descricao="Criou a tarefa",
            )
            messages.success(request, "Tarefa criada com sucesso.")
            return redirect("tarefas:kanban")
    else:
        form = TarefaForm()
        if not request.user.is_gestor:
            form.fields["responsavel"].initial = request.user
        form.fields["etapa"].initial = EtapaTarefa.objects.filter(
            is_concluido=False
        ).first()
    return render(
        request,
        "tarefas/form.html",
        {"form": form, "form_title": "Nova Tarefa", "cancel_url": "/tarefas/kanban/"},
    )


@login_required
def editar(request, pk):
    tarefa = get_object_or_404(Tarefa, pk=pk)
    if request.method == "POST":
        form = TarefaForm(request.POST, instance=tarefa)
        if form.is_valid():
            form.save()
            AtividadeTarefa.objects.create(
                tarefa=tarefa,
                autor=request.user,
                tipo="edicao",
                descricao="Editou a tarefa",
            )
            messages.success(request, "Tarefa atualizada.")
            return redirect("tarefas:detalhe", pk=tarefa.pk)
    else:
        form = TarefaForm(instance=tarefa)
    return render(
        request,
        "tarefas/form.html",
        {
            "form": form,
            "form_title": "Editar Tarefa",
            "cancel_url": f"/tarefas/{tarefa.pk}/",
        },
    )


@login_required
def detalhe(request, pk):
    tarefa = get_object_or_404(
        Tarefa.objects.select_related(
            "cliente", "responsavel", "tipo", "etapa", "criado_por"
        ).prefetch_related("etiquetas", "subtarefas", "comentarios__autor", "atividades__autor"),
        pk=pk,
    )
    comentario_form = ComentarioForm()
    subtarefa_form = SubTarefaForm()
    return render(
        request,
        "tarefas/detalhe.html",
        {
            "tarefa": tarefa,
            "comentario_form": comentario_form,
            "subtarefa_form": subtarefa_form,
            "etapas": EtapaTarefa.objects.all(),
            "hoje": timezone.now().date(),
        },
    )


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


@login_required
def excluir(request, pk):
    tarefa = get_object_or_404(Tarefa, pk=pk)
    if request.method == "POST":
        tarefa.soft_delete()
        messages.success(request, "Tarefa removida.")
        return redirect("tarefas:kanban")
    return render(
        request,
        "components/_confirm_delete.html",
        {"object": tarefa, "cancel_url": f"/tarefas/{tarefa.pk}/"},
    )


# ── Subtarefas ───────────────────────────────────────────────


@login_required
@require_POST
def adicionar_subtarefa(request, pk):
    tarefa = get_object_or_404(Tarefa, pk=pk)
    form = SubTarefaForm(request.POST)
    if form.is_valid():
        sub = form.save(commit=False)
        sub.tarefa = tarefa
        sub.ordem = tarefa.subtarefas.count()
        sub.save()
        AtividadeTarefa.objects.create(
            tarefa=tarefa,
            autor=request.user,
            tipo="subtarefa",
            descricao=f"Adicionou subtarefa: {sub.titulo}",
        )
    if request.htmx:
        tarefa.refresh_from_db()
        return render(
            request,
            "tarefas/_subtarefas.html",
            {"tarefa": tarefa, "subtarefa_form": SubTarefaForm()},
        )
    return redirect("tarefas:detalhe", pk=tarefa.pk)


@login_required
@require_POST
def toggle_subtarefa(request, pk):
    sub = get_object_or_404(SubTarefa, pk=pk)
    sub.concluida = not sub.concluida
    sub.save(update_fields=["concluida"])
    tarefa = sub.tarefa
    AtividadeTarefa.objects.create(
        tarefa=tarefa,
        autor=request.user,
        tipo="subtarefa",
        descricao=f"{'Concluiu' if sub.concluida else 'Reabriu'} subtarefa: {sub.titulo}",
    )
    if request.htmx:
        return render(
            request,
            "tarefas/_subtarefas.html",
            {"tarefa": tarefa, "subtarefa_form": SubTarefaForm()},
        )
    return redirect("tarefas:detalhe", pk=tarefa.pk)


@login_required
@require_POST
def excluir_subtarefa(request, pk):
    sub = get_object_or_404(SubTarefa, pk=pk)
    tarefa = sub.tarefa
    AtividadeTarefa.objects.create(
        tarefa=tarefa,
        autor=request.user,
        tipo="subtarefa",
        descricao=f"Removeu subtarefa: {sub.titulo}",
    )
    sub.delete()
    if request.htmx:
        return render(
            request,
            "tarefas/_subtarefas.html",
            {"tarefa": tarefa, "subtarefa_form": SubTarefaForm()},
        )
    return redirect("tarefas:detalhe", pk=tarefa.pk)


# ── Comentarios ──────────────────────────────────────────────


@login_required
@require_POST
def adicionar_comentario(request, pk):
    tarefa = get_object_or_404(Tarefa, pk=pk)
    form = ComentarioForm(request.POST)
    if form.is_valid():
        comentario = form.save(commit=False)
        comentario.tarefa = tarefa
        comentario.autor = request.user
        comentario.save()
        AtividadeTarefa.objects.create(
            tarefa=tarefa,
            autor=request.user,
            tipo="comentario",
            descricao="Adicionou um comentário",
        )
    if request.htmx:
        tarefa.refresh_from_db()
        return render(
            request,
            "tarefas/_comentarios.html",
            {"tarefa": tarefa, "comentario_form": ComentarioForm()},
        )
    return redirect("tarefas:detalhe", pk=tarefa.pk)


# ── Config Etapas ────────────────────────────────────────────


@gestor_required
def etapa_config(request):
    etapas = EtapaTarefa.objects.all()
    if request.method == "POST":
        form = EtapaTarefaForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Etapa criada.")
            return redirect("tarefas:etapa_config")
    else:
        form = EtapaTarefaForm()
    return render(
        request, "tarefas/etapa_config.html", {"etapas": etapas, "form": form}
    )


@gestor_required
def etapa_config_editar(request, pk):
    etapa = get_object_or_404(EtapaTarefa, pk=pk)
    if request.method == "POST":
        form = EtapaTarefaForm(request.POST, instance=etapa)
        if form.is_valid():
            form.save()
            messages.success(request, "Etapa atualizada.")
            return redirect("tarefas:etapa_config")
    else:
        form = EtapaTarefaForm(instance=etapa)
    return render(
        request,
        "tarefas/etapa_config_form.html",
        {"form": form, "etapa": etapa},
    )


@gestor_required
@require_POST
def etapa_config_excluir(request, pk):
    etapa = get_object_or_404(EtapaTarefa, pk=pk)
    etapa.delete()
    messages.success(request, f"Etapa '{etapa.nome}' removida.")
    return redirect("tarefas:etapa_config")


# ── Config Etiquetas ─────────────────────────────────────────


@gestor_required
def etiqueta_config(request):
    etiquetas = EtiquetaTarefa.objects.all()
    if request.method == "POST":
        form = EtiquetaTarefaForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Etiqueta criada.")
            return redirect("tarefas:etiqueta_config")
    else:
        form = EtiquetaTarefaForm()
    return render(
        request,
        "tarefas/etiqueta_config.html",
        {"etiquetas": etiquetas, "form": form},
    )


# ── Config Tipo Tarefa ───────────────────────────────────────


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
    return render(
        request, "tarefas/tipo_config_form.html", {"form": form, "tipo": tipo}
    )


@gestor_required
@require_POST
def tipo_config_excluir(request, pk):
    tipo = get_object_or_404(TipoTarefa, pk=pk)
    tipo.delete()
    messages.success(request, f"Tipo '{tipo.nome}' removido.")
    return redirect("tarefas:tipo_config")
