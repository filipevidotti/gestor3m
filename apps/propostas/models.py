import uuid

from django.db import models

from apps.core.models import BaseModel


class Servico(BaseModel):
    """Catálogo de serviços oferecidos pela 3M Consultoria."""

    nome = models.CharField("nome", max_length=200)
    descricao = models.TextField("descrição", blank=True)
    icone = models.CharField("ícone", max_length=50, blank=True, help_text="Classe CSS do ícone")
    preco_sugerido = models.DecimalField(
        "preço sugerido", max_digits=10, decimal_places=2, null=True, blank=True,
    )
    ordem = models.PositiveIntegerField("ordem", default=0)

    class Meta:
        db_table = "propostas_servicos"
        verbose_name = "Serviço"
        verbose_name_plural = "Serviços"
        ordering = ["ordem", "nome"]

    def __str__(self):
        return self.nome


class Proposta(BaseModel):
    """Proposta comercial com IA."""

    class TipoSeller(models.TextChoices):
        INICIANTE = "iniciante", "Iniciante"
        ESTRUTURANDO = "estruturando", "Estruturando"
        ESCALANDO = "escalando", "Escalando"
        AVANCADO = "avancado", "Operação Avançada"
        INDUSTRIA = "industria", "Indústria"
        DISTRIBUIDOR = "distribuidor", "Distribuidor"

    class Marketplace(models.TextChoices):
        MERCADO_LIVRE = "mercado_livre", "Mercado Livre"
        SHOPEE = "shopee", "Shopee"
        AMAZON = "amazon", "Amazon"
        MULTICANAL = "multicanal", "Multicanal"

    class Status(models.TextChoices):
        RASCUNHO = "rascunho", "Rascunho"
        QUESTIONARIO = "questionario", "Questionário"
        CALCULANDO = "calculando", "Calculando"
        GERANDO_IA = "gerando_ia", "Gerando IA"
        REVISAO = "revisao", "Em Revisão"
        ENVIADO = "enviado", "Enviado"
        ACEITO = "aceito", "Aceito"
        RECUSADO = "recusado", "Recusado"
        EXPIRADO = "expirado", "Expirado"

    # Vínculo — cliente existente OU lead
    cliente = models.ForeignKey(
        "clientes.Cliente",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="propostas",
        verbose_name="cliente existente",
    )
    lead_nome = models.CharField("nome do responsável", max_length=200, blank=True)
    lead_loja = models.CharField("nome da loja", max_length=200, blank=True)
    lead_email = models.EmailField("e-mail", blank=True)
    lead_telefone = models.CharField("telefone", max_length=20, blank=True)

    # Meta
    consultor = models.ForeignKey(
        "accounts.User",
        on_delete=models.PROTECT,
        related_name="propostas",
        verbose_name="consultor",
    )
    tipo_seller = models.CharField(
        "tipo de seller", max_length=20, choices=TipoSeller.choices,
    )
    marketplace = models.CharField(
        "marketplace principal", max_length=20, choices=Marketplace.choices,
        default=Marketplace.MERCADO_LIVRE,
    )
    status = models.CharField(
        "status", max_length=20, choices=Status.choices, default=Status.RASCUNHO,
    )
    passo_atual = models.PositiveIntegerField("passo atual", default=1)

    # Token público
    token = models.UUIDField("token público", unique=True, default=uuid.uuid4, editable=False)
    data_expiracao = models.DateField("data de expiração", null=True, blank=True)

    # Respostas do questionário (10 blocos)
    respostas = models.JSONField("respostas", default=dict)

    # Métricas calculadas
    metricas = models.JSONField("métricas", default=dict)

    # Textos IA
    diagnostico_ia = models.TextField("diagnóstico IA", blank=True)
    proposicao_valor = models.TextField("proposição de valor", blank=True)
    proposta_comercial = models.TextField("proposta comercial", blank=True)

    # Investimento
    valor_setup = models.DecimalField(
        "valor de setup", max_digits=10, decimal_places=2, default=0,
    )
    valor_mensalidade = models.DecimalField(
        "mensalidade", max_digits=10, decimal_places=2, default=0,
    )
    condicoes_especiais = models.TextField("condições especiais", blank=True)

    # Tracking
    visualizacoes = models.PositiveIntegerField("visualizações", default=0)
    data_envio = models.DateTimeField("data de envio", null=True, blank=True)
    data_resposta = models.DateTimeField("data da resposta", null=True, blank=True)
    motivo_recusa = models.TextField("motivo da recusa", blank=True)

    class Meta:
        db_table = "propostas"
        verbose_name = "Proposta"
        verbose_name_plural = "Propostas"
        ordering = ["-created_at"]

    def __str__(self):
        nome = self.cliente.empresa if self.cliente else self.lead_loja or self.lead_nome
        return f"Proposta — {nome} ({self.get_status_display()})"

    @property
    def nome_display(self):
        if self.cliente:
            return self.cliente.empresa
        return self.lead_loja or self.lead_nome

    @property
    def email_display(self):
        if self.cliente:
            return self.cliente.email
        return self.lead_email

    @property
    def expirada(self):
        from django.utils import timezone
        if self.data_expiracao:
            return timezone.now().date() > self.data_expiracao
        return False


class PropostaServico(BaseModel):
    """Serviço incluído em uma proposta."""

    proposta = models.ForeignKey(
        Proposta, on_delete=models.CASCADE, related_name="servicos_incluidos",
    )
    servico = models.ForeignKey(
        Servico, on_delete=models.PROTECT, related_name="propostas_servico",
    )
    valor = models.DecimalField("valor", max_digits=10, decimal_places=2, default=0)
    descricao_custom = models.TextField("descrição customizada", blank=True)
    ordem = models.PositiveIntegerField("ordem", default=0)

    class Meta:
        db_table = "propostas_servicos_incluidos"
        verbose_name = "Serviço da Proposta"
        verbose_name_plural = "Serviços da Proposta"
        ordering = ["ordem"]

    def __str__(self):
        return f"{self.servico.nome} — {self.proposta}"


class PropostaVisualizacao(models.Model):
    """Tracking de acesso ao link público."""

    proposta = models.ForeignKey(
        Proposta, on_delete=models.CASCADE, related_name="historico_visualizacoes",
    )
    ip = models.GenericIPAddressField("IP")
    user_agent = models.CharField("user agent", max_length=500, blank=True)
    data = models.DateTimeField("data", auto_now_add=True)

    class Meta:
        db_table = "propostas_visualizacoes"
        verbose_name = "Visualização"
        verbose_name_plural = "Visualizações"
        ordering = ["-data"]
