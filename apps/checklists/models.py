from django.db import models
from apps.core.models import BaseModel, ActiveManager


class ChecklistCategory(BaseModel):
    """Categoria para agrupar itens de checklist."""
    nome = models.CharField("nome", max_length=200)
    descricao = models.TextField("descrição", blank=True)
    icone = models.CharField("ícone", max_length=50, blank=True, help_text="Nome do ícone Flowbite/Heroicons")
    ordem = models.PositiveIntegerField("ordem", default=0)

    class Meta:
        db_table = "checklist_categorias"
        verbose_name = "Categoria de Checklist"
        verbose_name_plural = "Categorias de Checklist"
        ordering = ["ordem"]

    def __str__(self):
        return self.nome


class ChecklistTemplate(BaseModel):
    class TargetAudience(models.TextChoices):
        CONSULTANT = "consultant", "Consultor"
        CLIENT = "client", "Cliente"

    class Tipo(models.TextChoices):
        ONBOARDING = "onboarding", "Onboarding"
        RECORRENTE = "recorrente", "Recorrente"
        AVULSO = "avulso", "Avulso"

    nome = models.CharField("nome", max_length=200)
    descricao = models.TextField("descrição", blank=True)
    icone = models.CharField("ícone", max_length=50, blank=True)
    target_audience = models.CharField(
        "público-alvo", max_length=20,
        choices=TargetAudience.choices, default=TargetAudience.CONSULTANT,
    )
    tipo = models.CharField("tipo", max_length=20, choices=Tipo.choices, default=Tipo.AVULSO)
    criado_por = models.ForeignKey(
        "accounts.User", on_delete=models.PROTECT,
        related_name="templates_criados", verbose_name="criado por",
        null=True, blank=True,
    )

    objects = ActiveManager()
    all_objects = models.Manager()

    class Meta:
        db_table = "checklist_templates"
        verbose_name = "Template de Checklist"
        verbose_name_plural = "Templates de Checklist"

    def __str__(self):
        return f"{self.nome} ({self.get_target_audience_display()})"

    @property
    def total_itens(self):
        return self.itens.count()


class ChecklistTemplateItem(BaseModel):
    template = models.ForeignKey(
        ChecklistTemplate, on_delete=models.CASCADE, related_name="itens",
    )
    category = models.ForeignKey(
        ChecklistCategory, on_delete=models.SET_NULL,
        null=True, blank=True, related_name="template_itens",
        verbose_name="categoria",
    )
    descricao = models.CharField("descrição", max_length=500)
    instrucoes = models.TextField("instruções", blank=True, help_text="Instruções detalhadas para o item")
    ordem = models.PositiveIntegerField("ordem", default=0)
    requires_evidence = models.BooleanField("exige evidência", default=False)
    requires_note = models.BooleanField("exige observação", default=False)

    class Meta:
        db_table = "checklist_template_itens"
        verbose_name = "Item do Template"
        verbose_name_plural = "Itens do Template"
        ordering = ["category__ordem", "ordem"]

    def __str__(self):
        return self.descricao


class ChecklistExecution(BaseModel):
    class Status(models.TextChoices):
        PENDING = "pending", "Pendente"
        IN_PROGRESS = "in_progress", "Em Andamento"
        COMPLETED = "completed", "Concluído"
        CANCELLED = "cancelled", "Cancelado"

    template = models.ForeignKey(
        ChecklistTemplate, on_delete=models.PROTECT, related_name="execucoes",
    )
    cliente = models.ForeignKey(
        "clientes.Cliente", on_delete=models.CASCADE, related_name="checklists",
    )
    executor = models.ForeignKey(
        "accounts.User", on_delete=models.PROTECT,
        related_name="checklists_executados", verbose_name="executor",
    )
    status = models.CharField(
        "status", max_length=20, choices=Status.choices, default=Status.PENDING,
    )
    started_at = models.DateTimeField("iniciado em", null=True, blank=True)
    completed_at = models.DateTimeField("concluído em", null=True, blank=True)
    score = models.PositiveIntegerField("score", default=0, help_text="Percentual 0-100")

    objects = ActiveManager()
    all_objects = models.Manager()

    class Meta:
        db_table = "checklist_execucoes"
        verbose_name = "Execução de Checklist"
        verbose_name_plural = "Execuções de Checklist"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.template.nome} - {self.cliente} ({self.get_status_display()})"

    def calcular_score(self):
        """Calcula score: % de itens conformes vs total (excluindo N/A)."""
        itens = self.itens.exclude(status="not_applicable")
        total = itens.count()
        if total == 0:
            self.score = 0
            return 0
        conformes = itens.filter(status="conforming").count()
        self.score = int((conformes / total) * 100)
        return self.score

    @property
    def progresso(self):
        total = self.itens.count()
        if total == 0:
            return 0
        respondidos = self.itens.exclude(status="pending").count()
        return int((respondidos / total) * 100)


class ChecklistExecutionItem(BaseModel):
    class Status(models.TextChoices):
        PENDING = "pending", "Pendente"
        CONFORMING = "conforming", "Conforme"
        NON_CONFORMING = "non_conforming", "Não Conforme"
        NOT_APPLICABLE = "not_applicable", "Não Aplicável"

    execution = models.ForeignKey(
        ChecklistExecution, on_delete=models.CASCADE, related_name="itens",
    )
    template_item = models.ForeignKey(
        ChecklistTemplateItem, on_delete=models.PROTECT, related_name="execucoes",
    )
    status = models.CharField(
        "status", max_length=20, choices=Status.choices, default=Status.PENDING,
    )
    note = models.TextField("observação", blank=True)
    completed_at = models.DateTimeField("respondido em", null=True, blank=True)
    completed_by = models.ForeignKey(
        "accounts.User", on_delete=models.SET_NULL,
        null=True, blank=True, verbose_name="respondido por",
    )

    class Meta:
        db_table = "checklist_execucao_itens"
        verbose_name = "Item da Execução"
        verbose_name_plural = "Itens da Execução"
        ordering = ["template_item__category__ordem", "template_item__ordem"]

    def __str__(self):
        return f"{self.template_item.descricao} - {self.get_status_display()}"


class Evidence(BaseModel):
    """Evidência (foto/print) associada a um item de execução."""
    execution_item = models.ForeignKey(
        ChecklistExecutionItem, on_delete=models.CASCADE, related_name="evidencias",
    )
    file = models.ImageField("arquivo", upload_to="evidencias/%Y/%m/")
    description = models.CharField("descrição", max_length=300, blank=True)
    uploaded_by = models.ForeignKey(
        "accounts.User", on_delete=models.SET_NULL,
        null=True, verbose_name="enviado por",
    )

    class Meta:
        db_table = "evidencias"
        verbose_name = "Evidência"
        verbose_name_plural = "Evidências"

    def __str__(self):
        return f"Evidência - {self.execution_item.template_item.descricao[:40]}"
