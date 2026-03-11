from collections import OrderedDict

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from apps.clientes.models import Cliente
from apps.core.decorators import consultor_required, gestor_required
from .forms import (
    ChecklistTemplateForm, ChecklistTemplateItemFormSet,
    ChecklistExecutionForm, EvidenceForm,
)
from .models import (
    ChecklistTemplate, ChecklistTemplateItem,
    ChecklistExecution, ChecklistExecutionItem, Evidence,
)


# ─── Template CRUD (Gestor) ───────────────────────────────

@gestor_required
def template_listar(request):
    templates = ChecklistTemplate.objects.prefetch_related("itens").all()

    audience = request.GET.get("audience")
    if audience:
        templates = templates.filter(target_audience=audience)

    tipo = request.GET.get("tipo")
    if tipo:
        templates = templates.filter(tipo=tipo)

    context = {
        "templates": templates,
        "audience_choices": ChecklistTemplate.TargetAudience.choices,
        "tipo_choices": ChecklistTemplate.Tipo.choices,
    }
    if request.htmx:
        return render(request, "checklists/_template_lista.html", context)
    return render(request, "checklists/template_listar.html", context)


@gestor_required
def template_criar(request):
    if request.method == "POST":
        form = ChecklistTemplateForm(request.POST)
        formset = ChecklistTemplateItemFormSet(request.POST)
        if form.is_valid() and formset.is_valid():
            template = form.save(commit=False)
            template.criado_por = request.user
            template.save()
            formset.instance = template
            formset.save()
            messages.success(request, f"Template '{template.nome}' criado.")
            return redirect("checklists:template_listar")
    else:
        form = ChecklistTemplateForm()
        formset = ChecklistTemplateItemFormSet()
    return render(request, "checklists/template_form.html", {
        "form": form,
        "formset": formset,
        "form_title": "Novo Template de Checklist",
    })


@gestor_required
def template_editar(request, pk):
    template = get_object_or_404(ChecklistTemplate, pk=pk)
    if request.method == "POST":
        form = ChecklistTemplateForm(request.POST, instance=template)
        formset = ChecklistTemplateItemFormSet(request.POST, instance=template)
        if form.is_valid() and formset.is_valid():
            form.save()
            formset.save()
            messages.success(request, f"Template '{template.nome}' atualizado.")
            return redirect("checklists:template_listar")
    else:
        form = ChecklistTemplateForm(instance=template)
        formset = ChecklistTemplateItemFormSet(instance=template)
    return render(request, "checklists/template_form.html", {
        "form": form,
        "formset": formset,
        "form_title": f"Editar: {template.nome}",
    })


@gestor_required
def template_excluir(request, pk):
    template = get_object_or_404(ChecklistTemplate, pk=pk)
    if request.method == "POST":
        template.soft_delete()
        messages.success(request, f"Template '{template.nome}' removido.")
        return redirect("checklists:template_listar")
    return render(request, "components/_confirm_delete.html", {
        "object": template,
        "cancel_url": "/checklists/templates/",
    })


# ─── Execuções ────────────────────────────────────────────

@login_required
def listar(request, cliente_pk):
    cliente = get_object_or_404(Cliente, pk=cliente_pk)

    # Permissão: consultor só vê seus clientes, seller só o próprio
    if request.user.is_seller:
        if not hasattr(request.user, "cliente_perfil") or request.user.cliente_perfil.pk != cliente_pk:
            return HttpResponseForbidden("Acesso negado.")
    elif request.user.is_consultor and cliente.consultor != request.user:
        return HttpResponseForbidden("Acesso negado.")

    checklists = ChecklistExecution.objects.filter(
        cliente=cliente
    ).select_related("template", "executor")

    status_filter = request.GET.get("status")
    if status_filter:
        checklists = checklists.filter(status=status_filter)

    return render(request, "checklists/listar.html", {
        "cliente": cliente,
        "checklists": checklists,
        "status_choices": ChecklistExecution.Status.choices,
    })


