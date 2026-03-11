from celery import shared_task
from django.utils import timezone


@shared_task
def sincronizar_pagamentos_asaas():
    """Diário: puxa pagamentos de subscriptions ativas do Asaas."""
    from apps.core.services.asaas import AsaasClient
    from .models import Contrato, Pagamento
    from datetime import datetime

    contratos = Contrato.objects.filter(
        subscription_status="ativa",
        asaas_subscription_id__gt="",
    )

    asaas = AsaasClient()
    total_criados = 0

    for contrato in contratos:
        result = asaas.listar_pagamentos(
            subscription_id=contrato.asaas_subscription_id,
        )
        if not result or "data" not in result:
            continue

        for pag_data in result["data"]:
            asaas_id = pag_data.get("id")
            if Pagamento.objects.filter(asaas_payment_id=asaas_id).exists():
                # Atualizar status se mudou
                pag = Pagamento.objects.get(asaas_payment_id=asaas_id)
                status_map = {
                    "PENDING": "pendente",
                    "CONFIRMED": "pago",
                    "RECEIVED": "pago",
                    "OVERDUE": "atrasado",
                }
                new_status = status_map.get(pag_data.get("status"))
                if new_status and pag.status != new_status:
                    pag.status = new_status
                    if new_status == "pago":
                        pag.data_pagamento = pag_data.get("paymentDate") or timezone.now().date()
                    pag.save(update_fields=["status", "data_pagamento", "updated_at"])
                continue

            due_date = pag_data.get("dueDate", "")
            try:
                mes_ref = datetime.strptime(due_date, "%Y-%m-%d").date()
            except (ValueError, TypeError):
                mes_ref = timezone.now().date()

            billing_map = {
                "PIX": "pix", "BOLETO": "boleto", "CREDIT_CARD": "cartao",
            }
            status_map = {
                "PENDING": "pendente", "CONFIRMED": "pago",
                "RECEIVED": "pago", "OVERDUE": "atrasado",
            }

            Pagamento.objects.create(
                contrato=contrato,
                mes_referencia=mes_ref,
                valor=pag_data.get("value", contrato.valor),
                status=status_map.get(pag_data.get("status"), "pendente"),
                asaas_payment_id=asaas_id,
                metodo_pagamento=billing_map.get(pag_data.get("billingType"), "manual"),
                external_reference=pag_data.get("externalReference", ""),
            )
            total_criados += 1

    return f"{total_criados} pagamentos sincronizados"


@shared_task
def lembrete_pagamento():
    """Diário: WhatsApp + Email 3 dias antes do vencimento."""
    from datetime import timedelta
    from apps.core.services.evolution import enviar_mensagem
    from apps.core.services.brevo import enviar_email
    from .models import Pagamento

    daqui_3_dias = timezone.now().date() + timedelta(days=3)

    pagamentos = Pagamento.objects.filter(
        status="pendente",
        mes_referencia__day=daqui_3_dias.day,
        mes_referencia__month=daqui_3_dias.month,
        mes_referencia__year=daqui_3_dias.year,
    ).select_related("contrato__cliente")

    enviados = 0
    for pag in pagamentos:
        cliente = pag.contrato.cliente
        texto = (
            f"*Lembrete de Pagamento - 3M Consultoria*\n\n"
            f"Olá! Lembrando que o pagamento de R$ {pag.valor:.2f} "
            f"referente a {pag.mes_referencia:%m/%Y} vence em 3 dias.\n\n"
            f"Qualquer dúvida, entre em contato."
        )

        if cliente.telefone:
            enviar_mensagem(cliente.telefone, texto)
            enviados += 1

        if cliente.email:
            enviar_email(
                cliente.email,
                cliente.empresa,
                f"Lembrete: Pagamento vence em 3 dias - R$ {pag.valor:.2f}",
                f"<p>Olá <strong>{cliente.empresa}</strong>,</p>"
                f"<p>Seu pagamento de <strong>R$ {pag.valor:.2f}</strong> "
                f"referente a {pag.mes_referencia:%m/%Y} vence em 3 dias.</p>"
                f"<p>Qualquer dúvida, entre em contato.</p>"
                f"<p>— 3M Consultoria</p>",
            )

    return f"{enviados} lembretes de pagamento enviados"


@shared_task
def gerar_pagamentos_mensais():
    """1º do mês: gera Pagamento para contratos manuais (sem Asaas)."""
    from .models import Contrato, Pagamento

    hoje = timezone.now().date()
    contratos = Contrato.objects.filter(
        is_active=True,
        subscription_status="nao_integrado",
        data_inicio__lte=hoje,
    ).exclude(data_fim__lt=hoje)

    criados = 0
    for contrato in contratos:
        # Verificar se já existe pagamento deste mês
        existe = Pagamento.objects.filter(
            contrato=contrato,
            mes_referencia__month=hoje.month,
            mes_referencia__year=hoje.year,
        ).exists()

        if not existe:
            Pagamento.objects.create(
                contrato=contrato,
                mes_referencia=hoje.replace(day=contrato.dia_vencimento),
                valor=contrato.valor,
                status="pendente",
            )
            criados += 1

    return f"{criados} pagamentos mensais gerados"
