import json
from datetime import date

from django.contrib import messages
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from apps.core.decorators import comercial_required, gestor_required
from apps.agenda.models import Agendamento
from apps.clientes.models import Cliente
from apps.propostas.models import Proposta

from .forms import (
    LeadForm, OportunidadeForm, EtapaCRMForm,
    AtividadeForm, LembreteForm, ConversaoForm,
)
from .models import Lead, Oportunidade, EtapaCRM, AtividadeCRM, LembreteCRM


# ── Leads ────────────────────────────────────────────────────────────────────


@comercial_required
def listar_leads(request):
    leads = Lead.objects.select_related("responsavel", "cliente").all()

    if not request.user.is_gestor:
        leads = leads.filter(responsavel=request.user)

    busca = request.GET.get("q", "")
    if busca:
        leads = leads.filter(nome__icontains=busca) | leads.filter(empresa__icontains=busca)

    origem = request.GET.get("origem", "")
    if origem:
        leads = leads.filter(origem=origem)

    convertidos = request.GET.get("convertidos", "")
    if convertidos == "sim":
        leads = leads.exclude(cliente=None)
    elif convertidos == "nao":
        leads = leads.filter(cliente=None)

    return render(request, "crm/listar.html", {
        "leads": leads,
        "busca": busca,
        "origem_filtro": origem,
        "convertidos_filtro": convertidos,
        "origens": Lead.Origem.choices,
    })


@comercial_required
def criar_lead(request):
    if request.method == "POST":
        form = LeadForm(request.POST)
        if form.is_valid():
            lead = form.save(commit=False)
            lead.responsavel = request.user
            lead.save()
            messages.success(request, f"Lead '{lead.nome}' criado com sucesso.")
            return redirect("crm:detalhe_lead", pk=lead.pk)
    else:
        form = LeadForm()

    return render(request, "crm/form_lead.html", {
        "form": form,
        "form_title": "Novo Lead",
    })


@comercial_required
def detalhe_lead(request, pk):
    lead = get_object_or_404(Lead, pk=pk)
    atividades = lead.atividades_crm.select_related("autor").all()[:20]
    oportunidades = lead.oportunidades.select_related("etapa").all()
    lembretes = lead.lembretes.filter(enviado=False).all()

    atividade_form = AtividadeForm()
    lembrete_form = LembreteForm()

    return render(request, "crm/detalhe_lead.html", {
        "lead": lead,
        "atividades": atividades,
        "oportunidades": oportunidades,
        "lembretes": lembretes,
        "atividade_form": atividade_form,
        "lembrete_form": lembrete_form,
    })


@comercial_required
def editar_lead(request, pk):
    lead = get_object_or_404(Lead, pk=pk)

    if request.method == "POST":
        form = LeadForm(request.POST, instance=lead)
        if form.is_valid():
            form.save()
            messages.success(request, "Lead atualizado.")
            return redirect("crm:detalhe_lead", pk=lead.pk)
    else:
        form = LeadForm(instance=lead)

    return render(request, "crm/form_lead.html", {
        "form": form,
        "form_title": f"Editar Lead: {lead.nome}",
        "lead": lead,
    })


@comercial_required
@require_POST
def excluir_lead(request, pk):
    lead = get_object_or_404(Lead, pk=pk)
    lead.soft_delete()
    messages.success(request, f"Lead '{lead.nome}' excluído.")
    return redirect("crm:listar")


@comercial_required
@require_POST
def adicionar_atividade(request, pk):
    lead = get_object_or_404(Lead, pk=pk)
    form = AtividadeForm(request.POST)
    if form.is_valid():
        atividade = form.save(commit=False)
        atividade.lead = lead
        atividade.autor = request.user
        atividade.save()
        messages.success(request, "Atividade registrada.")
    return redirect("crm:detalhe_lead", pk=lead.pk)


@comercial_required
@require_POST
def criar_lembrete(request, pk):
    lead = get_object_or_404(Lead, pk=pk)
    form = LembreteForm(request.POST)
    if form.is_valid():
        lembrete = form.save(commit=False)
        lembrete.lead = lead
        lembrete.responsavel = request.user
        lembrete.save()
        messages.success(request, "Lembrete agendado.")
    return redirect("crm:detalhe_lead", pk=lead.pk)


# ── Conversão ────────────────────────────────────────────────────────────────


