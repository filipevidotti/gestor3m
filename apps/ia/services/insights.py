"""
Serviço de geração de insights diários via IA.

Analisa dados de cada consultor e gera alertas/sugestões.
"""
import logging
from datetime import timedelta

from django.utils import timezone

from .engine import chamar_ia, extrair_json

logger = logging.getLogger(__name__)

PROMPT_INSIGHTS = """Analise os dados dos clientes deste consultor e gere insights acionáveis.

## Consultor: {consultor_nome}

## Clientes e Dados
{clientes_dados}

---

Para cada insight relevante, retorne um JSON com lista:
{{
    "insights": [
        {{
            "cliente_id": <id do cliente ou null se geral>,
            "tipo": "alerta" | "sugestao" | "elogio" | "risco",
            "prioridade": "baixa" | "media" | "alta" | "critica",
            "titulo": "Título curto do insight (max 100 chars)",
            "descricao": "Descrição detalhada com dados concretos",
            "acao_sugerida": "Ação concreta que o consultor deve tomar",
            "expira_em_dias": 7
        }}
    ]
}}

Regras:
- Máximo 10 insights por consultor
- Priorize: atrasados > scores caindo > sem atividade > oportunidades
- Inclua dados concretos (scores, dias, percentuais)
- Ações devem ser específicas ("Agendar reunião de reputação com Cliente X")
- Elogios quando um cliente evoluiu significativamente
"""


def coletar_dados_consultor(consultor):
    """Coleta dados relevantes de todos os clientes do consultor."""
    from apps.clientes.models import Cliente
    from apps.tarefas.models import Tarefa
    from apps.reunioes.models import Reuniao

    hoje = timezone.now().date()
    clientes = Cliente.objects.filter(
        consultor=consultor, status__in=["ativo", "onboarding"]
    ).select_related("consultor")

    dados = []
    for cliente in clientes:
        # Último diagnóstico
        ultimo_diag = (
            cliente.diagnosticos.filter(status="completed")
            .order_by("-ano", "-mes")
            .first()
        )
        # Diagnóstico anterior (para comparação)
        diag_anterior = (
            cliente.diagnosticos.filter(status="completed")
            .order_by("-ano", "-mes")[1:2]
        )
        diag_anterior = diag_anterior.first() if diag_anterior.exists() else None

        # Tarefas atrasadas
        tarefas_atrasadas = Tarefa.objects.filter(
            cliente=cliente,
            status__in=["pendente", "em_andamento"],
            prazo__lt=hoje,
        ).count()

        tarefas_pendentes = Tarefa.objects.filter(
            cliente=cliente,
            status__in=["pendente", "em_andamento"],
        ).count()

        # Última reunião
        ultima_reuniao = (
            Reuniao.objects.filter(cliente=cliente)
            .order_by("-data")
            .first()
        )
        dias_sem_reuniao = (
            (hoje - ultima_reuniao.data.date()).days if ultima_reuniao else 999
        )

        # Jornada
        from apps.jornadas.models import JornadaCliente
        jornada = (
            JornadaCliente.objects.filter(cliente=cliente, status="ativa")
            .first()
        )
        etapas_atrasadas = 0
        if jornada:
            etapas_atrasadas = jornada.etapas.filter(
                status="atrasada",
            ).count()
            etapas_atrasadas += jornada.etapas.filter(
                status="pendente",
                data_limite__lt=hoje,
            ).count()

        info = f"""
### Cliente: {cliente.empresa} (ID {cliente.id})
- Status: {cliente.get_status_display()}
- Nicho: {cliente.nicho or 'N/A'}
- Dias como cliente: {(hoje - cliente.data_inicio).days}
- Score atual: {ultimo_diag.score if ultimo_diag else 'Sem diagnóstico'}
- Score anterior: {diag_anterior.score if diag_anterior else 'N/A'}
- Scores categorias: {ultimo_diag.scores_por_categoria if ultimo_diag else 'N/A'}
- Tarefas atrasadas: {tarefas_atrasadas}
- Tarefas pendentes: {tarefas_pendentes}
- Dias sem reunião: {dias_sem_reuniao}
- Etapas jornada atrasadas: {etapas_atrasadas}
"""
        dados.append({"cliente": cliente, "info": info})

    return dados


def gerar_insights_consultor(consultor):
    """Gera insights para um consultor específico."""
    from apps.ia.models import InsightIA

    dados = coletar_dados_consultor(consultor)
    if not dados:
        return []

    clientes_texto = "\n".join([d["info"] for d in dados])
    clientes_map = {d["cliente"].id: d["cliente"] for d in dados}

    prompt = PROMPT_INSIGHTS.format(
        consultor_nome=consultor.get_full_name(),
        clientes_dados=clientes_texto,
    )

    result = chamar_ia(
        prompt=prompt,
        tipo_analise="insight",
        consultor=consultor,
    )

    if not result.get("success"):
        logger.error(f"Falha ao gerar insights para {consultor}: {result.get('error')}")
        return []

    parsed = extrair_json(result["content"])
    if not parsed or "insights" not in parsed:
        logger.error(f"Resposta IA sem insights válidos para {consultor}")
        return []

    # Limpar insights antigos não lidos (substituir)
    InsightIA.objects.filter(
        consultor=consultor, lido=False
    ).update(is_active=False)

    insights_criados = []
    hoje = timezone.now().date()

    for item in parsed["insights"][:10]:
        cliente_id = item.get("cliente_id")
        cliente = clientes_map.get(cliente_id) if cliente_id else None
        expira_dias = item.get("expira_em_dias", 7)

        insight = InsightIA.objects.create(
            consultor=consultor,
            cliente=cliente,
            tipo=item.get("tipo", "sugestao"),
            prioridade=item.get("prioridade", "media"),
            titulo=item.get("titulo", "")[:300],
            descricao=item.get("descricao", ""),
            acao_sugerida=item.get("acao_sugerida", "")[:300],
            data_expiracao=hoje + timedelta(days=expira_dias),
        )
        insights_criados.append(insight)

    return insights_criados
