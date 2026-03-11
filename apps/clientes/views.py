import json

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from apps.core.decorators import consultor_required, gestor_required
from .forms import ClienteForm, EtapaPipelineForm
from .models import Cliente, Atividade, EtapaPipeline


@consultor_required
def listar(request):
    if request.user.is_gestor:
        clientes = Cliente.objects.select_related("consultor").all()
    else:
        clientes = Cliente.objects.filter(consultor=request.user)

    status_filter = request.GET.get("status")
    if status_filter:
        clientes = clientes.filter(status=status_filter)

    busca = request.GET.get("busca")
    if busca:
        clientes = clientes.filter(empresa__icontains=busca)

    context = {
        "clientes": clientes,
        "status_choices": Cliente.Status.choices,
    }
    if request.htmx:
        return render(request, "clientes/_tabela.html", context)
    return render(request, "clientes/listar.html", context)


@login_required
def detalhe(request, pk):
    cliente = get_object_or_404(Cliente, pk=pk)
    if request.user.is_seller:
        if not hasattr(request.user, "cliente_perfil") or request.user.cliente_perfil.pk != pk:
            return HttpResponseForbidden("Acesso negado.")
    elif request.user.is_consultor and cliente.consultor != request.user:
        return HttpResponseForbidden("Acesso negado.")

    diagnosticos = cliente.diagnosticos.select_related("template").all()[:5]
    checklists = cliente.checklists.select_related("template", "executor").all()[:10]
    tarefas = cliente.tarefas.filter(is_active=True)[:10]
    reunioes = cliente.reunioes.all()[:5]
    atividades = cliente.atividades.all()[:10]
    planos_count = cliente.planos.count()
    checklists_count = cliente.checklists.count()
    treinamentos_realizados = cliente.treinamentos_realizados.select_related(
        "treinamento"
    ).all()

    # Anúncios
    from apps.anuncios.models import UploadCurvaABC, UploadMetricas, AnuncioAtualizar
    uploads_abc = UploadCurvaABC.objects.filter(cliente=cliente)[:5]
    uploads_metricas = UploadMetricas.objects.filter(cliente=cliente)[:5]
    anuncios_qs = AnuncioAtualizar.objects.filter(cliente=cliente)
    from django.db.models import Q
    anuncios_atualizar_total = anuncios_qs.count()
    anuncios_atualizar_pendentes = anuncios_qs.filter(
        Q(precisa_foto=True, foto_feito=False) | Q(precisa_video=True, video_feito=False)
    ).count()
    anuncios_atualizar_lista = anuncios_qs[:10]

    # SWOT
    from apps.swot.models import AnaliseSwot
    analises_swot = AnaliseSwot.objects.filter(
        cliente=cliente, is_active=True
    ).select_related("consultor")[:5]

    # Jornada ativa
    from apps.jornadas.models import JornadaCliente
    jornada_ativa = JornadaCliente.objects.filter(
        cliente=cliente, status="ativa"
    ).first()

    return render(request, "clientes/detalhe.html", {
        "cliente": cliente,
        "diagnosticos": diagnosticos,
        "checklists": checklists,
        "checklists_count": checklists_count,
        "planos_count": planos_count,
        "tarefas": tarefas,
        "reunioes": reunioes,
        "atividades": atividades,
        "treinamentos_realizados": treinamentos_realizados,
        "uploads_abc": uploads_abc,
        "uploads_metricas": uploads_metricas,
        "anuncios_atualizar_total": anuncios_atualizar_total,
        "anuncios_atualizar_pendentes": anuncios_atualizar_pendentes,
        "anuncios_atualizar_lista": anuncios_atualizar_lista,
        "analises_swot": analises_swot,
        "jornada_ativa": jornada_ativa,
    })


@gestor_required
def criar(request):
    if request.method == "POST":
        form = ClienteForm(request.POST)
        if form.is_valid():
            cliente = form.save()
            Atividade.objects.create(
                cliente=cliente,
                descricao=f"Cliente cadastrado no sistema",
                autor=request.user,
            )
            messages.success(request, f"Cliente {cliente.empresa} criado com sucesso.")
            return redirect("clientes:detalhe", pk=cliente.pk)
    else:
        form = ClienteForm()
    return render(request, "clientes/form.html", {
        "form": form,
        "form_title": "Novo Cliente",
        "cancel_url": "/clientes/",
    })


