import json
from datetime import timedelta

from django.contrib.auth.decorators import login_required
from django.db.models import Avg, Count, Sum
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from apps.checklists.models import ChecklistExecution
from apps.clientes.models import Cliente
from apps.core.decorators import consultor_required
from apps.diagnosticos.models import Diagnostic
from apps.financeiro.models import Pagamento
from apps.notificacoes.models import Notificacao
from apps.reunioes.models import Reuniao
from apps.tarefas.models import Tarefa


@login_required
def index(request):
    if request.user.is_seller:
        return redirect("portal:dashboard")

    hoje = timezone.now()
    inicio_semana = hoje - timedelta(days=hoje.weekday())
    fim_semana = inicio_semana + timedelta(days=7)
    inicio_mes = hoje.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    # Filtro por role
    if request.user.is_gestor:
        clientes_qs = Cliente.objects.all()
        tarefas_qs = Tarefa.objects.all()
    elif request.user.is_consultor:
        clientes_qs = Cliente.objects.filter(consultor=request.user)
        tarefas_qs = Tarefa.objects.filter(cliente__consultor=request.user)
    else:
        clientes_qs = Cliente.objects.none()
        tarefas_qs = Tarefa.objects.none()

    # KPIs
    clientes_ativos = clientes_qs.filter(status="ativo").count()
    tarefas_pendentes = tarefas_qs.filter(status__in=["pendente", "em_andamento"]).count()
    reunioes_semana = Reuniao.objects.filter(data__gte=inicio_semana, data__lt=fim_semana).count()
    faturamento_mensal = Pagamento.objects.filter(
        status="pago", mes_referencia__gte=inicio_mes
    ).aggregate(total=Sum("valor"))["total"] or 0

    # Extra
    tarefas_atrasadas = tarefas_qs.filter(status="atrasado").count()
    tarefas_urgentes = tarefas_qs.filter(prioridade="urgente", status__in=["pendente", "em_andamento"]).count()
    clientes_onboarding = clientes_qs.filter(status="onboarding").count()
    total_clientes = clientes_qs.count()
    notificacoes_nao_lidas = Notificacao.objects.filter(destinatario=request.user, lida=False).count()

    # Recentes
    tarefas_recentes = tarefas_qs.select_related("cliente", "responsavel").order_by("-created_at")[:5]
    reunioes_proximas = Reuniao.objects.select_related("cliente").filter(data__gte=hoje).order_by("data")[:5]
    pagamentos_atrasados = Pagamento.objects.select_related("contrato__cliente").filter(status="atrasado").order_by("mes_referencia")[:5]

    context = {
        "clientes_ativos": clientes_ativos,
        "tarefas_pendentes": tarefas_pendentes,
        "reunioes_semana": reunioes_semana,
        "faturamento_mensal": faturamento_mensal,
        "tarefas_atrasadas": tarefas_atrasadas,
        "tarefas_urgentes": tarefas_urgentes,
        "clientes_onboarding": clientes_onboarding,
        "total_clientes": total_clientes,
        "notificacoes_nao_lidas": notificacoes_nao_lidas,
        "tarefas_recentes": tarefas_recentes,
        "reunioes_proximas": reunioes_proximas,
        "pagamentos_atrasados": pagamentos_atrasados,
    }
    return render(request, "dashboard/index.html", context)


@consultor_required
def evolucao_cliente(request, pk):
    """Dashboard de evolução completa de um cliente."""
    cliente = get_object_or_404(Cliente, pk=pk)

    # Verificar acesso: gestor vê tudo, consultor só seus clientes
    if request.user.is_consultor and cliente.consultor != request.user:
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden("Acesso negado.")

    # Diagnósticos dos últimos 12 meses
    diagnosticos = (
        Diagnostic.objects.filter(cliente=cliente, status="completed")
        .order_by("ano", "mes")
    )

    scores_mensal = []
    scores_categorias_atual = {}
    scores_categorias_primeiro = {}

    for d in diagnosticos:
        label = f"{d.mes:02d}/{d.ano}"
        scores_mensal.append({"label": label, "score": float(d.score or 0)})
        if d.scores_por_categoria:
            if not scores_categorias_primeiro:
                scores_categorias_primeiro = {
                    k: float(v) for k, v in d.scores_por_categoria.items()
                }
            scores_categorias_atual = {
                k: float(v) for k, v in d.scores_por_categoria.items()
            }

    # Tarefas por mês (últimos 6 meses)
    hoje = timezone.localdate()
    tarefas_mensal = []
    reunioes_mensal = []
    for i in range(5, -1, -1):
        mes_ref = (hoje.replace(day=1) - timedelta(days=i * 30)).replace(day=1)
        label = f"{mes_ref.month:02d}/{mes_ref.year}"

        t_concluidas = Tarefa.objects.filter(
            cliente=cliente,
            status="concluido",
            updated_at__year=mes_ref.year,
            updated_at__month=mes_ref.month,
        ).count()
        t_total = Tarefa.objects.filter(
            cliente=cliente,
            created_at__year=mes_ref.year,
            created_at__month=mes_ref.month,
        ).count()
        tarefas_mensal.append({
            "label": label,
            "concluidas": t_concluidas,
            "total": t_total,
        })

        r_count = Reuniao.objects.filter(
            cliente=cliente,
            data__year=mes_ref.year,
            data__month=mes_ref.month,
        ).count()
        reunioes_mensal.append({"label": label, "total": r_count})

    # Checklists score médio
    checklists_score = ChecklistExecution.objects.filter(
        cliente=cliente,
        status="completed",
    ).aggregate(media=Avg("score"))["media"] or 0

    # Marcos (timeline)
    marcos = []
    primeira_reuniao = Reuniao.objects.filter(cliente=cliente).order_by("data").first()
    if primeira_reuniao:
        marcos.append({
            "data": primeira_reuniao.data.strftime("%d/%m/%Y"),
            "titulo": "Primeira Reunião",
            "tipo": primeira_reuniao.get_tipo_display(),
        })
    primeiro_diag = diagnosticos.first()
    if primeiro_diag:
        marcos.append({
            "data": f"01/{primeiro_diag.mes:02d}/{primeiro_diag.ano}",
            "titulo": "Primeiro Diagnóstico",
            "tipo": f"Score: {primeiro_diag.score}",
        })

    # Comparativo
    score_primeiro = float(diagnosticos.first().score) if diagnosticos.exists() else 0
    score_atual = float(diagnosticos.last().score) if diagnosticos.exists() else 0
    variacao = score_atual - score_primeiro

    context = {
        "cliente": cliente,
        "scores_mensal_json": json.dumps(scores_mensal),
        "categorias_primeiro_json": json.dumps(scores_categorias_primeiro),
        "categorias_atual_json": json.dumps(scores_categorias_atual),
        "tarefas_mensal_json": json.dumps(tarefas_mensal),
        "reunioes_mensal_json": json.dumps(reunioes_mensal),
        "checklists_score": round(checklists_score, 1),
        "marcos": marcos,
        "score_primeiro": score_primeiro,
        "score_atual": score_atual,
        "variacao": round(variacao, 1),
        "total_diagnosticos": diagnosticos.count(),
        "total_reunioes": Reuniao.objects.filter(cliente=cliente).count(),
        "total_tarefas_concluidas": Tarefa.objects.filter(
            cliente=cliente, status="concluido"
        ).count(),
    }
    return render(request, "dashboard/evolucao.html", context)


