import json
import logging

from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from django.http import HttpResponse
from django.template import Template, Context

from apps.core.decorators import gestor_required
from apps.core.services.asaas import AsaasClient
from apps.core.services.autentique import AutentiqueClient
from .forms import ContratoForm, ContratoTemplateForm, PagamentoForm
from .models import Contrato, ContratoTemplate, Pagamento

logger = logging.getLogger(__name__)


@gestor_required
def listar(request):
    contratos = Contrato.objects.select_related("cliente").filter(is_active=True)
    return render(request, "financeiro/listar.html", {"contratos": contratos})


@gestor_required
def criar_contrato(request):
    if request.method == "POST":
        form = ContratoForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Contrato criado.")
            return redirect("financeiro:listar")
    else:
        form = ContratoForm()
    return render(request, "financeiro/form.html", {
        "form": form,
        "form_title": "Novo Contrato",
        "cancel_url": "/financeiro/",
    })


@gestor_required
def detalhe_contrato(request, pk):
    contrato = get_object_or_404(Contrato.objects.select_related("cliente"), pk=pk)
    pagamentos = contrato.pagamentos.all()
    pag_form = PagamentoForm(initial={"contrato": contrato, "valor": contrato.valor})
    templates_contrato = ContratoTemplate.objects.filter(is_active=True)
    return render(request, "financeiro/detalhe.html", {
        "contrato": contrato,
        "pagamentos": pagamentos,
        "pag_form": pag_form,
        "templates_contrato": templates_contrato,
    })


@gestor_required
def adicionar_pagamento(request, pk):
    contrato = get_object_or_404(Contrato, pk=pk)
    if request.method == "POST":
        form = PagamentoForm(request.POST)
        if form.is_valid():
            pag = form.save(commit=False)
            pag.contrato = contrato
            pag.save()
            messages.success(request, "Pagamento registrado.")
    return redirect("financeiro:detalhe", pk=pk)


@gestor_required
def marcar_pago(request, pk, pag_pk):
    pag = get_object_or_404(Pagamento, pk=pag_pk, contrato_id=pk)
    pag.status = "pago"
    pag.data_pagamento = timezone.now().date()
    pag.save()
    if request.htmx:
        return render(request, "financeiro/_pagamento.html", {"pag": pag})
    return redirect("financeiro:detalhe", pk=pk)


# ── Templates de Contrato ─────────────────────────────────────────────────────


@gestor_required
def config_templates(request):
    """CRUD de templates de contrato."""
    templates = ContratoTemplate.objects.filter(is_active=True)

    if request.method == "POST":
        form = ContratoTemplateForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Template criado.")
            return redirect("financeiro:config_templates")
    else:
        form = ContratoTemplateForm()

    return render(request, "financeiro/config_templates.html", {
        "templates": templates,
        "form": form,
    })


@gestor_required
def editar_template(request, pk):
    tmpl = get_object_or_404(ContratoTemplate, pk=pk)
    if request.method == "POST":
        form = ContratoTemplateForm(request.POST, instance=tmpl)
        if form.is_valid():
            form.save()
            messages.success(request, "Template atualizado.")
            return redirect("financeiro:config_templates")
    else:
        form = ContratoTemplateForm(instance=tmpl)

    return render(request, "financeiro/config_templates.html", {
        "templates": ContratoTemplate.objects.filter(is_active=True),
        "form": form,
        "editando": tmpl,
    })


@gestor_required
@require_POST
def excluir_template(request, pk):
    tmpl = get_object_or_404(ContratoTemplate, pk=pk)
    tmpl.soft_delete()
    messages.success(request, f"Template '{tmpl.nome}' excluído.")
    return redirect("financeiro:config_templates")