@gestor_required
def editar(request, pk):
    cliente = get_object_or_404(Cliente, pk=pk)
    if request.method == "POST":
        form = ClienteForm(request.POST, instance=cliente)
        if form.is_valid():
            form.save()
            messages.success(request, f"Cliente {cliente.empresa} atualizado.")
            return redirect("clientes:detalhe", pk=cliente.pk)
    else:
        form = ClienteForm(instance=cliente)
    return render(request, "clientes/form.html", {
        "form": form,
        "form_title": f"Editar: {cliente.empresa}",
        "cancel_url": f"/clientes/{cliente.pk}/",
        "cliente": cliente,
    })


@gestor_required
def excluir(request, pk):
    cliente = get_object_or_404(Cliente, pk=pk)
    if request.method == "POST":
        empresa = cliente.empresa
        cliente.soft_delete()
        messages.success(request, f"Cliente {empresa} removido.")
        return redirect("clientes:listar")
    return render(request, "components/_confirm_delete.html", {
        "object": cliente,
        "cancel_url": f"/clientes/{cliente.pk}/",
    })


# ── Pipeline Kanban ──────────────────────────────────────────


@consultor_required
def pipeline(request):
    etapas = EtapaPipeline.objects.prefetch_related("clientes__consultor").all()

    if request.user.is_gestor:
        clientes_qs = Cliente.objects.select_related("consultor", "etapa").all()
    else:
        clientes_qs = Cliente.objects.filter(consultor=request.user).select_related("etapa")

    # Agrupar por etapa
    colunas = []
    for etapa in etapas:
        cards = [c for c in clientes_qs if c.etapa_id == etapa.pk]
        colunas.append({"etapa": etapa, "clientes": cards})

    # Clientes sem etapa
    sem_etapa = [c for c in clientes_qs if c.etapa_id is None]
    if sem_etapa:
        colunas.insert(0, {
            "etapa": None,
            "clientes": sem_etapa,
        })

    return render(request, "clientes/pipeline.html", {"colunas": colunas})


@consultor_required
@require_POST
def pipeline_mover(request):
    try:
        data = json.loads(request.body)
        cliente_id = data.get("cliente_id")
        etapa_id = data.get("etapa_id")
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({"error": "Dados invalidos"}, status=400)

    cliente = get_object_or_404(Cliente, pk=cliente_id)

    if etapa_id:
        etapa = get_object_or_404(EtapaPipeline, pk=etapa_id)
        cliente.etapa = etapa
    else:
        cliente.etapa = None
    cliente.save(update_fields=["etapa"])

    Atividade.objects.create(
        cliente=cliente,
        descricao=f"Movido para etapa: {cliente.etapa or 'Sem etapa'}",
        autor=request.user,
    )

    return JsonResponse({"ok": True})


@gestor_required
def pipeline_config(request):
    etapas = EtapaPipeline.objects.all()

    if request.method == "POST":
        form = EtapaPipelineForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Etapa criada.")
            return redirect("clientes:pipeline_config")
    else:
        form = EtapaPipelineForm()

    return render(request, "clientes/pipeline_config.html", {
        "etapas": etapas,
        "form": form,
    })


@gestor_required
def pipeline_config_editar(request, pk):
    etapa = get_object_or_404(EtapaPipeline, pk=pk)
    if request.method == "POST":
        form = EtapaPipelineForm(request.POST, instance=etapa)
        if form.is_valid():
            form.save()
            messages.success(request, "Etapa atualizada.")
            return redirect("clientes:pipeline_config")
    else:
        form = EtapaPipelineForm(instance=etapa)
    return render(request, "clientes/pipeline_config_form.html", {
        "form": form,
        "etapa": etapa,
    })


@gestor_required
@require_POST
def pipeline_config_excluir(request, pk):
    etapa = get_object_or_404(EtapaPipeline, pk=pk)
    etapa.delete()
    messages.success(request, f"Etapa '{etapa.nome}' removida.")
    return redirect("clientes:pipeline_config")
