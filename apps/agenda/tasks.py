import logging
from datetime import timedelta

from celery import shared_task
from django.utils import timezone

logger = logging.getLogger(__name__)


def _montar_mensagem_cliente(agendamento):
    """Monta texto de confirmação de reunião para o cliente."""
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


def _montar_mensagem_consultor(agendamento):
    """Monta texto de lembrete para o consultor."""
    data = agendamento.data_hora
    dia_fmt = data.strftime("%d/%m/%Y")
    hora_fmt = data.strftime("%H:%M")

    texto = (
        f"📋 *Lembrete de Reunião*\n\n"
        f"Você tem uma reunião agendada:\n\n"
        f"👤 *Cliente:* {agendamento.nome_cliente}\n"
        f"📅 *Data:* {dia_fmt}\n"
        f"🕐 *Horário:* {hora_fmt}\n"
        f"⏱ *Duração:* {agendamento.duracao} minutos\n"
    )

    if agendamento.observacao:
        texto += f"📝 *Assunto:* {agendamento.observacao}\n"

    if agendamento.telefone_cliente:
        texto += f"📱 *Telefone:* {agendamento.telefone_cliente}\n"

    texto += f"\n_3M Consultoria_"
    return texto


def _montar_mensagem_grupo(agendamento):
    """Monta texto para enviar no grupo WhatsApp do cliente."""
    data = agendamento.data_hora
    dia_fmt = data.strftime("%d/%m/%Y")
    hora_fmt = data.strftime("%H:%M")
    consultor_nome = agendamento.consultor.get_full_name()

    texto = (
        f"📅 *Reunião Agendada*\n\n"
        f"🕐 *Data/Hora:* {dia_fmt} às {hora_fmt}\n"
        f"⏱ *Duração:* {agendamento.duracao} minutos\n"
        f"👤 *Consultor:* {consultor_nome}\n"
        f"🏢 *Cliente:* {agendamento.nome_cliente}\n"
    )

    if agendamento.observacao:
        texto += f"📝 *Assunto:* {agendamento.observacao}\n"

    texto += (
        f"\nPor favor, confirmem a presença! ✅\n\n"
        f"_3M Consultoria_"
    )
    return texto


def _montar_lembrete_cliente(agendamento):
    """Monta texto de lembrete (2h antes) para o cliente."""
    hora_fmt = agendamento.data_hora.strftime("%H:%M")
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


def _montar_lembrete_consultor(agendamento):
    """Monta texto de lembrete (2h antes) para o consultor."""
    hora_fmt = agendamento.data_hora.strftime("%H:%M")

    texto = (
        f"⏰ *Lembrete*\n\n"
        f"Sua reunião com *{agendamento.nome_cliente}* é às *{hora_fmt}*.\n"
        f"Duração: {agendamento.duracao} minutos.\n"
    )

    if agendamento.telefone_cliente:
        texto += f"📱 Telefone: {agendamento.telefone_cliente}\n"

    if agendamento.observacao:
        texto += f"📝 Assunto: {agendamento.observacao}\n"

    texto += f"\n_3M Consultoria_"
    return texto


def _enviar_para_todos(agendamento, msg_cliente, msg_consultor, msg_grupo):
    """Envia mensagem para cliente, consultor e grupo WhatsApp do cliente."""
    from apps.core.models import GrupoWhatsApp
    from apps.core.services.uazapi import enviar_mensagem, enviar_mensagem_grupo

    enviados = 0

    # 1. Enviar para o telefone do cliente
    if agendamento.telefone_cliente and msg_cliente:
        if enviar_mensagem(agendamento.telefone_cliente, msg_cliente):
            enviados += 1
            logger.info("Msg enviada para cliente %s", agendamento.nome_cliente)

    # 2. Enviar para o consultor
    consultor = agendamento.consultor
    if consultor.telefone and msg_consultor:
        if enviar_mensagem(consultor.telefone, msg_consultor):
            enviados += 1
            logger.info("Msg enviada para consultor %s", consultor.get_full_name())

    # 3. Enviar para o grupo WhatsApp do cliente (se vinculado)
    if agendamento.cliente_id and msg_grupo:
        grupos = GrupoWhatsApp.objects.filter(
            cliente_id=agendamento.cliente_id, is_active=True
        )
        for grupo in grupos:
            if grupo.group_id:
                if enviar_mensagem_grupo(grupo.group_id, msg_grupo):
                    enviados += 1
                    logger.info("Msg enviada para grupo %s", grupo.nome)

    return enviados


@shared_task
def enviar_lembrete_agendamentos():
    """Envia lembrete 2h antes: cliente + consultor + grupo WhatsApp."""
    from .models import Agendamento

    agora = timezone.now()
    limite = agora + timedelta(hours=2, minutes=10)

    agendamentos = Agendamento.objects.filter(
        status=Agendamento.Status.CONFIRMADO,
        lembrete_enviado=False,
        data_hora__gt=agora,
        data_hora__lte=limite,
    ).select_related("consultor", "cliente")

    count = 0
    for ag in agendamentos:
        msg_cliente = _montar_lembrete_cliente(ag)
        msg_consultor = _montar_lembrete_consultor(ag)
        msg_grupo = _montar_mensagem_grupo(ag)

        enviados = _enviar_para_todos(ag, msg_cliente, msg_consultor, msg_grupo)

        if enviados > 0:
            ag.lembrete_enviado = True
            ag.save(update_fields=["lembrete_enviado", "updated_at"])
            count += 1
            logger.info("Lembrete enviado (agendamento %d): %d destinos", ag.pk, enviados)

    logger.info("enviar_lembrete_agendamentos: %d agendamentos notificados", count)
    return count


@shared_task
def enviar_confirmacao_agendamento(agendamento_id):
    """Envia confirmação manual: cliente + consultor + grupo WhatsApp."""
    from .models import Agendamento

    try:
        ag = Agendamento.objects.select_related("consultor", "cliente").get(pk=agendamento_id)
    except Agendamento.DoesNotExist:
        logger.error("Agendamento %d não encontrado", agendamento_id)
        return False

    msg_cliente = _montar_mensagem_cliente(ag)
    msg_consultor = _montar_mensagem_consultor(ag)
    msg_grupo = _montar_mensagem_grupo(ag)

    enviados = _enviar_para_todos(ag, msg_cliente, msg_consultor, msg_grupo)

    if enviados > 0:
        ag.mensagem_enviada_em = timezone.now()
        ag.save(update_fields=["mensagem_enviada_em", "updated_at"])
        logger.info("Confirmação enviada (agendamento %d): %d destinos", ag.pk, enviados)

    return enviados > 0
