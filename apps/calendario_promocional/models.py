from django.db import models
from apps.core.models import BaseModel


class DataPromocional(BaseModel):
    """Datas promocionais do Mercado Livre e e-commerce."""

    class Tipo(models.TextChoices):
        OFICIAL_ML = "oficial_ml", "Oficial Mercado Livre"
        ECOMMERCE = "ecommerce", "E-commerce Geral"
        SAZONAL = "sazonal", "Sazonal / Comemorativa"
        CUSTOM = "custom", "Personalizada"

    class Importancia(models.TextChoices):
        CRITICA = "critica", "Crítica (não perder)"
        ALTA = "alta", "Alta"
        MEDIA = "media", "Média"
        BAIXA = "baixa", "Baixa"

    nome = models.CharField("nome", max_length=200)
    tipo = models.CharField("tipo", max_length=20, choices=Tipo.choices)
    importancia = models.CharField(
        "importância", max_length=20, choices=Importancia.choices, default=Importancia.MEDIA
    )
    data_inicio = models.DateField("data início")
    data_fim = models.DateField("data fim")
    inscricao_inicio = models.DateField("início inscrição", null=True, blank=True)
    inscricao_fim = models.DateField("fim inscrição", null=True, blank=True)
    descricao = models.TextField("descrição", blank=True)
    dicas = models.TextField("dicas para o seller", blank=True)
    categorias_foco = models.JSONField(
        "categorias em foco",
        default=list,
        blank=True,
        help_text="Lista de categorias que mais vendem nesta data.",
    )
    cor = models.CharField("cor", max_length=7, default="#FE8103")
    icone = models.CharField("ícone", max_length=50, blank=True)
    link_ml = models.URLField("link ML (inscrição/info)", blank=True)
    antecedencia_preparo_dias = models.PositiveIntegerField(
        "antecedência de preparo (dias)", default=30,
        help_text="Quantos dias antes o seller deve começar a se preparar.",
    )

    class Meta:
        db_table = "calendario_data_promocional"
        verbose_name = "Data Promocional"
        verbose_name_plural = "Datas Promocionais"
        ordering = ["data_inicio"]

    def __str__(self):
        return f"{self.nome} ({self.data_inicio.strftime('%d/%m')})"

    @property
    def is_inscricao_aberta(self):
        from django.utils import timezone
        hoje = timezone.now().date()
        if self.inscricao_inicio and self.inscricao_fim:
            return self.inscricao_inicio <= hoje <= self.inscricao_fim
        return False


class PreparacaoPromocional(BaseModel):
    """Preparação de um cliente para uma data promocional."""

    class Status(models.TextChoices):
        NAO_PARTICIPANDO = "nao_participando", "Não Participando"
        PREPARANDO = "preparando", "Preparando"
        INSCRITO = "inscrito", "Inscrito"
        PRONTO = "pronto", "Pronto"
        PARTICIPANDO = "participando", "Participando"
        CONCLUIDO = "concluido", "Concluído"

    data_promocional = models.ForeignKey(
        DataPromocional, on_delete=models.CASCADE, related_name="preparacoes"
    )
    cliente = models.ForeignKey(
        "clientes.Cliente", on_delete=models.CASCADE, related_name="preparacoes_promocionais"
    )
    consultor = models.ForeignKey(
        "accounts.User", on_delete=models.PROTECT, related_name="preparacoes_promo"
    )
    status = models.CharField(
        "status", max_length=20, choices=Status.choices, default=Status.NAO_PARTICIPANDO
    )
    produtos_selecionados = models.JSONField(
        "produtos selecionados", default=list, blank=True,
        help_text="Lista de produtos que participarão da promoção.",
    )
    desconto_medio = models.DecimalField(
        "desconto médio (%)", max_digits=5, decimal_places=2, default=0
    )
    budget_ads = models.DecimalField(
        "budget Ads (R$)", max_digits=10, decimal_places=2, default=0
    )
    observacoes = models.TextField("observações", blank=True)
    resultado_vendas = models.PositiveIntegerField("vendas no período", default=0)
    resultado_faturamento = models.DecimalField(
        "faturamento (R$)", max_digits=12, decimal_places=2, default=0
    )

    class Meta:
        db_table = "calendario_preparacao"
        verbose_name = "Preparação Promocional"
        verbose_name_plural = "Preparações Promocionais"
        unique_together = ("data_promocional", "cliente")
        ordering = ["-data_promocional__data_inicio"]

    def __str__(self):
        return f"{self.cliente.empresa} → {self.data_promocional.nome}"
