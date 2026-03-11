from django.db import models

from apps.core.models import BaseModel


class RegistroHoras(BaseModel):
    """Registro de horas trabalhadas por consultor em um cliente."""

    class Categoria(models.TextChoices):
        REUNIAO = "reuniao", "Reunião"
        DIAGNOSTICO = "diagnostico", "Diagnóstico"
        CHECKLIST = "checklist", "Checklist"
        PLANO_ACAO = "plano_acao", "Plano de Ação"
        TREINAMENTO = "treinamento", "Treinamento"
        SUPORTE = "suporte", "Suporte / Atendimento"
        ADMINISTRATIVO = "administrativo", "Administrativo"
        OUTRO = "outro", "Outro"

    consultor = models.ForeignKey(
        "accounts.User",
        on_delete=models.PROTECT,
        related_name="registros_horas",
        verbose_name="consultor",
    )
    cliente = models.ForeignKey(
        "clientes.Cliente",
        on_delete=models.CASCADE,
        related_name="registros_horas",
        verbose_name="cliente",
    )
    data = models.DateField("data")
    hora_inicio = models.TimeField("hora início")
    hora_fim = models.TimeField("hora fim")
    categoria = models.CharField(
        "categoria", max_length=20, choices=Categoria.choices, default=Categoria.REUNIAO
    )
    descricao = models.TextField("descrição", blank=True)

    class Meta:
        db_table = "timesheet_registro"
        verbose_name = "Registro de Horas"
        verbose_name_plural = "Registros de Horas"
        ordering = ["-data", "-hora_inicio"]

    def __str__(self):
        return f"{self.consultor} — {self.cliente} — {self.data}"

    @property
    def duracao_minutos(self):
        from datetime import datetime, timedelta

        inicio = datetime.combine(self.data, self.hora_inicio)
        fim = datetime.combine(self.data, self.hora_fim)
        if fim < inicio:
            fim += timedelta(days=1)
        return int((fim - inicio).total_seconds() / 60)

    @property
    def duracao_formatada(self):
        mins = self.duracao_minutos
        horas = mins // 60
        minutos = mins % 60
        return f"{horas}h{minutos:02d}" if horas else f"{minutos}min"