@gestor_required
@require_POST
def gerar_contrato_pdf(request, pk):
    """Gera PDF do contrato a partir do template selecionado."""
    contrato = get_object_or_404(Contrato.objects.select_related("cliente"), pk=pk)

    template_id = request.POST.get("template_id")
    if not template_id:
        messages.error(request, "Selecione um template.")
        return redirect("financeiro:detalhe", pk=pk)

    tmpl = get_object_or_404(ContratoTemplate, pk=template_id)
    cliente = contrato.cliente

    # Substituir variáveis no conteúdo
    variaveis = {
        "cliente": cliente.empresa,
        "empresa": cliente.empresa,
        "cpf_cnpj": getattr(cliente, "cnpj", "") or "",
        "valor": f"{contrato.valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
        "plano": contrato.plano,
        "data_inicio": contrato.data_inicio.strftime("%d/%m/%Y") if contrato.data_inicio else "",
        "data_fim": contrato.data_fim.strftime("%d/%m/%Y") if contrato.data_fim else "Indeterminado",
        "dia_vencimento": str(contrato.dia_vencimento),
    }

    conteudo_html = tmpl.conteudo
    for chave, valor in variaveis.items():
        conteudo_html = conteudo_html.replace("{" + chave + "}", valor)

    # Gerar PDF com weasyprint ou xhtml2pdf
    try:
        from xhtml2pdf import pisa
        from io import BytesIO
        from django.core.files.base import ContentFile

        html_completo = f"""
        <!DOCTYPE html>
        <html>
        <head><meta charset="utf-8"><style>
            body {{ font-family: Arial, sans-serif; font-size: 12px; line-height: 1.6; padding: 40px; }}
            h1 {{ font-size: 18px; text-align: center; }}
            h2 {{ font-size: 14px; }}
        </style></head>
        <body>{conteudo_html}</body>
        </html>
        """

        buffer = BytesIO()
        pisa.CreatePDF(html_completo, dest=buffer, encoding="utf-8")
        pdf_bytes = buffer.getvalue()

        filename = f"contrato_{contrato.pk}_{cliente.empresa[:20]}.pdf"
        contrato.pdf_arquivo.save(filename, ContentFile(pdf_bytes), save=False)
        contrato.template = tmpl
        contrato.save(update_fields=["template", "pdf_arquivo"])

        messages.success(request, "PDF do contrato gerado com sucesso!")
    except ImportError:
        messages.error(request, "Biblioteca xhtml2pdf não instalada. Execute: pip install xhtml2pdf")
    except Exception as e:
        logger.exception("Erro ao gerar PDF do contrato %s", contrato.pk)
        messages.error(request, f"Erro ao gerar PDF: {e}")

    return redirect("financeiro:detalhe", pk=pk)


@gestor_required
def preview_contrato(request, pk):
    """Preview do contrato preenchido em HTML."""
    contrato = get_object_or_404(Contrato.objects.select_related("cliente"), pk=pk)
    template_id = request.GET.get("template_id")

    if not template_id:
        return HttpResponse("Selecione um template.", status=400)

    tmpl = get_object_or_404(ContratoTemplate, pk=template_id)
    cliente = contrato.cliente

    variaveis = {
        "cliente": cliente.empresa,
        "empresa": cliente.empresa,
        "cpf_cnpj": getattr(cliente, "cnpj", "") or "",
        "valor": f"{contrato.valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
        "plano": contrato.plano,
        "data_inicio": contrato.data_inicio.strftime("%d/%m/%Y") if contrato.data_inicio else "",
        "data_fim": contrato.data_fim.strftime("%d/%m/%Y") if contrato.data_fim else "Indeterminado",
        "dia_vencimento": str(contrato.dia_vencimento),
    }

    conteudo = tmpl.conteudo
    for chave, valor in variaveis.items():
        conteudo = conteudo.replace("{" + chave + "}", valor)

    return render(request, "financeiro/preview_contrato.html", {
        "contrato": contrato,
        "conteudo": conteudo,
        "template": tmpl,
    })


@gestor_required
@require_POST
def enviar_para_assinatura(request, pk):
    """Envia contrato PDF para assinatura via Autentique."""
    contrato = get_object_or_404(Contrato.objects.select_related("cliente"), pk=pk)

    if not contrato.pdf_arquivo:
        messages.error(request, "Gere o PDF do contrato antes de enviar para assinatura.")
        return redirect("financeiro:detalhe", pk=pk)

    cliente = contrato.cliente
    if not cliente.email:
        messages.error(request, "Cliente não tem email cadastrado. Adicione o email antes de enviar.")
        return redirect("financeiro:detalhe", pk=pk)

    autentique = AutentiqueClient()

    # Ler PDF
    contrato.pdf_arquivo.seek(0)
    pdf_content = contrato.pdf_arquivo.read()
    pdf_file = (
        contrato.pdf_arquivo.name.split("/")[-1],
        pdf_content,
        "application/pdf",
    )

    signatarios = [
        {"email": cliente.email, "name": cliente.empresa, "action": "SIGN"},
    ]

    result = autentique.criar_documento(
        nome=f"Contrato - {cliente.empresa} - {contrato.plano}",
        pdf_bytes=pdf_file,
        signatarios=signatarios,
    )

    if not result or "id" not in result:
        messages.error(request, "Erro ao enviar para Autentique. Verifique a configuração da API.")
        return redirect("financeiro:detalhe", pk=pk)

    contrato.autentique_doc_id = result["id"]
    contrato.status_assinatura = Contrato.StatusAssinatura.ENVIADO
    contrato.save(update_fields=["autentique_doc_id", "status_assinatura"])

    messages.success(request, "Contrato enviado para assinatura digital!")
    return redirect("financeiro:detalhe", pk=pk)