@comercial_required
def converter_lead(request, pk):
    lead = get_object_or_404(Lead, pk=pk)

    if lead.convertido:
        messages.warning(request, "Este lead já foi convertido.")
        return redirect("crm:detalhe_lead", pk=lead.pk)

    if request.method == "POST":
        form = ConversaoForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                cliente = Cliente.objects.create(
                    empresa=lead.empresa or lead.nome,
                    nicho=lead.nicho,
                    telefone=lead.telefone,
                    email=lead.email,
                    status=Cliente.Status.ONBOARDING,
                    consultor=form.cleaned_data["consultor"],
                    tipo_consultoria=form.cleaned_data["tipo_consultoria"],
                    data_inicio=form.cleaned_data["data_inicio"],
                )
                lead.cliente = cliente
                lead.save(update_fields=["cliente"])

                AtividadeCRM.objects.create(
                    lead=lead,
                    tipo=AtividadeCRM.Tipo.MUDANCA_ETAPA,
                    descricao="Lead convertido em cliente.",
                    autor=request.user,
                )

                # Mover oportunidades para etapa de ganho
                etapa_ganho = EtapaCRM.objects.filter(is_ganho=True).first()
                if etapa_ganho:
                    lead.oportunidades.update(etapa=etapa_ganho)

            messages.success(request, f"Lead convertido! Cliente '{cliente.empresa}' criado.")
            return redirect("clientes:detalhe", pk=cliente.pk)
    else:
        form = ConversaoForm(initial={"data_inicio": date.today()})

    return render(request, "crm/converter.html", {
        "lead": lead,
        "form": form,
    })


# ── Integração Agenda ────────────────────────────────────────────────────────


@comercial_required
def agendar_reuniao(request, pk):
    lead = get_object_or_404(Lead, pk=pk)

    if request.method == "POST":
        data_hora = request.POST.get("data_hora")
        duracao = request.POST.get("duracao", 60)
        observacao = request.POST.get("observacao", "")

        if data_hora:
            agendamento = Agendamento.objects.create(
                consultor=request.user,
                data_hora=data_hora,
                duracao=int(duracao),
                nome_cliente=lead.nome,
                email_cliente=lead.email or "",
                telefone_cliente=lead.telefone or "",
                observacao=f"Reunião comercial - {lead.empresa}\n{observacao}".strip(),
            )

            AtividadeCRM.objects.create(
                lead=lead,
                tipo=AtividadeCRM.Tipo.REUNIAO,
                descricao=f"Reunião agendada para {agendamento.data_hora:%d/%m/%Y %H:%M}.",
                autor=request.user,
            )

            messages.success(request, "Reunião agendada com sucesso!")
            return redirect("crm:detalhe_lead", pk=lead.pk)

    return render(request, "crm/agendar_reuniao.html", {
        "lead": lead,
    })


# ── Integração Propostas ─────────────────────────────────────────────────────


@comercial_required
@require_POST
def criar_proposta(request, pk):
    lead = get_object_or_404(Lead, pk=pk)

    proposta = Proposta.objects.create(
        lead_nome=lead.nome,
        lead_loja=lead.empresa,
        lead_email=lead.email,
        lead_telefone=lead.telefone,
        consultor=request.user,
        status="rascunho",
    )

    AtividadeCRM.objects.create(
        lead=lead,
        tipo=AtividadeCRM.Tipo.NOTA,
        descricao=f"Proposta #{proposta.pk} criada.",
        autor=request.user,
    )

    messages.success(request, "Proposta criada! Redirecionando para edição...")
    return redirect("propostas:editar", pk=proposta.pk)


# ── Oportunidades ────────────────────────────────────────────────────────────


@comercial_required
def criar_oportunidade(request, lead_pk):
    lead = get_object_or_404(Lead, pk=lead_pk)

    if request.method == "POST":
        form = OportunidadeForm(request.POST)
        if form.is_valid():
            oportunidade = form.save(commit=False)
            oportunidade.lead = lead
            oportunidade.responsavel = request.user
            if not oportunidade.etapa:
                oportunidade.etapa = EtapaCRM.objects.order_by("ordem").first()
            oportunidade.save()

            AtividadeCRM.objects.create(
                lead=lead,
                oportunidade=oportunidade,
                tipo=AtividadeCRM.Tipo.NOTA,
                descricao=f"Oportunidade '{oportunidade.titulo}' criada.",
                autor=request.user,
            )

            messages.success(request, "Oportunidade criada.")
            return redirect("crm:detalhe_lead", pk=lead.pk)
    else:
        form = OportunidadeForm(initial={
            "titulo": f"Consultoria - {lead.empresa or lead.nome}",
        })

    return render(request, "crm/form_oportunidade.html", {
        "form": form,
        "lead": lead,
        "form_title": "Nova Oportunidade",
    })


