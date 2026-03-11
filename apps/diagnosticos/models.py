from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Avg

from apps.core.models import BaseModel, ActiveManager


class DiagnosticTemplate(BaseModel):
    """Template de diagnóstico criado pelo gestor."""
    nome = models.CharField("nome", max_length=200)
    descricao = models.TextField("descrição", blank=True)
    criado_por = models.ForeignKey(
        "accounts.User", on_delete=models.PROTECT,
        related_name="diagnostic_templates", verbose_name="criado por",
        null=True, blank=True,
    )

    objects = ActiveManager()
    all_objects = models.Manager()

    class Meta:
        db_table = "diagnostic_templates"
        verbose_name = "Template de Diagnóstico"
        verbose_name_plural = "Templates de Diagnóstico"

    def __str__(self):
        return self.nome

    @property
    def total_perguntas(self):
        return self.perguntas.count()

    @property
    def categorias(self):
        return (
            self.perguntas
            .values_list("categoria", flat=True)
            .distinct()
            .order_by("categoria")
        )


class DiagnosticQuestion(BaseModel):
    """Pergunta do template de diagnóstico com peso e tipo."""

    class TipoPergunta(models.TextChoices):
        SCALE_1_10 = "scale_1_10", "Escala 1 a 10"
        VALUE = "value", "Valor Numérico"
        SELECTION = "selection", "Seleção"

    template = models.ForeignKey(
        DiagnosticTemplate, on_delete=models.CASCADE, related_name="perguntas",
    )
    categoria = models.CharField("categoria", max_length=100, help_text="Ex: Vendas, Logística, Reputação")
    texto = models.CharField("pergunta", max_length=500)
    tipo = models.CharField("tipo", max_length=20, choices=TipoPergunta.choices)
    weight = models.DecimalField(
        "peso", max_digits=5, decimal_places=2, default=1.00,
        help_text="Peso na média ponderada",
    )
    is_inverted = models.BooleanField(
        "invertida", default=False,
        help_text="Marque se menor valor = melhor resultado",
    )
    options = models.JSONField(
        "opções", null=True, blank=True,
        help_text='Para tipo "selection": {"Bom": 8, "Regular": 5, "Ruim": 2}',
    )
    ordem = models.PositiveIntegerField("ordem", default=0)

    class Meta:
        db_table = "diagnostic_questions"
        verbose_name = "Pergunta do Diagnóstico"
        verbose_name_plural = "Perguntas do Diagnóstico"
        ordering = ["categoria", "ordem"]

    def __str__(self):
        return f"[{self.categoria}] {self.texto}"


class Diagnostic(BaseModel):
    """Execução de diagnóstico mensal vinculada a template + cliente."""

    class Status(models.TextChoices):
        PENDING = "pending", "Pendente"
        IN_PROGRESS = "in_progress", "Em Andamento"
        COMPLETED = "completed", "Concluído"
        CANCELLED = "cancelled", "Cancelado"

    template = models.ForeignKey(
        DiagnosticTemplate, on_delete=models.PROTECT, related_name="diagnosticos",
    )
    cliente = models.ForeignKey(
        "clientes.Cliente", on_delete=models.CASCADE, related_name="diagnosticos",
    )
    executor = models.ForeignKey(
        "accounts.User", on_delete=models.PROTECT,
        related_name="diagnosticos_executados", verbose_name="executor",
    )
    mes = models.PositiveIntegerField("mês", validators=[MinValueValidator(1), MaxValueValidator(12)])
    ano = models.PositiveIntegerField("ano")
    status = models.CharField(
        "status", max_length=20, choices=Status.choices, default=Status.PENDING,
    )
    score = models.DecimalField(
        "score", max_digits=4, decimal_places=1, default=0,
        validators=[MinValueValidator(0), MaxValueValidator(10)],
    )
    scores_por_categoria = models.JSONField(
        "scores por categoria", default=dict, blank=True,
        help_text='Ex: {"Vendas": 7.2, "Logística": 5.8}',
    )
    completed_at = models.DateTimeField("concluído em", null=True, blank=True)

    objects = ActiveManager()
    all_objects = models.Manager()

    class Meta:
        db_table = "diagnosticos"
        verbose_name = "Diagnóstico"
        verbose_name_plural = "Diagnósticos"
        unique_together = ["cliente", "mes", "ano", "template"]
        ordering = ["-ano", "-mes"]

    def __str__(self):
        return f"{self.cliente} - {self.mes:02d}/{self.ano} ({self.get_status_display()})"

    def calcular_score(self):
        """Calcula score final e por categoria (média ponderada 0-10)."""
        respostas = self.respostas.select_related("question").all()
        if not respostas:
            return 0

        scores_cat = {}
        pesos_cat = {}
        total_score = 0
        total_peso = 0

        for resp in respostas:
            q = resp.question
            cat = q.categoria
            peso = float(q.weight)

            if cat not in scores_cat:
                scores_cat[cat] = 0
                pesos_cat[cat] = 0

            scores_cat[cat] += float(resp.score) * peso
            pesos_cat[cat] += peso
            total_score += float(resp.score) * peso
            total_peso += peso

        # Score por categoria
        self.scores_por_categoria = {
            cat: round(scores_cat[cat] / pesos_cat[cat], 1)
            for cat in scores_cat if pesos_cat[cat] > 0
        }

        # Score geral
        self.score = round(total_score / total_peso, 1) if total_peso > 0 else 0
        return self.score

    def copy_to_next_month(self):
        """Cria diagnóstico do próximo mês com mesmo template."""
        next_mes = self.mes + 1 if self.mes < 12 else 1
        next_ano = self.ano if self.mes < 12 else self.ano + 1
        return Diagnostic.objects.create(
            template=self.template,
            cliente=self.cliente,
            executor=self.executor,
            mes=next_mes,
            ano=next_ano,
        )

    @property
    def progresso(self):
        total = self.template.perguntas.count()
        if total == 0:
            return 0
        respondidas = self.respostas.count()
        return int((respondidas / total) * 100)


