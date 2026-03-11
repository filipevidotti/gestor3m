import json

from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from apps.clientes.models import Cliente
from apps.core.decorators import consultor_required, gestor_required

from .models import Proposta, PropostaServico, PropostaVisualizacao, Servico


# ─── Serviços CRUD (gestor) ──────────────────────────────────────

@gestor_required
def servicos_listar(request):
    servicos = Servico.objects.filter(is_active=True)
    return render(request, "propostas/servicos_listar.html", {
        "servicos": servicos,
    })


@gestor_required
def servico_criar(request):
    if request.method == "POST":
        Servico.objects.create(
            nome=request.POST.get("nome", ""),
            descricao=request.POST.get("descricao", ""),
            icone=request.POST.get("icone", ""),
            preco_sugerido=request.POST.get("preco_sugerido") or None,
            ordem=request.POST.get("ordem", 0),
        )
        messages.success(request, "Serviço criado com sucesso.")
        return redirect("propostas:servicos_listar")
    return render(request, "propostas/servico_form.html", {"editing": False})


@gestor_required
def servico_editar(request, pk):
    servico = get_object_or_404(Servico, pk=pk)
    if request.method == "POST":
        servico.nome = request.POST.get("nome", "")
        servico.descricao = request.POST.get("descricao", "")
        servico.icone = request.POST.get("icone", "")
        servico.preco_sugerido = request.POST.get("preco_sugerido") or None
        servico.ordem = request.POST.get("ordem", 0)
        servico.save()
        messages.success(request, "Serviço atualizado.")
        return redirect("propostas:servicos_listar")
    return render(request, "propostas/servico_form.html", {
        "servico": servico,
        "editing": True,
    })


@gestor_required
@require_POST
def servico_excluir(request, pk):
    servico = get_object_or_404(Servico, pk=pk)
    servico.soft_delete()
    messages.success(request, "Serviço removido.")
    return redirect("propostas:servicos_listar")


# ─── Propostas CRUD ──────────────────────────────────────────────

@consultor_required
def listar(request):
    qs = Proposta.objects.select_related("cliente", "consultor").filter(is_active=True)

    # Consultores veem apenas as suas
    if request.user.role == "consultor":
        qs = qs.filter(consultor=request.user)

    # Filtros
    status = request.GET.get("status")
    if status:
        qs = qs.filter(status=status)

    busca = request.GET.get("busca", "").strip()
    if busca:
        from django.db.models import Q
        qs = qs.filter(
            Q(lead_nome__icontains=busca)
            | Q(lead_loja__icontains=busca)
            | Q(lead_email__icontains=busca)
            | Q(cliente__empresa__icontains=busca)
        )

    return render(request, "propostas/listar.html", {
        "propostas": qs,
        "status_choices": Proposta.Status.choices,
        "status_atual": status or "",
    })


@consultor_required
def criar(request):
    clientes = Cliente.objects.filter(is_active=True).order_by("empresa")
    servicos = Servico.objects.filter(is_active=True).order_by("ordem")

    if request.method == "POST":
        cliente_id = request.POST.get("cliente")
        proposta = Proposta.objects.create(
            consultor=request.user,
            cliente_id=cliente_id if cliente_id else None,
            lead_nome=request.POST.get("lead_nome", ""),
            lead_loja=request.POST.get("lead_loja", ""),
            lead_email=request.POST.get("lead_email", ""),
            lead_telefone=request.POST.get("lead_telefone", ""),
            tipo_seller=request.POST.get("tipo_seller", "iniciante"),
            marketplace=request.POST.get("marketplace", "mercado_livre"),
        )
        messages.success(request, "Proposta criada. Preencha o questionário.")
        return redirect("propostas:questionario", pk=proposta.pk)

    return render(request, "propostas/criar.html", {
        "clientes": clientes,
        "servicos": servicos,
        "tipo_seller_choices": Proposta.TipoSeller.choices,
        "marketplace_choices": Proposta.Marketplace.choices,
    })


@consultor_required
def detalhe(request, pk):
    proposta = get_object_or_404(
        Proposta.objects.select_related("cliente", "consultor")
        .prefetch_related("servicos_incluidos__servico"),
        pk=pk,
    )
    return render(request, "propostas/detalhe.html", {
        "proposta": proposta,
    })


