"""
Serviço para aplicar resultados da IA nas jornadas.
"""
import logging
from datetime import timedelta

from django.db import models
from django.utils import timezone

logger = logging.getLogger(__name__)


def aplicar_jornada_ia(cliente, diagnostico, dados_ia):
    """
    Aplica a recomendação da IA para gerar a jornada do cliente.

    dados_ia = {
        "template_recomendado_id": int,
        "justificativa": str,
        "etapas_manter": [int],
        "etapas_remover": [{"etapa_id": int, "motivo": str}],
        "etapas_adicionar": [{"nome": str, "tipo": str, ...}],
        "areas_foco": [str],
    }
    """
    from apps.jornadas.models import JornadaTemplate, JornadaCliente, EtapaCliente

    template_id = dados_ia.get("template_recomendado_id")
    template = None

    if template_id:
        try:
            template = JornadaTemplate.objects.get(pk=template_id, is_active=True)
        except JornadaTemplate.DoesNotExist:
            template = JornadaTemplate.objects.filter(is_active=True).first()

    if not template:
        template = JornadaTemplate.objects.filter(is_active=True).first()

    if not template:
        logger.error("Nenhum template de jornada disponível")
        return None

    hoje = timezone.now().date()

    # Criar jornada do cliente
    jornada = JornadaCliente.objects.create(
        cliente=cliente,
        jornada_template=template,
        nome=f"{template.nome} - {cliente.empresa}",
        data_inicio=hoje,
        justificativa_ia=dados_ia.get("justificativa", ""),
        areas_foco=dados_ia.get("areas_foco", []),
    )

    # IDs de etapas a remover
    ids_remover = {
        item["etapa_id"] for item in dados_ia.get("etapas_remover", [])
    }

    # Criar etapas do template (exceto as removidas pela IA)
    ordem = 0
    for etapa_tpl in template.etapas.filter(is_active=True).order_by("ordem"):
        if etapa_tpl.id in ids_remover:
            continue

        EtapaCliente.objects.create(
            jornada=jornada,
            etapa_template=etapa_tpl,
            nome=etapa_tpl.nome,
            descricao=etapa_tpl.descricao,
            tipo=etapa_tpl.tipo,
            ordem=ordem,
            data_prevista=hoje + timedelta(days=etapa_tpl.dias_offset),
            data_limite=hoje + timedelta(days=etapa_tpl.dias_offset + etapa_tpl.duracao_dias),
        )
        ordem += 1

    # Adicionar etapas extras da IA
    for etapa_ia in dados_ia.get("etapas_adicionar", []):
        dias_offset = etapa_ia.get("dias_offset", 0)
        duracao = etapa_ia.get("duracao_dias", 7)

        EtapaCliente.objects.create(
            jornada=jornada,
            nome=etapa_ia.get("nome", "Etapa IA"),
            descricao=etapa_ia.get("descricao", ""),
            tipo=etapa_ia.get("tipo", "tarefa"),
            ordem=ordem,
            data_prevista=hoje + timedelta(days=dias_offset),
            data_limite=hoje + timedelta(days=dias_offset + duracao),
            adicionada_por_ia=True,
            motivo_ia=etapa_ia.get("motivo", ""),
        )
        ordem += 1

    jornada.calcular_progresso()
    logger.info(f"Jornada criada: {jornada} com {ordem} etapas")
    return jornada


def aplicar_recalibracao_ia(jornada, dados_ia):
    """
    Aplica recalibração da IA na jornada existente.

    dados_ia = {
        "etapas_adicionar": [...],
        "etapas_remover_ids": [int],
        "etapas_repriorizar": [{"etapa_id": int, "nova_ordem": int}],
        "analise_evolucao": str,
    }
    """
    from apps.jornadas.models import EtapaCliente

    hoje = timezone.now().date()

    # Remover etapas pendentes que a IA disse que não são mais necessárias
    ids_remover = dados_ia.get("etapas_remover_ids", [])
    if ids_remover:
        jornada.etapas.filter(
            id__in=ids_remover,
            status__in=["pendente", "em_andamento"],
        ).update(status="pulada")

    # Repriorizar etapas
    for reprio in dados_ia.get("etapas_repriorizar", []):
        jornada.etapas.filter(id=reprio["etapa_id"]).update(
            ordem=reprio["nova_ordem"]
        )

    # Adicionar novas etapas
    max_ordem = jornada.etapas.aggregate(
        max_ordem=models.Max("ordem")
    )["max_ordem"] or 0

    for etapa_ia in dados_ia.get("etapas_adicionar", []):
        max_ordem += 1
        dias_offset = etapa_ia.get("dias_offset", 0)
        duracao = etapa_ia.get("duracao_dias", 7)

        EtapaCliente.objects.create(
            jornada=jornada,
            nome=etapa_ia.get("nome", "Etapa IA"),
            descricao=etapa_ia.get("descricao", ""),
            tipo=etapa_ia.get("tipo", "tarefa"),
            ordem=max_ordem,
            data_prevista=hoje + timedelta(days=dias_offset),
            data_limite=hoje + timedelta(days=dias_offset + duracao),
            adicionada_por_ia=True,
            motivo_ia=etapa_ia.get("motivo", ""),
        )

    # Atualizar jornada
    jornada.recalibragens += 1
    jornada.save(update_fields=["recalibragens", "updated_at"])
    jornada.calcular_progresso()

    logger.info(
        f"Jornada recalibrada: {jornada} "
        f"(+{len(dados_ia.get('etapas_adicionar', []))} etapas, "
        f"-{len(ids_remover)} removidas)"
    )
    return jornada
