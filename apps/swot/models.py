from django.db import models

from apps.core.models import BaseModel


class AnaliseSwot(BaseModel):
    cliente = models.ForeignKey(
        "clientes.Cliente",
        on_delete=models.CASCADE,
        related_name="analises_swot",
        verbose_name="cliente",
    )
    consultor = models.ForeignKey(
        "accounts.User",
        on_delete=models.PROTECT,
        related_name="analises_swot",
        verbose_name="consultor",
    )
    reuniao = models.ForeignKey(
        "reunioes.Reuniao",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="analises_swot",
        verbose_name="reunião vinculada",
    )

    # Quadrantes SWOT — lista de strings
    forcas = models.JSONField("forças", default=list)
    fraquezas = models.JSONField("fraquezas", default=list)
    oportunidades = models.JSONField("oportunidades", default=list)
    ameacas = models.JSONField("ameaças", default=list)

    # Informações de mercado
    segmento_mercado = models.CharField("segmento de mercado", max_length=200, blank=True)
    publico_alvo = models.CharField("público-alvo", max_length=300, blank=True)
    concorrentes = models.TextField("principais concorrentes", blank=True)
    diferencial = models.TextField("diferencial competitivo", blank=True)
    observacoes_mercado = models.TextField("observações do mercado", blank=True)

    # Produtos principais — [{"nome": "...", "categoria": "...", "participacao": 30}]
    produtos_principais = models.JSONField("produtos principais", default=list)

    # Meta
    data_analise = models.DateField("data da análise")
    observacoes = models.TextField("observações gerais", blank=True)

    class Meta:
        db_table = "analises_swot"
        verbose_name = "Análise SWOT"
        verbose_name_plural = "Análises SWOT"
        ordering = ["-data_analise"]

    def __str__(self):
        return f"SWOT — {self.cliente.empresa} ({self.data_analise})"
