"""
Serviço de geração e recalibração de jornadas com IA.

Analisa diagnóstico do cliente e personaliza a jornada
(adiciona/remove etapas dos templates).
"""
import logging

from .engine import chamar_ia, extrair_json

logger = logging.getLogger(__name__)

PROMPT_GERAR_JORNADA = """Analise o diagnóstico deste vendedor do Mercado Livre e recomende uma jornada de consultoria personalizada.

## Dados do Cliente
- Empresa: {empresa}
- Status: {status}
- Tipo consultoria: {tipo_consultoria}
- Data início: {data_inicio}
- Nicho: {nicho}

## Diagnóstico (Score 0-10)
- Score Geral: {score_geral}
- Scores por categoria:
{scores_detalhados}

## Templates de Jornada Disponíveis
{templates_disponiveis}

## Etapas Base do Template Selecionado
{etapas_template}

---

Retorne um JSON com esta estrutura EXATA:
{{
    "template_recomendado_id": <id do template mais adequado>,
    "justificativa": "Por que este template foi escolhido (2-3 frases)",
    "etapas_manter": [<lista de IDs das etapas do template que devem ser mantidas>],
    "etapas_remover": [
        {{
            "etapa_id": <id>,
            "motivo": "Por que remover esta etapa"
        }}
    ],
    "etapas_adicionar": [
        {{
            "nome": "Nome da etapa",
            "descricao": "Descrição detalhada",
            "tipo": "reuniao" | "diagnostico" | "checklist" | "treinamento" | "tarefa" | "marco",
            "dias_offset": <dias após início>,
            "duracao_dias": <prazo para completar>,
            "prioridade": "baixa" | "media" | "alta" | "urgente",
            "motivo": "Por que adicionar esta etapa baseado no diagnóstico"
        }}
    ],
    "observacoes": "Observações gerais sobre a jornada recomendada",
    "areas_foco": ["Lista das 3 áreas prioritárias baseado nos scores"]
}}
"""

PROMPT_RECALIBRAR = """A jornada do cliente foi recalibrada com base em um novo diagnóstico.

## Dados do Cliente
- Empresa: {empresa}
- Nicho: {nicho}

## Diagnóstico Anterior
- Score: {score_anterior}
- Categorias: {scores_anterior}

## Diagnóstico Atual
- Score: {score_atual}
- Categorias: {scores_atual}

## Jornada Atual
{etapas_atuais}

---

Retorne um JSON com esta estrutura EXATA:
{{
    "analise_evolucao": "Análise da evolução entre os dois diagnósticos (2-3 frases)",
    "etapas_adicionar": [
        {{
            "nome": "Nome",
            "descricao": "Descrição",
            "tipo": "reuniao" | "treinamento" | "checklist" | "tarefa" | "marco",
            "dias_offset": <dias a partir de hoje>,
            "duracao_dias": <prazo>,
            "motivo": "Justificativa baseada na mudança de score"
        }}
    ],
    "etapas_remover_ids": [<ids de etapas pendentes que não são mais necessárias>],
    "etapas_repriorizar": [
        {{
            "etapa_id": <id>,
            "nova_ordem": <nova posição>,
            "motivo": "Por que repriorizar"
        }}
    ],
    "alertas": ["Lista de alertas importantes sobre a evolução"],
    "areas_melhoraram": ["Categorias que melhoraram"],
    "areas_pioraram": ["Categorias que pioraram"]
}}
"""


def gerar_jornada(cliente, diagnostico, templates_jornada):
    """Gera jornada personalizada usando IA."""

    # Montar contexto dos templates disponíveis
    templates_info = ""
    for t in templates_jornada:
        templates_info += f"\n- ID {t.id}: {t.nome} — {t.descricao}"

    # Montar scores detalhados
    scores_det = ""
    if diagnostico.scores_por_categoria:
        for cat, score in diagnostico.scores_por_categoria.items():
            scores_det += f"  - {cat}: {score}/10\n"
    else:
        scores_det = "  Sem detalhamento por categoria"

    # Montar etapas de todos os templates para a IA escolher
    etapas_info = ""
    for t in templates_jornada:
        etapas_info += f"\n### Template: {t.nome} (ID {t.id})\n"
        for e in t.etapas.filter(is_active=True).order_by("ordem"):
            etapas_info += (
                f"  - ID {e.id}: {e.nome} | tipo={e.tipo} | "
                f"dia={e.dias_offset} | duração={e.duracao_dias}d | "
                f"obrigatória={'sim' if e.is_obrigatoria else 'não'} | "
                f"condição: {e.condicao or 'nenhuma'}\n"
            )

    prompt = PROMPT_GERAR_JORNADA.format(
        empresa=cliente.empresa,
        status=cliente.get_status_display(),
        tipo_consultoria=cliente.get_tipo_consultoria_display(),
        data_inicio=str(cliente.data_inicio),
        nicho=cliente.nicho or "Não informado",
        score_geral=str(diagnostico.score),
        scores_detalhados=scores_det,
        templates_disponiveis=templates_info,
        etapas_template=etapas_info,
    )

    result = chamar_ia(
        prompt=prompt,
        tipo_analise="jornada",
        cliente=cliente,
    )

    if not result.get("success"):
        return result

    parsed = extrair_json(result["content"])
    if not parsed:
        return {
            "success": False,
            "error": "Não foi possível extrair JSON da resposta da IA",
            "raw_content": result["content"],
        }

    return {"success": True, "data": parsed}


def recalibrar_jornada(cliente, jornada, diagnostico_anterior, diagnostico_atual):
    """Recalibra jornada existente com base em novo diagnóstico."""

    # Montar etapas atuais
    etapas_info = ""
    for e in jornada.etapas.filter(is_active=True).order_by("ordem"):
        status_label = e.get_status_display()
        etapas_info += (
            f"  - ID {e.id}: {e.nome} | tipo={e.tipo} | "
            f"status={status_label} | data_prevista={e.data_prevista} | "
            f"{'[CONCLUÍDA]' if e.data_conclusao else ''}\n"
        )

    prompt = PROMPT_RECALIBRAR.format(
        empresa=cliente.empresa,
        nicho=cliente.nicho or "Não informado",
        score_anterior=str(diagnostico_anterior.score),
        scores_anterior=str(diagnostico_anterior.scores_por_categoria),
        score_atual=str(diagnostico_atual.score),
        scores_atual=str(diagnostico_atual.scores_por_categoria),
        etapas_atuais=etapas_info,
    )

    result = chamar_ia(
        prompt=prompt,
        tipo_analise="recalibracao",
        cliente=cliente,
    )

    if not result.get("success"):
        return result

    parsed = extrair_json(result["content"])
    if not parsed:
        return {
            "success": False,
            "error": "Não foi possível extrair JSON da resposta da IA",
            "raw_content": result["content"],
        }

    return {"success": True, "data": parsed}