@consultor_required
def criar(request, cliente_pk):
    cliente = get_object_or_404(Cliente, pk=cliente_pk)

    if request.method == "POST":
        template_id = request.POST.get("template")
        template = get_object_or_404(ChecklistTemplate, pk=template_id)

        # Step 2: confirmar com dados da tarefa (para checklists do cliente)
        step = request.POST.get("step", "select")
        if step == "select" and template.target_audience == ChecklistTemplate.TargetAudience.CLIENT:
            # Mostrar formulário de tarefa antes de criar
            return render(request, "checklists/criar_confirmar.html", {
                "cliente": cliente,
                "template": template,
            })

        # Criar execução
        execucao = ChecklistExecution.objects.create(
            template=template,
            cliente=cliente,
            executor=request.user,
        )
        for item_tpl in template.itens.select_related("category").all():
            ChecklistExecutionItem.objects.create(
                execution=execucao,
                template_item=item_tpl,
            )

        # Se for checklist do cliente, criar tarefa vinculada
        if template.target_audience == ChecklistTemplate.TargetAudience.CLIENT:
            from apps.tarefas.models import Tarefa
            descricao = request.POST.get(
                "tarefa_descricao",
                f"Preencher checklist: {template.nome}",
            )
            prioridade = request.POST.get("tarefa_prioridade", "media")
            prazo = request.POST.get("tarefa_prazo") or None
            Tarefa.objects.create(
                cliente=cliente,
                criado_por=request.user,
                responsavel=request.user,
                descricao=descricao,
                prioridade=prioridade,
                prazo=prazo,
                checklist_execution=execucao,
            )
            messages.success(request, f"Checklist '{template.nome}' atribuído ao cliente com tarefa criada.")
        else:
            messages.success(request, "Checklist criado com sucesso.")

        return redirect("checklists:detalhe", pk=execucao.pk)

    # Listar templates disponíveis
    templates = ChecklistTemplate.objects.prefetch_related("itens").all()
    return render(request, "checklists/criar.html", {
        "cliente": cliente,
        "templates": templates,
    })


@login_required
def detalhe(request, pk):
    checklist = get_object_or_404(
        ChecklistExecution.objects.select_related("template", "cliente", "executor"),
        pk=pk,
    )
    itens = checklist.itens.select_related(
        "template_item", "template_item__category"
    ).prefetch_related("evidencias").all()

    # Agrupar por categoria
    categorias = OrderedDict()
    for item in itens:
        cat_nome = item.template_item.category.nome if item.template_item.category else "Sem Categoria"
        if cat_nome not in categorias:
            categorias[cat_nome] = []
        categorias[cat_nome].append(item)

    return render(request, "checklists/detalhe.html", {
        "checklist": checklist,
        "categorias": categorias,
    })


@login_required
def executar(request, pk):
    """Execução do checklist por categoria (1 categoria por vez)."""
    checklist = get_object_or_404(
        ChecklistExecution.objects.select_related("template", "cliente"),
        pk=pk,
    )

    # Marcar como in_progress se estiver pending
    if checklist.status == ChecklistExecution.Status.PENDING:
        checklist.status = ChecklistExecution.Status.IN_PROGRESS
        checklist.started_at = timezone.now()
        checklist.save(update_fields=["status", "started_at", "updated_at"])

    itens = checklist.itens.select_related(
        "template_item", "template_item__category"
    ).prefetch_related("evidencias").all()

    # Agrupar por categoria
    categorias = OrderedDict()
    for item in itens:
        cat_nome = item.template_item.category.nome if item.template_item.category else "Sem Categoria"
        if cat_nome not in categorias:
            categorias[cat_nome] = {"itens": [], "completos": 0, "total": 0}
        categorias[cat_nome]["itens"].append(item)
        categorias[cat_nome]["total"] += 1
        if item.status != ChecklistExecutionItem.Status.PENDING:
            categorias[cat_nome]["completos"] += 1

    # Determinar categoria ativa
    cat_param = request.GET.get("cat")
    cat_names = list(categorias.keys())
    if cat_param and cat_param in categorias:
        cat_ativa = cat_param
    else:
        # Primeira categoria incompleta
        cat_ativa = cat_names[0] if cat_names else None
        for nome, dados in categorias.items():
            if dados["completos"] < dados["total"]:
                cat_ativa = nome
                break

    return render(request, "checklists/executar.html", {
        "checklist": checklist,
        "categorias": categorias,
        "cat_names": cat_names,
        "cat_ativa": cat_ativa,
        "evidence_form": EvidenceForm(),
    })


