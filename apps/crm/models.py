from django.db import models

from apps.core.models import BaseModel, ActiveManager


class EtapaCRM(BaseModel):
    """Etapas do funil comercial (pré-venda)."""

    nome = models.CharField("nome", max_length=100)
    descricao = models.CharField("descrição", max_length=200, blank=True)
    cor = models.CharField("cor", max_length=7, default="#3b82f6")
    ordem = models.PositiveIntegerField("ordem", default=0)
    is_ganho = models.BooleanField("é etapa de ganho?", default=False)
    is_perdido = models.BooleanField("é etapa de perda?", default=False)

    class Meta:
        db_table = "crm_etapas"
        verbose_name = "Etapa CRM"
        verbose_name_plural = "Etapas CRM"
        ordering = ["ordem"]

    def __str__(self):
        return self.nome


class Lead(BaseModel):
    """Lead/prospect do CRM pré-venda."""

    class Origem(models.TextChoices):
        INDICACAO = "indicacao", "Indicação"
        SITE = "site", "Site"
        REDES_SOCIAIS = "redes_sociais", "Redes Sociais"
        EVENTO = "evento", "Evento"
        OUTRO = "outro", "Outro"

    nome = models.CharField("nome do responsável", max_length=200)
    empresa = models.CharField("empresa/loja", max_length=200, blank=True)
    telefone = models.CharField("telefone", max_length=20, blank=True)
    email = models.EmailField("e-mail", blank=True)
    nicho = models.CharField("nicho", max_length=100, blank=True)
    origem = models.CharField(
        "origem", max_length=20, choices=Origem.choices, default=Origem.OUTRO,
    )
    observacoes = models.TextField("observações", blank=True)
    responsavel = models.ForeignKey(
        "accounts.User", on_delete=models.PROTECT,
        related_name="leads", verbose_name="responsável",
    )
    cliente = models.OneToOneField(
        "clientes.Cliente", on_delete=models.SET_NULL,
        null=True, blank=True, related_name="lead_origem",
        verbose_name="cliente convertido",
    )

    objects = ActiveManager()
    all_objects = models.Manager()

    class Meta:
        db_table = "crm_leads"
        verbose_name = "Lead"
        verbose_name_plural = "Leads"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.nome} ({self.empresa})" if self.empresa else self.nome

    @property
    def convertido(self):
        return self.cliente_id is not None


class Oportunidade(BaseModel):
    """Oportunidade de negócio vinculada a um lead."""

    lead = models.ForeignKey(
        Lead, on_delete=models.CASCADE, related_name="oportunidades",
    )
    titulo = models.CharField("título", max_length=200)
    valor_estimado = models.DecimalField(
        "valor estimado", max_digits=10, decimal_places=2, default=0,
    )
    etapa = models.ForeignKey(
        EtapaCRM, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="oportunidades", verbose_name="etapa",
    )
    responsavel = models.ForeignKey(
        "accounts.User", on_delete=models.PROTECT,
        related_name="oportunidades_crm", verbose_name="responsável",
    )
    previsao_fechamento = models.DateField(
        "previsão de fechamento", null=True, blank=True,
    )
    motivo_perda = models.TextField("motivo da perda", blank=True)
    proposta = models.ForeignKey(
        "propostas.Proposta", on_delete=models.SET_NULL,
        null=True, blank=True, related_name="oportunidades_crm",
    )

    objects = ActiveManager()
    all_objects = models.Manager()

    class Meta:
        db_table = "crm_oportunidades"
        verbose_name = "Oportunidade"
        verbose_name_plural = "Oportunidades"
        ordering = ["-created_at"]

    def __str__(self):
        return self.titulo


class AtividadeCRM(BaseModel):
    """Registro de atividade no CRM (timeline)."""

    class Tipo(models.TextChoices):
        NOTA = "nota", "Nota"
        LIGACAO = "ligacao", "Ligação"
        EMAIL = "email", "E-mail"
        REUNIAO = "reuniao", "Reunião"
        WHATSAPP = "whatsapp", "WhatsApp"
        MUDANCA_ETAPA = "mudanca_etapa", "Mudança de Etapa"

    lead = models.ForeignKey(
        Lead, on_delete=models.CASCADE, related_name="atividades_crm",
    )
    oportunidade = models.ForeignKey(
        Oportunidade, on_delete=models.CASCADE,
        null=True, blank=True, related_name="atividades_crm",
    )
    tipo = models.CharField(
        "tipo", max_length=20, choices=Tipo.choices, default=Tipo.NOTA,
    )
    descricao = models.TextField("descrição")
    autor = models.ForeignKey(
        "accounts.User", on_delete=models.PROTECT, verbose_name="autor",
    )

    class Meta:
        db_table = "crm_atividades"
        verbose_name = "Atividade CRM"
        verbose_name_plural = "Atividades CRM"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.get_tipo_display()} - {self.lead}"


class LembreteCRM(BaseModel):
    """Lembrete agendado para follow-up."""

    lead = models.ForeignKey(
        Lead, on_delete=models.CASCADE, related_name="lembretes",
    )
    responsavel = models.ForeignKey(
        "accounts.User", on_delete=models.CASCADE,
        related_name="lembretes_crm",
    )
    data_hora = models.DateTimeField("data/hora do lembrete")
    descricao = models.CharField("descrição", max_length=300)
    enviado = models.BooleanField("enviado?", default=False)
    enviar_whatsapp = models.BooleanField("enviar WhatsApp?", default=True)
    enviar_email = models.BooleanField("enviar e-mail?", default=True)

    class Meta:
        db_table = "crm_lembretes"
        verbose_name = "Lembrete"
        verbose_name_plural = "Lembretes"
        ordering = ["data_hora"]

    def __str__(self):
        return f"{self.descricao} - {self.data_hora:%d/%m %H:%M}"
