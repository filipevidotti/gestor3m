from celery import shared_task
from django.utils import timezone


@shared_task
def enviar_lembretes_crm():
    """Envia lembretes CRM pendentes via WhatsApp + Email. Executar a cada 15 min."""
    from apps.core.services.evolution import enviar_mensagem
    from apps.core.services.brevo import enviar_email
    from .models import LembreteCRM

    agora = timezone.now()
    lembretes = LembreteCRM.objects.filter(
        enviado=False,
        data_hora__lte=agora,
    ).select_related("lead", "responsavel")

    enviados = 0
    for lem in lembretes:
        texto = (
            f"*Lembrete CRM*\n"
            f"Lead: {lem.lead.nome}\n"
            f"{lem.descricao}"
        )

        if lem.enviar_whatsapp and lem.responsavel.telefone:
            enviar_mensagem(lem.responsavel.telefone, texto)

        if lem.enviar_email and lem.responsavel.email:
            enviar_email(
                lem.responsavel.email,
                lem.responsavel.get_full_name(),
                f"Lembrete CRM: {lem.lead.nome}",
                f"<p><strong>Lead:</strong> {lem.lead.nome}</p>"
                f"<p>{lem.descricao}</p>",
            )

        lem.enviado = True
        lem.save(update_fields=["enviado"])
        enviados += 1

    return f"{enviados} lembretes enviados"


@shared_task
def lembrete_reuniao_lead():
    """Envia lembrete de reunião com lead amanhã. Executar diário às 18h."""
    from datetime import timedelta
    from apps.core.services.evolution import enviar_mensagem
    from apps.agenda.models import Agendamento

    amanha = timezone.now().date() + timedelta(days=1)
    agendamentos = Agendamento.objects.filter(
        data_hora__date=amanha,
        status="confirmado",
        observacao__icontains="Reunião comercial",
    ).select_related("consultor")

    enviados = 0
    for ag in agendamentos:
        if ag.consultor.telefone:
            texto = (
                f"*Lembrete de Reunião Comercial*\n"
                f"Amanhã às {ag.data_hora:%H:%M}\n"
                f"Cliente: {ag.nome_cliente}\n"
                f"Duração: {ag.duracao} min"
            )
            enviar_mensagem(ag.consultor.telefone, texto)
            enviados += 1

        if ag.telefone_cliente:
            texto_cliente = (
                f"Olá {ag.nome_cliente}! Lembrando da nossa reunião "
                f"amanhã às {ag.data_hora:%H:%M}. "
                f"Até lá! 🤝\n\n"
                f"— 3M Consultoria"
            )
            enviar_mensagem(ag.telefone_cliente, texto_cliente)

    return f"{enviados} lembretes de reunião enviados"