@comercial_required
def editar_oportunidade(request, pk):
    oportunidade = get_object_or_404(Oportunidade, pk=pk)

    if request.method == "POST":
        form = OportunidadeForm(request.POST, instance=oportunidade)
        if form.is_valid():
            form.save()
            messages.success(request, "Oportunidade atualizada.")
            return redirect("crm:detalhe_lead", pk=oportunidade.lead.pk)
    else:
        form = OportunidadeForm(instance=oportunidade)

    return render(request, "crm/form_oportunidade.html", {
        "form": form,
        "lead": oportunidade.lead,
        "form_title": f"Editar: {oportunidade.titulo}",
        "oportunidade": oportunidade,
    })


# ── Kanban ───────────────────────────────────────────────────────────────────


@comercial_required
def kanban(request):
    etapas = EtapaCRM.objects.all()

    if request.user.is_gestor:
        oportunidades = Oportunidade.objects.select_related(
            "lead", "etapa", "responsavel"
        ).all()
    else:
        oportunidades = Oportunidade.objects.filter(
            responsavel=request.user
        ).select_related("lead", "etapa")

    colunas = []
    for etapa in etapas:
        cards = [o for o in oportunidades if o.etapa_id == etapa.pk]
        colunas.append({"etapa": etapa, "oportunidades": cards})

    sem_etapa = [o for o in oportunidades if o.etapa_id is None]
    if sem_etapa:
        colunas.insert(0, {"etapa": None, "oportunidades": sem_etapa})

    return render(request, "crm/kanban.html", {"colunas": colunas})


@comercial_required
@require_POST
def kanban_mover(request):
    try:
        data = json.loads(request.body)
        oportunidade_id = data.get("oportunidade_id")
        etapa_id = data.get("etapa_id")
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({"error": "Dados inválidos"}, status=400)

    oportunidade = get_object_or_404(Oportunidade, pk=oportunidade_id)

    if etapa_id:
        etapa = get_object_or_404(EtapaCRM, pk=etapa_id)
        oportunidade.etapa = etapa
    else:
        oportunidade.etapa = None
    oportunidade.save(update_fields=["etapa"])

    AtividadeCRM.objects.create(
        lead=oportunidade.lead,
        oportunidade=oportunidade,
        tipo=AtividadeCRM.Tipo.MUDANCA_ETAPA,
        descricao=f"Oportunidade movida para: {oportunidade.etapa or 'Sem etapa'}",
        autor=request.user,
    )

    return JsonResponse({"ok": True})


# ── Config Etapas ────────────────────────────────────────────────────────────


@gestor_required
def config_etapas(request):
    etapas = EtapaCRM.objects.all()

    if request.method == "POST":
        form = EtapaCRMForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Etapa criada.")
            return redirect("crm:config_etapas")
    else:
        form = EtapaCRMForm()

    return render(request, "crm/config_etapas.html", {
        "etapas": etapas,
        "form": form,
    })


@gestor_required
def config_etapa_editar(request, pk):
    etapa = get_object_or_404(EtapaCRM, pk=pk)

    if request.method == "POST":
        form = EtapaCRMForm(request.POST, instance=etapa)
        if form.is_valid():
            form.save()
            messages.success(request, "Etapa atualizada.")
            return redirect("crm:config_etapas")
    else:
        form = EtapaCRMForm(instance=etapa)

    return render(request, "crm/config_etapas.html", {
        "etapas": EtapaCRM.objects.all(),
        "form": form,
        "editando": etapa,
    })


@gestor_required
@require_POST
def config_etapa_excluir(request, pk):
    etapa = get_object_or_404(EtapaCRM, pk=pk)
    etapa.soft_delete()
    messages.success(request, f"Etapa '{etapa.nome}' excluída.")
    return redirect("crm:config_etapas")
