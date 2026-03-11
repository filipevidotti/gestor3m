from django.db import models

from apps.core.models import BaseModel, ActiveManager


class JornadaTemplate(BaseModel):
    """Template de jornada criado pelo gestor."""

    nome = models.CharField("nome", max_length=200)
    descricao = models.TextField("descrição", blank=True)
    tipo_consultoria = models.CharField(
        "tipo de consultoria",
        max_length=20,
        blank=True,
        help_text="Deixe vazio para aplicar a qualquer tipo",
    )
    icone = models.CharField("ícone", max_length=50, default="map", blank=True)
    cor = models.CharField("cor", max_length=7, default="#FE8103")

    objects = ActiveManager()
    all_objects = models.Manager()

    class Meta:
        db_table = "jornada_templates"
        verbose_name = "Template de Jornada"
        verbose_name_plural = "Templates de Jornada"
        ordering = ["nome"]

    def __str__(self):
        return self.nome

    @property
    def total_etapas(self):
        return self.etapas.filter(is_active=True).count()

    @property
    def duracao_total_dias(self):
        ultima = self.etapas.filter(is_active=True).order_by("-dias_offset").first()
        if ultima:
            return ultima.dias_offset + ultima.duracao_dias
        return 0


class EtapaTemplate(BaseModel):
    """Etapa-base de um template de jornada."""

    class TipoEtapa(models.TextChoices):
        REUNIAO = "reuniao", "Reunião"
        DIAGNOSTICO = "diagnostico", "Diagnóstico"
        CHECKLIST = "checklist", "Checklist"
        TREINAMENTO = "treinamento", "Treinamento"
        TAREFA = "tarefa", "Tarefa"
        MARCO = "marco", "Marco"

    jornada_template = models.ForeignKey(
        JornadaTemplate,
        on_delete=models.CASCADE,
        related_name="etapas",
    )
    nome = models.CharField("nome", max_length=200)
    descricao = models.TextField("descrição", blank=True)
    tipo = models.CharField("tipo", max_length=20, choices=TipoEtapa.choices)
    ordem = models.PositiveIntegerField("ordem", default=0)
    dias_offset = models.PositiveIntegerField(
        "dias após início",
        default=0,
        help_text="Dias após o início da jornada para esta etapa",
    )
    duracao_dias = models.PositiveIntegerField(
        "prazo (dias)",
        default=7,
        help_text="Prazo em dias para completar esta etapa",
    )
    is_obrigatoria = models.BooleanField("obrigatória", default=True)
    condicao = models.TextField(
        "condição IA",
        blank=True,
        help_text="Regra para IA: ex: 'só se score_reputacao < 6'",
    )

    # Vínculos opcionais com recursos existentes
    checklist_template = models.ForeignKey(
        "checklists.ChecklistTemplate",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
        verbose_name="checklist vinculado",
    )
    treinamento = models.ForeignKey(
        "treinamentos.Treinamento",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
        verbose_name="treinamento vinculado",
    )
    diagnostico_template = models.ForeignKey(
        "diagnosticos.DiagnosticTemplate",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
        verbose_name="diagnóstico vinculado",
    )

    class Meta:
        db_table = "jornada_etapa_templates"
        verbose_name = "Etapa do Template"
        verbose_name_plural = "Etapas do Template"
        ordering = ["ordem", "dias_offset"]

    def __str__(self):
        return f"{self.nome} (dia +{self.dias_offset})"


class JornadaCliente(BaseModel):
    """Jornada instanciada para um cliente específico."""

    class Status(models.TextChoices):
        ATIVA = "ativa", "Ativa"
        PAUSADA = "pausada", "Pausada"
        CONCLUIDA = "concluida", "Concluída"
        CANCELADA = "cancelada", "Cancelada"

    cliente = models.ForeignKey(
        "clientes.Cliente",
        on_delete=models.CASCADE,
        related_name="jornadas",
    )
    jornada_template = models.ForeignKey(
        JornadaTemplate,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="instancias",
        verbose_name="template base",
    )
    nome = models.CharField("nome da jornada", max_length=200)
    data_inicio = models.DateField("data de início")
    status = models.CharField(
        "status", max_length=20, choices=Status.choices, default=Status.ATIVA,
    )
    progresso = models.DecimalField(
        "progresso (%)", max_digits=5, decimal_places=1, default=0,
    )
    justificativa_ia = models.TextField(
        "justificativa da IA", blank=True,
        help_text="Por que a IA recomendou esta jornada",
    )
    areas_foco = models.JSONField(
        "áreas de foco", default=list, blank=True,
        help_text="Categorias prioritárias identificadas pela IA",
    )
    recalibragens = models.PositiveIntegerField("recalibrações", default=0)

    objects = ActiveManager()
    all_objects = models.Manager()

    class Meta:
        db_table = "jornada_clientes"
        verbose_name = "Jornada do Cliente"
        verbose_name_plural = "Jornadas dos Clientes"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.nome} - {self.cliente}"

    def calcular_progresso(self):
        """Calcula progresso baseado em etapas concluídas."""
        total = self.etapas.filter(is_active=True).count()
        if total == 0:
            self.progresso = 0
            return 0
        concluidas = self.etapas.filter(status="concluida", is_active=True).count()
        self.progresso = round((concluidas / total) * 100, 1)
        self.save(update_fields=["progresso", "updated_at"])
        return self.progresso

    @property
    def total_etapas(self):
        return self.etapas.filter(is_active=True).count()

    @property
    def etapas_concluidas(self):
        return self.etapas.filter(status="concluida", is_active=True).count()

    @property
    def etapas_atrasadas(self):
        from django.utils import timezone
        hoje = timezone.now().date()
        return self.etapas.filter(
            is_active=True,
            status__in=["pendente", "em_andamento"],
            data_limite__lt=hoje,
        ).count()