@login_required
def salvar_categoria(request, pk):
    """Salvar respostas de uma categoria inteira via POST."""
    checklist = get_object_or_404(ChecklistExecution, pk=pk)
    if request.method == "POST":
        for key, value in request.POST.items():
            if key.startswith("item_"):
                item_id = key.replace("item_", "")
                try:
                    item = ChecklistExecutionItem.objects.get(pk=item_id, execution=checklist)
                    item.status = value
                    item.completed_at = timezone.now()
                    item.completed_by = request.user
                    # Salvar nota se existir
                    note_key = f"note_{item_id}"
                    if note_key in request.POST:
                        item.note = request.POST[note_key]
                    item.save()
                except ChecklistExecutionItem.DoesNotExist:
                    pass

        # Ir para próxima categoria ou resultado
        next_cat = request.POST.get("next_cat")
        if next_cat:
            return redirect(f"/checklists/{pk}/executar/?cat={next_cat}")

        messages.success(request, "Categoria salva com sucesso.")
    return redirect("checklists:executar", pk=pk)


@login_required
def completar(request, pk):
    """Finalizar checklist e calcular score."""
    checklist = get_object_or_404(ChecklistExecution, pk=pk)
    if request.method == "POST":
        checklist.calcular_score()
        checklist.status = ChecklistExecution.Status.COMPLETED
        checklist.completed_at = timezone.now()
        checklist.save()
        messages.success(request, f"Checklist finalizado! Score: {checklist.score}%")
        return redirect("checklists:detalhe", pk=pk)
    return redirect("checklists:executar", pk=pk)


@login_required
def toggle_item(request, pk, item_pk):
    item = get_object_or_404(ChecklistExecutionItem, pk=item_pk, execution_id=pk)
    if item.status == ChecklistExecutionItem.Status.PENDING:
        item.status = ChecklistExecutionItem.Status.CONFORMING
        item.completed_at = timezone.now()
        item.completed_by = request.user
    elif item.status == ChecklistExecutionItem.Status.CONFORMING:
        item.status = ChecklistExecutionItem.Status.NON_CONFORMING
        item.completed_at = timezone.now()
        item.completed_by = request.user
    else:
        item.status = ChecklistExecutionItem.Status.PENDING
        item.completed_at = None
        item.completed_by = None
    item.save()
    if request.htmx:
        return render(request, "checklists/_item_exec.html", {
            "item": item,
            "checklist": item.execution,
        })
    return redirect("checklists:executar", pk=pk)


@login_required
def upload_evidencia(request, pk, item_pk):
    item = get_object_or_404(ChecklistExecutionItem, pk=item_pk, execution_id=pk)
    if request.method == "POST":
        form = EvidenceForm(request.POST, request.FILES)
        if form.is_valid():
            evidence = form.save(commit=False)
            evidence.execution_item = item
            evidence.uploaded_by = request.user
            evidence.save()
            if request.htmx:
                return render(request, "checklists/_evidencias.html", {
                    "item": item,
                    "evidencias": item.evidencias.all(),
                })
            messages.success(request, "Evidência enviada.")
    return redirect("checklists:executar", pk=pk)
