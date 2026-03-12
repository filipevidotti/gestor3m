import logging
from datetime import timedelta

from celery import shared_task
from django.utils import timezone

logger = logging.getLogger(__name__)


def _montar_mensagem_confirmacao(agendamento):
    """Monta texto de confirmação de reunião para WhatsApp."""
    data = agendamento.data_hora
    dia_fmt = data.strftime("%d/%m/%Y")
    hora_fmt = data.strftime("%H:%M")
    consultor_nome = agendamento.consultor.get_full_name()

    texto = (
        f"Olá, {agendamento.nome_cliente}! 👋\n\n"
        f"Confirmação de reunião:\n\n"
        f"📅 *Data:* {dia_fmt}\n"
        f"🕐 *Horário:* {hora_fmt}\n"
        f"⏱ *Duração:* {agendamento.duracao} minutos\n"
        f"👤 *Consultor:* {consultor_nome}\n"
    )

    if agendamento.observacao:
        texto += f"📝 *Assunto:* {agendamento.observacao}\n"

    texto += (
        f"\nPor favor, confirme sua presença respondendo esta mensagem.\n\n"
        f"_3M Consultoria_"
    )
    return texto


def _montar_mensagem_lembrete(agendamento):
    """Monta texto de lembrete (2h antes) para WhatsApp."""
    data = agendamento.data_hora
    hora_fmt = data.strftime("%H:%M")
    consultor_nome = agendamento.consultor.get_full_name()

    texto = (
        f"⏰ *Lembrete de Reunião*\n\n"
        f"Olá, {agendamento.nome_cliente}!\n\n"
        f"Sua reunião com *{consultor_nome}* é daqui a pouco, às *{hora_fmt}*.\n"
        f"Duração: {agendamento.duracao} minutos.\n"
    )

    if agendamento.observacao:
        texto += f"Assunto: {agendamento.observacao}\n"

    texto += f"\nAté logo! 🚀\n_3M Consultoria_"
    return texto


@shared_task
def enviar_lembrete_agendamentos():
    """Envia lembrete WhatsApp 2h antes da reunião para agendamentos confirmados."""
    from apps.core.services.uazapi import enviar_mensagem

    from .models import Agendamento

    agora = timezone.now()
    limite = agora + timedelta(hours=2, minutes=10)

    agendamentos = Agendamento.objects.filter(
        status=Agendamento.Status.CONFIRMADO,
        lembrete_enviado=False,
        data_hora__gt=agora,
        data_hora__lte=limite,
    )

    count = 0
    for ag in agendamentos:
        if not ag.telefone_cliente:
            continue

        texto = _montar_mensagem_lembrete(ag)
        if enviar_mensagem(ag.telefone_cliente, texto):
            ag.lembrete_enviado = True
            ag.save(update_fields=["lembrete_enviado", "updated_at"])
            count += 1
            logger.info("Lembrete enviado para %s (agendamento %d)", ag.nome_cliente, ag.pk)

    logger.info("enviar_lembrete_agendamentos: %d lembretes enviados", count)
    return count


@shared_task
def enviar_confirmacao_agendamento(agendamento_id):
    """Envia mensagem de confirmação para um agendamento específico."""
    from apps.core.services.uazapi import enviar_mensagem

    from .models import Agendamento

    try:
        ag = Agendamento.objects.get(pk=agendamento_id)
    except Agendamento.DoesNotExist:
        logger.error("Agendamento %d não encontrado", agendamento_id)
        return False

    if not ag.telefone_cliente:
        logger.warning("Agendamento %d sem telefone", agendamento_id)
        return False

    texto = _montar_mensagem_confirmacao(ag)
    sucesso = enviar_mensagem(ag.telefone_cliente, texto)

    if sucesso:
        ag.mensagem_enviada_em = timezone.now()
        ag.save(update_fields=["mensagem_enviada_em", "updated_at"])
        logger.info("Confirmação enviada para %s (agendamento %d)", ag.nome_cliente, ag.pk)

    return sucesso
