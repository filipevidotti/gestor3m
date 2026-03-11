from django.db import models
from apps.core.models import BaseModel


class ContratoTemplate(BaseModel):
    """Template de contrato com variáveis para preenchimento automático."""

    nome = models.CharField("nome do template", max_length=200)
    conteudo = models.TextField(
        "conteúdo HTML",
        help_text=(
            "Use variáveis: {cliente}, {empresa}, {cpf_cnpj}, {valor}, "
            "{plano}, {data_inicio}, {data_fim}, {dia_vencimento}"
        ),
    )

    class Meta:
        db_table = "contrato_templates"
        verbose_name = "Template de Contrato"
        verbose_name_plural = "Templates de Contrato"

    def __str__(self):
        return self.nome


class Contrato(BaseModel):
    class StatusSubscription(models.TextChoices):
        NAO_INTEGRADO = "nao_integrado", "Não Integrado"
        ATIVA = "ativa", "Ativa"
        INATIVA = "inativa", "Inativa"
        EXPIRADA = "expirada", "Expirada"

    class StatusAssinatura(models.TextChoices):
        RASCUNHO = "rascunho", "Rascunho"
        ENVIADO = "enviado", "Enviado para assinatura"
        ASSINADO = "assinado", "Assinado"
        RECUSADO = "recusado", "Recusado"

    cliente = models.ForeignKey(
        "clientes.Cliente", on_delete=models.CASCADE, related_name="contratos"
    )
    plano = models.CharField("plano", max_length=100)
    valor = models.DecimalField("valor mensal", max_digits=10, decimal_places=2)
    dia_vencimento = models.PositiveIntegerField("dia do vencimento", default=10)
    data_inicio = models.DateField("início do contrato")
    data_fim = models.DateField("fim do contrato", null=True, blank=True)
    observacoes = models.TextField("observações", blank=True)

    # Template e assinatura digital
    template = models.ForeignKey(
        ContratoTemplate, on_delete=models.SET_NULL, null=True, blank=True,
        verbose_name="template do contrato",
    )
    status_assinatura = models.CharField(
        "status assinatura", max_length=20,
        choices=StatusAssinatura.choices, default=StatusAssinatura.RASCUNHO,
    )
    autentique_doc_id = models.CharField(
        "Autentique Document ID", max_length=100, blank=True,
    )
    pdf_arquivo = models.FileField(
        "PDF do contrato", upload_to="contratos/", blank=True,
    )

    # Asaas
    asaas_customer_id = models.CharField(
        "Asaas Customer ID", max_length=100, blank=True,
    )
    asaas_subscription_id = models.CharField(
        "Asaas Subscription ID", max_length=100, blank=True,
    )
    subscription_status = models.CharField(
        "status assinatura", max_length=20,
        choices=StatusSubscription.choices,
        default=StatusSubscription.NAO_INTEGRADO,
    )

    class Meta:
        db_table = "contratos"
        verbose_name = "Contrato"
        verbose_name_plural = "Contratos"

    def __str__(self):
        return f"{self.cliente} - {self.plano} (R$ {self.valor})"


class Pagamento(BaseModel):
    class Status(models.TextChoices):
        PAGO = "pago", "Pago"
        ATRASADO = "atrasado", "Atrasado"
        CANCELADO = "cancelado", "Cancelado"
        PENDENTE = "pendente", "Pendente"

    class MetodoPagamento(models.TextChoices):
        MANUAL = "manual", "Manual"
        PIX = "pix", "PIX"
        BOLETO = "boleto", "Boleto"
        CARTAO = "cartao", "Cartão de Crédito"

    contrato = models.ForeignKey(
        Contrato, on_delete=models.CASCADE, related_name="pagamentos"
    )
    mes_referencia = models.DateField("mês referência")
    valor = models.DecimalField("valor", max_digits=10, decimal_places=2)
    status = models.CharField(
        "status", max_length=20, choices=Status.choices, default=Status.PENDENTE
    )
    data_pagamento = models.DateField("data do pagamento", null=True, blank=True)

    # Asaas
    asaas_payment_id = models.CharField(
        "Asaas Payment ID", max_length=100, blank=True,
    )
    metodo_pagamento = models.CharField(
        "método", max_length=20,
        choices=MetodoPagamento.choices, default=MetodoPagamento.MANUAL,
    )
    pix_code = models.TextField("código PIX copia-e-cola", blank=True)
    pix_qr_code_image = models.TextField("QR Code PIX (base64)", blank=True)
    boleto_url = models.URLField("URL do boleto", max_length=500, blank=True)
    boleto_linha_digitavel = models.CharField(
        "linha digitável", max_length=100, blank=True,
    )
    external_reference = models.CharField(
        "referência externa", max_length=100, blank=True, db_index=True,
    )

    class Meta:
        db_table = "pagamentos"
        verbose_name = "Pagamento"
        verbose_name_plural = "Pagamentos"
        ordering = ["-mes_referencia"]

    def __str__(self):
        return f"{self.contrato.cliente} - {self.mes_referencia:%m/%Y} ({self.get_status_display()})"
