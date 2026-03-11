from django.db import models
from apps.core.models import BaseModel, ActiveManager


class TipoTarefa(BaseModel):
    """Tipos configuraveis de tarefa operacional."""
    nome = models.CharField("nome", max_length=100)
    icone = models.CharField("icone", max_length=50, default="clipboard")
    cor = models.CharField("cor", max_length=7, default="#6366f1")

    class Meta:
        db_table = "tipos_tarefa"
        verbose_name = "Tipo de Tarefa"
        verbose_name_plural = "Tipos de Tarefa"
        ordering = ["nome"]

    def __str__(self):
        return self.nome


class Tarefa(BaseModel):
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

    cliente = models.ForeignKey(
        "clientes.Cliente", on_delete=models.CASCADE, related_name="tarefas"
    )
    criado_por = models.ForeignKey(
        "accounts.User", on_delete=models.PROTECT, related_name="tarefas_criadas",
        verbose_name="criado por"
    )
    responsavel = models.ForeignKey(
        "accounts.User", on_delete=models.PROTECT, related_name="tarefas_responsavel",
        verbose_name="responsável"
    )
    tipo = models.ForeignKey(
        TipoTarefa,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="tarefas",
        verbose_name="tipo",
    )
    descricao = models.TextField("descrição")
    prioridade = models.CharField(
        "prioridade", max_length=20, choices=Prioridade.choices, default=Prioridade.MEDIA
    )
    prazo = models.DateField("prazo", null=True, blank=True)
    status = models.CharField(
        "status", max_length=20, choices=Status.choices, default=Status.PENDENTE
    )
    concluido_em = models.DateTimeField("concluído em", null=True, blank=True)
    checklist_execution = models.ForeignKey(
        "checklists.ChecklistExecution",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="tarefas",
        verbose_name="checklist vinculado",
    )

    objects = ActiveManager()
    all_objects = models.Manager()

    class Meta:
        db_table = "tarefas"
        verbose_name = "Tarefa"
        verbose_name_plural = "Tarefas"

    def __str__(self):
        return f"{self.descricao[:60]} - {self.cliente}"