@gestor_required
@require_POST
def verificar_assinatura(request, pk):
    """Verifica status da assinatura no Autentique."""
    contrato = get_object_or_404(Contrato, pk=pk)

    if not contrato.autentique_doc_id:
        messages.warning(request, "Contrato não foi enviado para assinatura.")
        return redirect("financeiro:detalhe", pk=pk)

    autentique = AutentiqueClient()
    if autentique.documento_assinado(contrato.autentique_doc_id):
        contrato.status_assinatura = Contrato.StatusAssinatura.ASSINADO
        contrato.save(update_fields=["status_assinatura"])
        messages.success(request, "Contrato assinado com sucesso!")
    else:
        doc = autentique.consultar_documento(contrato.autentique_doc_id)
        if doc:
            for sig in doc.get("signatures", []):
                if sig.get("rejected"):
                    contrato.status_assinatura = Contrato.StatusAssinatura.RECUSADO
                    contrato.save(update_fields=["status_assinatura"])
                    messages.warning(request, "Contrato foi recusado pelo signatário.")
                    return redirect("financeiro:detalhe", pk=pk)
        messages.info(request, "Assinatura ainda pendente.")

    return redirect("financeiro:detalhe", pk=pk)


# ── Asaas Integration ────────────────────────────────────────────────────────


@gestor_required
@require_POST
def integrar_asaas(request, pk):
    """Cria customer + subscription no Asaas para um contrato."""
    contrato = get_object_or_404(Contrato.objects.select_related("cliente"), pk=pk)
    cliente = contrato.cliente
    asaas = AsaasClient()

    # 1. Criar/reusar customer
    if not contrato.asaas_customer_id:
        result = asaas.criar_customer(
            nome=cliente.empresa,
            cpf_cnpj=cliente.cnpj or "00000000000",
            email=cliente.email or None,
            telefone=cliente.telefone or None,
            external_reference=f"cliente_{cliente.pk}",
        )
        if not result or "id" not in result:
            messages.error(request, "Erro ao criar cliente no Asaas. Verifique a API key.")
            return redirect("financeiro:detalhe", pk=pk)
        contrato.asaas_customer_id = result["id"]

    # 2. Criar subscription
    result = asaas.criar_subscription(
        customer_id=contrato.asaas_customer_id,
        valor=contrato.valor,
        dia_vencimento=contrato.dia_vencimento,
        descricao=f"Consultoria 3M - {cliente.empresa} - {contrato.plano}",
        external_reference=f"contrato_{contrato.pk}",
    )
    if not result or "id" not in result:
        messages.error(request, "Erro ao criar assinatura no Asaas.")
        contrato.save(update_fields=["asaas_customer_id"])
        return redirect("financeiro:detalhe", pk=pk)

    contrato.asaas_subscription_id = result["id"]
    contrato.subscription_status = Contrato.StatusSubscription.ATIVA
    contrato.save(update_fields=[
        "asaas_customer_id", "asaas_subscription_id", "subscription_status",
    ])

    messages.success(request, "Contrato integrado com Asaas! Cobranças serão geradas automaticamente.")
    return redirect("financeiro:detalhe", pk=pk)


