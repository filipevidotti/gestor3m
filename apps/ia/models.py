from django.db import models

from apps.core.models import BaseModel, ActiveManager


class InsightIA(BaseModel):
    """Insight gerado pela IA para um consultor sobre um cliente."""

    class Tipo(models.TextChoices):
        ALERTA = "alerta", "Alerta"
        SUGESTAO = "sugestao", "Sugestão"
        ELOGIO = "elogio", "Elogio"
        RISCO = "risco", "Risco"

    class Prioridade(models.TextChoices):
        BAIXA = "baixa", "Baixa"
        MEDIA = "media", "Média"
        ALTA = "alta", "Alta"
        CRITICA = "critica", "Crítica"

    consultor = models.ForeignKey(
        "accounts.User",
        on_delete=models.CASCADE,
        related_name="insights_ia",
        verbose_name="consultor",
    )
    cliente = models.ForeignKey(
        "clientes.Cliente",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="insights_ia",
        verbose_name="cliente",
    )
    tipo = models.CharField("tipo", max_length=20, choices=Tipo.choices)
    prioridade = models.CharField(
        "prioridade", max_length=20, choices=Prioridade.choices, default=Prioridade.MEDIA,
    )
    titulo = models.CharField("título", max_length=300)
    descricao = models.TextField("descrição")
    acao_sugerida = models.CharField("ação sugerida", max_length=300, blank=True)
    url_acao = models.CharField("URL da ação", max_length=500, blank=True)
    lido = models.BooleanField("lido", default=False)
    data_expiracao = models.DateField("expira em", null=True, blank=True)

    objects = ActiveManager()
    all_objects = models.Manager()

    class Meta:
        db_table = "ia_insights"
        verbose_name = "Insight IA"
        verbose_name_plural = "Insights IA"
        ordering = ["-created_at"]

    def __str__(self):
        return f"[{self.get_tipo_display()}] {self.titulo}"


class HistoricoAnalise(BaseModel):
    """Registro de cada análise feita pela IA."""

    class TipoAnalise(models.TextChoices):
        JORNADA = "jornada", "Geração de Jornada"
        RECALIBRACAO = "recalibracao", "Recalibração de Jornada"
        REUNIAO = "reuniao", "Análise de Reunião"
        INSIGHT = "insight", "Geração de Insights"
        DIAGNOSTICO = "diagnostico", "Análise de Diagnóstico"

    tipo = models.CharField("tipo", max_length=30, choices=TipoAnalise.choices)
    cliente = models.ForeignKey(
        "clientes.Cliente",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="analises_ia",
    )
    consultor = models.ForeignKey(
        "accounts.User",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="analises_ia",
    )
    provider = models.CharField("provider", max_length=50, blank=True)
    modelo = models.CharField("modelo", max_length=100, blank=True)
    prompt_resumo = models.TextField("resumo do prompt", blank=True)
    resposta_resumo = models.TextField("resumo da resposta", blank=True)
    resposta_json = models.JSONField("resposta completa", default=dict, blank=True)
    tokens_input = models.PositiveIntegerField("tokens input", default=0)
    tokens_output = models.PositiveIntegerField("tokens output", default=0)
    custo_estimado = models.DecimalField(
        "custo estimado (USD)", max_digits=8, decimal_places=4, default=0,
    )
    duracao_ms = models.PositiveIntegerField("duração (ms)", default=0)
    sucesso = models.BooleanField("sucesso", default=True)
    erro = models.TextField("erro", blank=True)

    class Meta:
        db_table = "ia_historico_analises"
        verbose_name = "Histórico de Análise IA"
        verbose_name_plural = "Histórico de Análises IA"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.get_tipo_display()} - {self.created_at:%d/%m/%Y %H:%M}"
