from django.db import models

from apps.core.models import BaseModel


class RelatorioMensal(BaseModel):
    """Relatório mensal gerado automaticamente por cliente."""
    cliente = models.ForeignKey(
        "clientes.Cliente", on_delete=models.CASCADE, related_name="relatorios_mensais",
    )
    mes = models.PositiveIntegerField("mês")
    ano = models.PositiveIntegerField("ano")
    arquivo = models.FileField("PDF", upload_to="relatorios/%Y/%m/", blank=True)
    dados = models.JSONField("dados do relatório", default=dict, blank=True)
    enviado = models.BooleanField("enviado", default=False)
    enviado_em = models.DateTimeField("enviado em", null=True, blank=True)

    class Meta:
        db_table = "relatorios_mensais"
        verbose_name = "Relatório Mensal"
        verbose_name_plural = "Relatórios Mensais"
        unique_together = ["cliente", "mes", "ano"]
        ordering = ["-ano", "-mes"]

    def __str__(self):
        return f"{self.cliente} — {self.mes:02d}/{self.ano}"