@gestor_required
@require_POST
def sincronizar_pagamentos(request, pk):
    """Puxa pagamentos do Asaas e sincroniza com local."""
    contrato = get_object_or_404(Contrato, pk=pk)

    if not contrato.asaas_subscription_id:
        messages.warning(request, "Contrato não integrado com Asaas.")
        return redirect("financeiro:detalhe", pk=pk)

    asaas = AsaasClient()
    result = asaas.listar_pagamentos(subscription_id=contrato.asaas_subscription_id)

    if not result or "data" not in result:
        messages.error(request, "Erro ao buscar pagamentos no Asaas.")
        return redirect("financeiro:detalhe", pk=pk)

    criados = 0
    for pag_data in result["data"]:
        asaas_id = pag_data.get("id")
        if Pagamento.objects.filter(asaas_payment_id=asaas_id).exists():
            continue

        status_map = {
            "PENDING": Pagamento.Status.PENDENTE,
            "CONFIRMED": Pagamento.Status.PAGO,
            "RECEIVED": Pagamento.Status.PAGO,
            "OVERDUE": Pagamento.Status.ATRASADO,
            "REFUNDED": Pagamento.Status.CANCELADO,
            "DELETED": Pagamento.Status.CANCELADO,
        }
        billing_map = {
            "PIX": Pagamento.MetodoPagamento.PIX,
            "BOLETO": Pagamento.MetodoPagamento.BOLETO,
            "CREDIT_CARD": Pagamento.MetodoPagamento.CARTAO,
        }

        from datetime import datetime
        due_date = pag_data.get("dueDate", "")
        try:
            mes_ref = datetime.strptime(due_date, "%Y-%m-%d").date()
        except (ValueError, TypeError):
            mes_ref = timezone.now().date()

        Pagamento.objects.create(
            contrato=contrato,
            mes_referencia=mes_ref,
            valor=pag_data.get("value", contrato.valor),
            status=status_map.get(pag_data.get("status"), Pagamento.Status.PENDENTE),
            asaas_payment_id=asaas_id,
            metodo_pagamento=billing_map.get(
                pag_data.get("billingType"), Pagamento.MetodoPagamento.MANUAL,
            ),
            external_reference=pag_data.get("externalReference", ""),
            data_pagamento=pag_data.get("paymentDate"),
        )
        criados += 1

    messages.success(request, f"{criados} pagamentos sincronizados do Asaas.")
    return redirect("financeiro:detalhe", pk=pk)


@gestor_required
def ver_pix(request, pk, pag_pk):
    """Mostra QR code PIX de um pagamento."""
    pag = get_object_or_404(Pagamento, pk=pag_pk, contrato_id=pk)

    if not pag.pix_code and pag.asaas_payment_id:
        asaas = AsaasClient()
        result = asaas.obter_pix_qrcode(pag.asaas_payment_id)
        if result:
            pag.pix_code = result.get("payload", "")
            pag.pix_qr_code_image = result.get("encodedImage", "")
            pag.save(update_fields=["pix_code", "pix_qr_code_image"])

    return render(request, "financeiro/pix.html", {"pag": pag, "contrato": pag.contrato})


@gestor_required
def ver_boleto(request, pk, pag_pk):
    """Mostra dados do boleto."""
    pag = get_object_or_404(Pagamento, pk=pag_pk, contrato_id=pk)

    if not pag.boleto_linha_digitavel and pag.asaas_payment_id:
        asaas = AsaasClient()
        result = asaas.obter_boleto(pag.asaas_payment_id)
        if result:
            pag.boleto_linha_digitavel = result.get("identificationField", "")
            pag.save(update_fields=["boleto_linha_digitavel"])

        pag_info = asaas.consultar_pagamento(pag.asaas_payment_id)
        if pag_info and pag_info.get("bankSlipUrl"):
            pag.boleto_url = pag_info["bankSlipUrl"]
            pag.save(update_fields=["boleto_url"])

    return render(request, "financeiro/boleto.html", {"pag": pag, "contrato": pag.contrato})


# ── Webhook ──────────────────────────────────────────────────────────────────


@csrf_exempt
@require_POST
def asaas_webhook(request):
    """Recebe webhooks do Asaas para atualizar status de pagamentos."""
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    event = data.get("event", "")
    payment_data = data.get("payment", {})
    asaas_payment_id = payment_data.get("id")
    external_reference = payment_data.get("externalReference", "")

    logger.info("Asaas webhook: event=%s payment=%s", event, asaas_payment_id)

    # Buscar pagamento
    pagamento = None
    if external_reference:
        pagamento = Pagamento.objects.filter(
            external_reference=external_reference
        ).first()
    if not pagamento and asaas_payment_id:
        pagamento = Pagamento.objects.filter(
            asaas_payment_id=asaas_payment_id
        ).first()

    if not pagamento:
        logger.info("Asaas webhook: pagamento não encontrado, ignorando.")
        return JsonResponse({"status": "ignored"})

    status_map = {
        "PAYMENT_CONFIRMED": Pagamento.Status.PAGO,
        "PAYMENT_RECEIVED": Pagamento.Status.PAGO,
        "PAYMENT_OVERDUE": Pagamento.Status.ATRASADO,
        "PAYMENT_REFUNDED": Pagamento.Status.CANCELADO,
        "PAYMENT_DELETED": Pagamento.Status.CANCELADO,
    }

    new_status = status_map.get(event)
    if new_status:
        pagamento.status = new_status
        if new_status == Pagamento.Status.PAGO:
            pagamento.data_pagamento = timezone.now().date()
        pagamento.save(update_fields=["status", "data_pagamento", "updated_at"])
        logger.info(
            "Asaas webhook: pagamento %s atualizado para %s",
            pagamento.pk, new_status,
        )

    return JsonResponse({"status": "ok"})