@consultor_required
def editar(request, pk):
    proposta = get_object_or_404(Proposta, pk=pk)
    clientes = Cliente.objects.filter(is_active=True).order_by("empresa")

    if request.method == "POST":
        cliente_id = request.POST.get("cliente")
        proposta.cliente_id = cliente_id if cliente_id else None
        proposta.lead_nome = request.POST.get("lead_nome", "")
        proposta.lead_loja = request.POST.get("lead_loja", "")
        proposta.lead_email = request.POST.get("lead_email", "")
        proposta.lead_telefone = request.POST.get("lead_telefone", "")
        proposta.tipo_seller = request.POST.get("tipo_seller", "iniciante")
        proposta.marketplace = request.POST.get("marketplace", "mercado_livre")
        proposta.save()
        messages.success(request, "Proposta atualizada.")
        return redirect("propostas:detalhe", pk=proposta.pk)

    return render(request, "propostas/criar.html", {
        "proposta": proposta,
        "clientes": clientes,
        "tipo_seller_choices": Proposta.TipoSeller.choices,
        "marketplace_choices": Proposta.Marketplace.choices,
        "editing": True,
    })


@consultor_required
@require_POST
def excluir(request, pk):
    proposta = get_object_or_404(Proposta, pk=pk)
    proposta.soft_delete()
    messages.success(request, "Proposta removida.")
    return redirect("propostas:listar")


# ─── Questionário (wizard 10 blocos) ─────────────────────────────

@consultor_required
def questionario(request, pk):
    proposta = get_object_or_404(Proposta, pk=pk)

    if request.method == "POST":
        passo = int(request.POST.get("passo", 1))
        respostas = proposta.respostas or {}

        # Salva respostas do passo atual
        dados_passo = {}
        for key, value in request.POST.items():
            if key.startswith("r_"):
                dados_passo[key[2:]] = value
        respostas[f"bloco_{passo}"] = dados_passo
        proposta.respostas = respostas

        acao = request.POST.get("acao", "proximo")

        if acao == "anterior" and passo > 1:
            proposta.passo_atual = passo - 1
        elif acao == "proximo" and passo < 10:
            proposta.passo_atual = passo + 1
        elif acao == "finalizar":
            proposta.status = Proposta.Status.CALCULANDO
            proposta.passo_atual = 10

        proposta.save()

        if acao == "finalizar":
            messages.success(request, "Questionário finalizado! Calculando métricas...")
            return redirect("propostas:detalhe", pk=proposta.pk)

        return redirect("propostas:questionario", pk=proposta.pk)

    return render(request, "propostas/questionario.html", {
        "proposta": proposta,
        "passo": proposta.passo_atual,
        "total_passos": 10,
    })


# ─── Cálculo + IA (Fase 2 — stubs) ──────────────────────────────

@consultor_required
@require_POST
def calcular(request, pk):
    from .utils import calcular_metricas

    proposta = get_object_or_404(Proposta, pk=pk)
    proposta.metricas = calcular_metricas(proposta)
    proposta.save(update_fields=["metricas"])
    messages.success(request, "Métricas calculadas com sucesso!")
    return redirect("propostas:detalhe", pk=proposta.pk)


@consultor_required
@require_POST
def gerar_ia(request, pk):
    from .ai import gerar_diagnostico, gerar_proposta_comercial, gerar_proposicao_valor

    proposta = get_object_or_404(Proposta, pk=pk)

    # Calcular métricas primeiro se não existem
    if not proposta.metricas:
        from .utils import calcular_metricas
        proposta.metricas = calcular_metricas(proposta)

    proposta.status = Proposta.Status.GERANDO_IA
    proposta.save()

    proposta.diagnostico_ia = gerar_diagnostico(proposta)
    proposta.proposicao_valor = gerar_proposicao_valor(proposta)
    proposta.proposta_comercial = gerar_proposta_comercial(proposta)
    proposta.status = Proposta.Status.REVISAO
    proposta.save()

    messages.success(request, "Textos gerados pela IA! Revise antes de enviar.")
    return redirect("propostas:revisao", pk=proposta.pk)