@login_required
def meu_dia(request):
    """Dashboard 'Meu Dia' — visão consolidada do dia do consultor."""
    hoje = timezone.now().date()
    inicio_semana = hoje - timedelta(days=hoje.weekday())
    fim_semana = inicio_semana + timedelta(days=6)
    user = request.user

    # Filter based on role
    if user.is_gestor:
        tarefas_base = Tarefa.objects.all()
        reunioes_base = Reuniao.objects.all()
    elif user.is_consultor:
        tarefas_base = Tarefa.objects.filter(responsavel=user)
        reunioes_base = Reuniao.objects.filter(consultor=user)
    else:
        tarefas_base = Tarefa.objects.filter(responsavel=user)
        reunioes_base = Reuniao.objects.filter(cliente__usuario=user)

    # Overdue tasks
    tarefas_atrasadas = tarefas_base.filter(
        status__in=["pendente", "em_andamento"],
        prazo__lt=hoje,
    ).select_related("cliente")[:10]

    # Overdue journey steps
    from apps.jornadas.models import EtapaCliente

    if user.is_gestor:
        etapas_base = EtapaCliente.objects.all()
    else:
        etapas_base = EtapaCliente.objects.filter(
            jornada__cliente__consultor=user
        )

    etapas_atrasadas = etapas_base.filter(
        status__in=["pendente", "em_andamento"],
        data_limite__lt=hoje,
        jornada__status="ativa",
    ).select_related("jornada__cliente")[:10]

    # Today's meetings
    reunioes_hoje = reunioes_base.filter(
        data__date=hoje
    ).select_related("cliente").order_by("data")

    # Today's journey steps
    etapas_hoje = etapas_base.filter(
        data_prevista=hoje,
        status="pendente",
        jornada__status="ativa",
    ).select_related("jornada__cliente")

    # Today's tasks
    tarefas_hoje = tarefas_base.filter(
        prazo=hoje,
        status__in=["pendente", "em_andamento"],
    ).select_related("cliente")

    # Week stats
    tarefas_semana_total = tarefas_base.filter(
        prazo__range=[inicio_semana, fim_semana]
    ).count()
    tarefas_semana_concluidas = tarefas_base.filter(
        prazo__range=[inicio_semana, fim_semana], status="concluido"
    ).count()
    reunioes_semana = reunioes_base.filter(
        data__date__range=[inicio_semana, fim_semana]
    ).count()

    # IA Insights
    from apps.ia.models import InsightIA

    insights = InsightIA.objects.filter(
        consultor=user, lido=False, is_active=True
    ).select_related("cliente").order_by("-prioridade", "-created_at")[:8]

    # Clients needing attention
    if user.is_gestor:
        clientes = Cliente.objects.filter(status="ativo")
    else:
        clientes = Cliente.objects.filter(consultor=user, status="ativo")

    clientes_atencao = []
    for cliente in clientes[:20]:
        n_atrasadas = Tarefa.objects.filter(
            cliente=cliente,
            status__in=["pendente", "em_andamento"],
            prazo__lt=hoje,
        ).count()
        if n_atrasadas > 0:
            clientes_atencao.append({"cliente": cliente, "atrasadas": n_atrasadas})
    clientes_atencao.sort(key=lambda x: -x["atrasadas"])

    return render(request, "dashboard/meu_dia.html", {
        "tarefas_atrasadas": tarefas_atrasadas,
        "etapas_atrasadas": etapas_atrasadas,
        "reunioes_hoje": reunioes_hoje,
        "etapas_hoje": etapas_hoje,
        "tarefas_hoje": tarefas_hoje,
        "tarefas_semana_total": tarefas_semana_total,
        "tarefas_semana_concluidas": tarefas_semana_concluidas,
        "reunioes_semana": reunioes_semana,
        "insights": insights,
        "clientes_atencao": clientes_atencao[:5],
    })
