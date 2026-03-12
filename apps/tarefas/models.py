from django.db import models
from django.utils import timezone

from apps.core.models import ActiveManager, BaseModel


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


class EtapaTarefa(BaseModel):
    """Etapas/colunas configuraveis do kanban de tarefas."""

    nome = models.CharField("nome", max_length=100)
    cor = models.CharField("cor", max_length=7, default="#6366f1")
    icone = models.CharField("ícone", max_length=50, default="circle", blank=True)
    ordem = models.PositiveIntegerField("ordem", default=0)
    is_concluido = models.BooleanField("é conclusão", default=False)

    objects = ActiveManager()
    all_objects = models.Manager()

    class Meta:
        db_table = "etapas_tarefa"
        verbose_name = "Etapa de Tarefa"
        verbose_name_plural = "Etapas de Tarefa"
        ordering = ["ordem"]

    def __str__(self):
        return self.nome


class EtiquetaTarefa(BaseModel):
    """Etiquetas/tags coloridas para categorizar tarefas."""

    nome = models.CharField("nome", max_length=50)
    cor = models.CharField("cor", max_length=7, default="#3b82f6")

    objects = ActiveManager()
    all_objects = models.Manager()

    class Meta:
        db_table = "etiquetas_tarefa"
        verbose_name = "Etiqueta"
        verbose_name_plural = "Etiquetas"
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

    titulo = models.CharField("título", max_length=200, default="")
    cliente = models.ForeignKey(
        "clientes.Cliente",
        on_delete=models.CASCADE,
        related_name="tarefas",
        null=True,
        blank=True,
    )
    criado_por = models.ForeignKey(
        "accounts.User",
        on_delete=models.PROTECT,
        related_name="tarefas_criadas",
        verbose_name="criado por",
    )
    responsavel = models.ForeignKey(
        "accounts.User",
        on_delete=models.PROTECT,
        related_name="tarefas_responsavel",
        verbose_name="responsável",
    )
    tipo = models.ForeignKey(
        TipoTarefa,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="tarefas",
        verbose_name="tipo",
    )
    etapa = models.ForeignKey(
        EtapaTarefa,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="tarefas",
        verbose_name="etapa",
    )
    descricao = models.TextField("descrição", blank=True)
    prioridade = models.CharField(
        "prioridade",
        max_length=20,
        choices=Prioridade.choices,
        default=Prioridade.MEDIA,
    )
    prazo = models.DateField("prazo", null=True, blank=True)
    status = models.CharField(
        "status", max_length=20, choices=Status.choices, default=Status.PENDENTE
    )
    concluido_em = models.DateTimeField("concluído em", null=True, blank=True)
    ordem_kanban = models.PositiveIntegerField("ordem no kanban", default=0)
    etiquetas = models.ManyToManyField(
        EtiquetaTarefa, blank=True, related_name="tarefas", verbose_name="etiquetas"
    )
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
        ordering = ["ordem_kanban"]

    def __str__(self):
        label = self.titulo or self.descricao[:60]
        if self.cliente:
            return f"{label} - {self.cliente}"
        return label

    def save(self, *args, **kwargs):
        # Sync status field from etapa for backward compatibility
        if self.etapa:
            if self.etapa.is_concluido:
                self.status = self.Status.CONCLUIDO
                if not self.concluido_em:
                    self.concluido_em = timezone.now()
            else:
                _map = {
                    "a fazer": "pendente",
                    "em andamento": "em_andamento",
                    "em revisao": "em_andamento",
                    "em revisão": "em_andamento",
                }
                self.status = _map.get(
                    self.etapa.nome.lower(), self.Status.EM_ANDAMENTO
                )
        super().save(*args, **kwargs)

    @property
    def progresso_subtarefas(self):
        total = self.subtarefas.count()
        if not total:
            return None
        concluidas = self.subtarefas.filter(concluida=True).count()
        return {"total": total, "concluidas": concluidas, "percentual": int(concluidas / total * 100)}


class SubTarefa(BaseModel):
    """Itens de checklist dentro de uma tarefa."""

    tarefa = models.ForeignKey(
        Tarefa, on_delete=models.CASCADE, related_name="subtarefas"
    )
    titulo = models.CharField("título", max_length=300)
    concluida = models.BooleanField("concluída", default=False)
    ordem = models.PositiveIntegerField("ordem", default=0)
    responsavel = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="subtarefas",
        verbose_name="responsável",
    )

    class Meta:
        db_table = "subtarefas"
        verbose_name = "Subtarefa"
        verbose_name_plural = "Subtarefas"
        ordering = ["ordem"]

    def __str__(self):
        return self.titulo


class ComentarioTarefa(BaseModel):
    """Comentarios em tarefas."""

    tarefa = models.ForeignKey(
        Tarefa, on_delete=models.CASCADE, related_name="comentarios"
    )
    autor = models.ForeignKey(
        "accounts.User", on_delete=models.PROTECT, related_name="comentarios_tarefa"
    )
    texto = models.TextField("texto")

    class Meta:
        db_table = "comentarios_tarefa"
        verbose_name = "Comentário"
        verbose_name_plural = "Comentários"
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.autor} em {self.tarefa}"


class AtividadeTarefa(BaseModel):
    """Log automatico de atividades em tarefas."""

    tarefa = models.ForeignKey(
        Tarefa, on_delete=models.CASCADE, related_name="atividades"
    )
    autor = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        related_name="atividades_tarefa",
    )
    tipo = models.CharField("tipo", max_length=30)
    descricao = models.CharField("descrição", max_length=500)

    class Meta:
        db_table = "atividades_tarefa"
        verbose_name = "Atividade"
        verbose_name_plural = "Atividades"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.tipo}: {self.descricao[:60]}"