# ─── Revisão ─────────────────────────────────────────────────────

@consultor_required
def revisao(request, pk):
    proposta = get_object_or_404(
        Proposta.objects.select_related("cliente", "consultor")
        .prefetch_related("servicos_incluidos__servico"),
        pk=pk,
    )
    servicos = Servico.objects.filter(is_active=True).order_by("ordem")

    if request.method == "POST":
        proposta.diagnostico_ia = request.POST.get("diagnostico_ia", "")
        proposta.proposicao_valor = request.POST.get("proposicao_valor", "")
        proposta.proposta_comercial = request.POST.get("proposta_comercial", "")
        proposta.valor_setup = request.POST.get("valor_setup", 0)
        proposta.valor_mensalidade = request.POST.get("valor_mensalidade", 0)
        proposta.condicoes_especiais = request.POST.get("condicoes_especiais", "")
        proposta.status = Proposta.Status.REVISAO
        proposta.save()

        # Atualizar serviços incluídos
        proposta.servicos_incluidos.all().delete()
        servicos_json = json.loads(request.POST.get("servicos_incluidos", "[]"))
        for idx, s in enumerate(servicos_json):
            PropostaServico.objects.create(
                proposta=proposta,
                servico_id=s["servico_id"],
                valor=s.get("valor", 0),
                descricao_custom=s.get("descricao_custom", ""),
                ordem=idx,
            )

        messages.success(request, "Revisão salva.")
        return redirect("propostas:detalhe", pk=proposta.pk)

    return render(request, "propostas/revisao.html", {
        "proposta": proposta,
        "servicos": servicos,
    })


# ─── Enviar proposta ─────────────────────────────────────────────

@consultor_required
@require_POST
def enviar(request, pk):
    proposta = get_object_or_404(Proposta, pk=pk)
    proposta.status = Proposta.Status.ENVIADO
    proposta.data_envio = timezone.now()
    proposta.data_expiracao = (timezone.now() + timezone.timedelta(days=15)).date()
    proposta.save()
    messages.success(request, "Proposta enviada com sucesso!")
    return redirect("propostas:detalhe", pk=proposta.pk)


# ─── Exportar PDF (Fase 3 — stub) ────────────────────────────────

@consultor_required
def exportar_pdf(request, pk):
    from .pdf import gerar_proposta_pdf

    proposta = get_object_or_404(
        Proposta.objects.select_related("cliente", "consultor")
        .prefetch_related("servicos_incluidos__servico"),
        pk=pk,
    )
    return gerar_proposta_pdf(proposta)


# ─── Link Público (sem auth) ─────────────────────────────────────

def publico(request, token):
    proposta = get_object_or_404(
        Proposta.objects.select_related("cliente", "consultor")
        .prefetch_related("servicos_incluidos__servico"),
        token=token,
        status__in=[
            Proposta.Status.ENVIADO,
            Proposta.Status.ACEITO,
            Proposta.Status.RECUSADO,
        ],
    )

    # Registrar visualização
    proposta.visualizacoes += 1
    proposta.save(update_fields=["visualizacoes"])

    PropostaVisualizacao.objects.create(
        proposta=proposta,
        ip=request.META.get("REMOTE_ADDR", ""),
        user_agent=request.META.get("HTTP_USER_AGENT", "")[:500],
    )

    return render(request, "propostas/publico.html", {
        "proposta": proposta,
    })


@require_POST
def publico_responder(request, token):
    proposta = get_object_or_404(
        Proposta,
        token=token,
        status=Proposta.Status.ENVIADO,
    )

    acao = request.POST.get("acao")
    if acao == "aceitar":
        proposta.status = Proposta.Status.ACEITO
        proposta.data_resposta = timezone.now()
        proposta.save()
        messages.success(request, "Proposta aceita! Entraremos em contato.")
    elif acao == "recusar":
        proposta.status = Proposta.Status.RECUSADO
        proposta.data_resposta = timezone.now()
        proposta.motivo_recusa = request.POST.get("motivo_recusa", "")
        proposta.save()
        messages.info(request, "Resposta registrada. Obrigado pelo feedback.")

    return redirect("propostas:publico", token=token)