class EtapaCliente(BaseModel):
    """Etapa instanciada da jornada de um cliente."""

    class Status(models.TextChoices):
        PENDENTE = "pendente", "Pendente"
        EM_ANDAMENTO = "em_andamento", "Em Andamento"
        CONCLUIDA = "concluida", "Concluída"
        ATRASADA = "atrasada", "Atrasada"
        PULADA = "pulada", "Pulada"

    class TipoEtapa(models.TextChoices):
        REUNIAO = "reuniao", "Reunião"
        DIAGNOSTICO = "diagnostico", "Diagnóstico"
        CHECKLIST = "checklist", "Checklist"
        TREINAMENTO = "treinamento", "Treinamento"
        TAREFA = "tarefa", "Tarefa"
        MARCO = "marco", "Marco"

    jornada = models.ForeignKey(
        JornadaCliente,
        on_delete=models.CASCADE,
        related_name="etapas",
    )
    etapa_template = models.ForeignKey(
        EtapaTemplate,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="instancias",
    )
    nome = models.CharField("nome", max_length=200)
    descricao = models.TextField("descrição", blank=True)
    tipo = models.CharField("tipo", max_length=20, choices=TipoEtapa.choices)
    ordem = models.PositiveIntegerField("ordem", default=0)
    data_prevista = models.DateField("data prevista")
    data_limite = models.DateField("data limite")
    data_conclusao = models.DateField("data de conclusão", null=True, blank=True)
    status = models.CharField(
        "status", max_length=20, choices=Status.choices, default=Status.PENDENTE,
    )

    # IA metadata
    adicionada_por_ia = models.BooleanField("adicionada pela IA", default=False)
    motivo_ia = models.TextField(
        "motivo IA", blank=True,
        help_text="Por que a IA adicionou/recomendou esta etapa",
    )

    # Vínculos com recursos (preenchidos quando a etapa é concluída)
    reuniao = models.ForeignKey(
        "reunioes.Reuniao",
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="etapas_jornada",
    )
    checklist_execucao = models.ForeignKey(
        "checklists.ChecklistExecution",
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="etapas_jornada",
    )
    treinamento_realizado = models.ForeignKey(
        "treinamentos.TreinamentoRealizado",
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="etapas_jornada",
    )
    tarefa = models.ForeignKey(
        "tarefas.Tarefa",
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="etapas_jornada",
    )
    diagnostico = models.ForeignKey(
        "diagnosticos.Diagnostic",
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="etapas_jornada",
    )

    class Meta:
        db_table = "jornada_etapa_clientes"
        verbose_name = "Etapa do Cliente"
        verbose_name_plural = "Etapas dos Clientes"
        ordering = ["ordem", "data_prevista"]

    def __str__(self):
        return f"{self.nome} ({self.get_status_display()})"

    def concluir(self, data=None):
        """Marca etapa como concluída."""
        from django.utils import timezone
        self.status = self.Status.CONCLUIDA
        self.data_conclusao = data or timezone.now().date()
        self.save(update_fields=["status", "data_conclusao", "updated_at"])
        self.jornada.calcular_progresso()

    def verificar_atraso(self):
        """Verifica se etapa está atrasada."""
        from django.utils import timezone
        if self.status in [self.Status.PENDENTE, self.Status.EM_ANDAMENTO]:
            if self.data_limite and self.data_limite < timezone.now().date():
                self.status = self.Status.ATRASADA
                self.save(update_fields=["status", "updated_at"])
                return True
        return False
