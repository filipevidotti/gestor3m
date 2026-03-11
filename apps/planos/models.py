from django.db import models
from apps.core.models import BaseModel


class PlanoAcao(BaseModel):
    class Tipo(models.TextChoices):
        ESTRATEGICO = "estrategico", "Estratégico"
        SEMANAL = "semanal", "Semanal"
        DIARIO = "diario", "Diário"

    cliente = models.ForeignKey(
        "clientes.Cliente", on_delete=models.CASCADE, related_name="planos"
    )
    titulo = models.CharField("título", max_length=200)
    tipo = models.CharField("tipo", max_length=20, choices=Tipo.choices)
    descricao = models.TextField("descrição", blank=True)

    class Meta:
        db_table = "planos_acao"
        verbose_name = "Plano de Ação"
        verbose_name_plural = "Planos de Ação"

    def __str__(self):
        return f"{self.titulo} ({self.cliente})"

    @property
    def progresso(self):
        total = self.itens.count()
        if total == 0:
            return 0
        concluidos = self.itens.filter(status="concluido").count()
        return int((concluidos / total) * 100)


class ItemPlano(BaseModel):
    class Status(models.TextChoices):
        PENDENTE = "pendente", "Pendente"
        EM_ANDAMENTO = "em_andamento", "Em Andamento"
        CONCLUIDO = "concluido", "Concluído"
        ATRASADO = "atrasado", "Atrasado"

    class Prioridade(models.TextChoices):
        BAIXA = "baixa", "Baixa"
        MEDIA = "media", "Média"
        ALTA = "alta", "Alta"
        URGENTE = "urgente", "Urgente"

    plano = models.ForeignKey(
        PlanoAcao, on_delete=models.CASCADE, related_name="itens"
    )
    descricao = models.TextField("descrição")
    responsavel = models.ForeignKey(
        "accounts.User", on_delete=models.PROTECT, verbose_name="responsável"
    )
    prioridade = models.CharField(
        "prioridade", max_length=20, choices=Prioridade.choices, default=Prioridade.MEDIA
    )
    prazo = models.DateField("prazo", null=True, blank=True)
    status = models.CharField(
        "status", max_length=20, choices=Status.choices, default=Status.PENDENTE
    )

    class Meta:
        db_table = "itens_plano"
        verbose_name = "Item do Plano"
        verbose_name_plural = "Itens do Plano"
        ordering = ["prioridade", "prazo"]

    def __str__(self):
        return self.descricao[:80]