class DiagnosticAnswer(BaseModel):
    """Resposta individual a uma pergunta do diagnóstico."""
    diagnostic = models.ForeignKey(
        Diagnostic, on_delete=models.CASCADE, related_name="respostas",
    )
    question = models.ForeignKey(
        DiagnosticQuestion, on_delete=models.PROTECT, related_name="respostas",
    )
    value_numeric = models.DecimalField(
        "valor numérico", max_digits=12, decimal_places=2, null=True, blank=True,
    )
    value_text = models.CharField("valor texto", max_length=200, blank=True)
    score = models.DecimalField(
        "score", max_digits=4, decimal_places=1, default=0,
        validators=[MinValueValidator(0), MaxValueValidator(10)],
        help_text="Score normalizado 0-10",
    )

    class Meta:
        db_table = "diagnostic_answers"
        verbose_name = "Resposta do Diagnóstico"
        verbose_name_plural = "Respostas do Diagnóstico"
        unique_together = ["diagnostic", "question"]

    def __str__(self):
        return f"{self.question.texto[:40]} = {self.value_numeric or self.value_text}"

    def calcular_score(self):
        """Calcula score normalizado 0-10 baseado no tipo da pergunta."""
        q = self.question

        if q.tipo == DiagnosticQuestion.TipoPergunta.SCALE_1_10:
            raw = float(self.value_numeric or 0)
            self.score = round(raw, 1)

        elif q.tipo == DiagnosticQuestion.TipoPergunta.VALUE:
            # Para valor livre, normalizar é responsabilidade do template
            raw = float(self.value_numeric or 0)
            self.score = min(round(raw, 1), 10)

        elif q.tipo == DiagnosticQuestion.TipoPergunta.SELECTION:
            if q.options and self.value_text in q.options:
                raw = float(q.options[self.value_text])
                self.score = min(round(raw, 1), 10)
            else:
                self.score = 0

        # Inverter se menor = melhor
        if q.is_inverted:
            self.score = round(10 - float(self.score), 1)

        return self.score


class BenchmarkSegmento(BaseModel):
    """Benchmark médio por segmento/nicho para comparação com diagnósticos."""
    segmento = models.CharField("segmento", max_length=100, unique=True)
    score_medio = models.DecimalField(
        "score médio", max_digits=4, decimal_places=1, default=0,
    )
    scores_por_categoria = models.JSONField(
        "scores por categoria", default=dict, blank=True,
    )
    total_diagnosticos = models.PositiveIntegerField("total diagnósticos", default=0)
    atualizado_em = models.DateTimeField("atualizado em", auto_now=True)

    class Meta:
        db_table = "benchmark_segmentos"
        verbose_name = "Benchmark por Segmento"
        verbose_name_plural = "Benchmarks por Segmento"
        ordering = ["segmento"]

    def __str__(self):
        return f"{self.segmento} — Score: {self.score_medio}"

    @classmethod
    def recalcular(cls, segmento):
        """Recalcula benchmark de um segmento baseado nos diagnósticos concluídos."""
        from apps.clientes.models import Cliente

        clientes_ids = Cliente.objects.filter(
            nicho__iexact=segmento, status__in=["ativo", "onboarding"]
        ).values_list("id", flat=True)

        diags = Diagnostic.objects.filter(
            cliente_id__in=clientes_ids, status="completed"
        )

        total = diags.count()
        if total == 0:
            cls.objects.filter(segmento=segmento).delete()
            return None

        score_medio = diags.aggregate(media=Avg("score"))["media"] or 0

        # Média por categoria
        scores_cat = {}
        contagens_cat = {}
        for d in diags:
            if d.scores_por_categoria:
                for cat, val in d.scores_por_categoria.items():
                    scores_cat[cat] = scores_cat.get(cat, 0) + float(val)
                    contagens_cat[cat] = contagens_cat.get(cat, 0) + 1

        medias_cat = {
            cat: round(scores_cat[cat] / contagens_cat[cat], 1)
            for cat in scores_cat
        }

        benchmark, _ = cls.objects.update_or_create(
            segmento=segmento,
            defaults={
                "score_medio": round(float(score_medio), 1),
                "scores_por_categoria": medias_cat,
                "total_diagnosticos": total,
            },
        )
        return benchmark

    @classmethod
    def recalcular_todos(cls):
        """Recalcula benchmarks para todos os segmentos com diagnósticos."""
        from apps.clientes.models import Cliente

        segmentos = (
            Cliente.objects.filter(status__in=["ativo", "onboarding"])
            .exclude(nicho="")
            .values_list("nicho", flat=True)
            .distinct()
        )
        for seg in segmentos:
            cls.recalcular(seg)
