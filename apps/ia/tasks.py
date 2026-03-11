"""Celery tasks para processamento assíncrono de IA."""
import logging

from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=2, default_retry_delay=60)
def processar_reuniao(self, reuniao_id):
    """
    Task completa de processamento de reunião:
    1. Transcreve áudio (Whisper)
    2. Analisa transcrição (Agno/LLM)
    3. Salva resultados na reunião
    4. Cria tarefas automáticas
    """
    from apps.reunioes.models import Reuniao
    from apps.ia.services.reuniao import transcrever_audio, analisar_reuniao, criar_tarefas_da_reuniao

    try:
        reuniao = Reuniao.objects.get(pk=reuniao_id)
    except Reuniao.DoesNotExist:
        logger.error(f"Reunião {reuniao_id} não encontrada")
        return

    # 1. Transcrever áudio se tiver arquivo
    if reuniao.audio_arquivo and not reuniao.transcricao:
        reuniao.transcricao_status = "processando"
        reuniao.save(update_fields=["transcricao_status"])

        result = transcrever_audio(reuniao.audio_arquivo.path)

        if result["success"]:
            reuniao.transcricao = result["transcricao"]
            reuniao.transcricao_status = "concluida"
            reuniao.save(update_fields=["transcricao", "transcricao_status"])
        else:
            reuniao.transcricao_status = "erro"
            reuniao.save(update_fields=["transcricao_status"])
            logger.error(f"Erro transcrição reunião {reuniao_id}: {result['error']}")
            # Se tiver rascunho, continua com ele
            if not reuniao.transcricao_rascunho:
                return

    # 2. Analisar com IA (usa transcrição final ou rascunho)
    if reuniao.transcricao or reuniao.transcricao_rascunho:
        result = analisar_reuniao(reuniao)

        if result.get("success"):
            data = result["data"]
            reuniao.resumo_ia = data.get("resumo", "")
            reuniao.acoes_identificadas = data.get("acoes_identificadas", [])
            reuniao.sentimento_cliente = data.get("sentimento_cliente", "neutro")
            reuniao.insights_ia = data.get("insights", [])

            # Se não tinha resumo manual, usar o da IA
            if not reuniao.resumo:
                reuniao.resumo = data.get("resumo", "")
            if not reuniao.proximos_passos:
                reuniao.proximos_passos = data.get("proximos_passos", "")

            reuniao.save(update_fields=[
                "resumo_ia", "acoes_identificadas", "sentimento_cliente",
                "insights_ia", "resumo", "proximos_passos",
            ])

            # 3. Criar tarefas
            acoes = data.get("acoes_identificadas", [])
            if acoes:
                tarefas = criar_tarefas_da_reuniao(reuniao, acoes)
                logger.info(f"Criadas {len(tarefas)} tarefas da reunião {reuniao_id}")
        else:
            logger.error(f"Erro análise IA reunião {reuniao_id}: {result.get('error')}")


@shared_task
def gerar_insights_diarios():
    """
    Task diária: gera insights IA para todos os consultores ativos.
    Configurar no Celery Beat para rodar às 6h.
    """
    from apps.accounts.models import User
    from apps.ia.services.insights import gerar_insights_consultor

    consultores = User.objects.filter(
        role__in=["consultor", "gestor"], is_active=True
    )

    total_insights = 0
    for consultor in consultores:
        try:
            insights = gerar_insights_consultor(consultor)
            total_insights += len(insights)
            logger.info(f"Gerados {len(insights)} insights para {consultor}")
        except Exception as e:
            logger.error(f"Erro insights para {consultor}: {e}")

    logger.info(f"Total: {total_insights} insights gerados para {consultores.count()} consultores")


@shared_task
def gerar_jornada_automatica(cliente_id, diagnostico_id):
    """Gera jornada automaticamente após conclusão de diagnóstico."""
    from apps.clientes.models import Cliente
    from apps.diagnosticos.models import Diagnostic
    from apps.jornadas.models import JornadaTemplate
    from apps.ia.services.jornada import gerar_jornada
    from apps.jornadas.services import aplicar_jornada_ia

    try:
        cliente = Cliente.objects.get(pk=cliente_id)
        diagnostico = Diagnostic.objects.get(pk=diagnostico_id)
    except (Cliente.DoesNotExist, Diagnostic.DoesNotExist):
        return

    # Verificar se já tem jornada ativa
    from apps.jornadas.models import JornadaCliente
    if JornadaCliente.objects.filter(cliente=cliente, status="ativa").exists():
        logger.info(f"Cliente {cliente} já tem jornada ativa, pulando geração")
        return

    templates = JornadaTemplate.objects.filter(is_active=True)
    if not templates.exists():
        logger.warning("Nenhum template de jornada disponível")
        return

    result = gerar_jornada(cliente, diagnostico, templates)

    if result.get("success"):
        aplicar_jornada_ia(cliente, diagnostico, result["data"])
        logger.info(f"Jornada gerada automaticamente para {cliente}")
    else:
        logger.error(f"Falha ao gerar jornada para {cliente}: {result.get('error')}")


@shared_task
def recalibrar_jornada_task(cliente_id, diagnostico_id):
    """Recalibra jornada existente após novo diagnóstico."""
    from apps.clientes.models import Cliente
    from apps.diagnosticos.models import Diagnostic
    from apps.jornadas.models import JornadaCliente
    from apps.ia.services.jornada import recalibrar_jornada
    from apps.jornadas.services import aplicar_recalibracao_ia

    try:
        cliente = Cliente.objects.get(pk=cliente_id)
        diagnostico_atual = Diagnostic.objects.get(pk=diagnostico_id)
    except (Cliente.DoesNotExist, Diagnostic.DoesNotExist):
        return

    jornada = JornadaCliente.objects.filter(
        cliente=cliente, status="ativa"
    ).first()

    if not jornada:
        # Sem jornada ativa, gerar uma nova
        gerar_jornada_automatica.delay(cliente_id, diagnostico_id)
        return

    # Buscar diagnóstico anterior
    diagnostico_anterior = (
        cliente.diagnosticos
        .filter(status="completed")
        .exclude(pk=diagnostico_atual.pk)
        .order_by("-ano", "-mes")
        .first()
    )

    if not diagnostico_anterior:
        return

    result = recalibrar_jornada(cliente, jornada, diagnostico_anterior, diagnostico_atual)

    if result.get("success"):
        aplicar_recalibracao_ia(jornada, result["data"])
        logger.info(f"Jornada recalibrada para {cliente}")
    else:
        logger.error(f"Falha recalibração {cliente}: {result.get('error')}")
