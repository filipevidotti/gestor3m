from django.db import models
from apps.core.models import BaseModel


class Score(BaseModel):
    """Pontuacao do usuario (consultor ou seller)."""

    class Categoria(models.TextChoices):
        CHECKLIST = "checklist", "Checklist"
        DIAGNOSTICO = "diagnostico", "Diagnostico"
        TAREFA = "tarefa", "Tarefa"
        REUNIAO = "reuniao", "Reuniao"
        BONUS = "bonus", "Bonus"

    usuario = models.ForeignKey(
        "accounts.User", on_delete=models.CASCADE, related_name="scores"
    )
    pontos = models.IntegerField("pontos")
    categoria = models.CharField("categoria", max_length=20, choices=Categoria.choices)
    descricao = models.CharField("descricao", max_length=200)
    referencia_id = models.PositiveIntegerField("ID referencia", null=True, blank=True)

    class Meta:
        db_table = "gamificacao_scores"
        verbose_name = "Score"
        verbose_name_plural = "Scores"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.usuario} +{self.pontos} ({self.categoria})"


class Achievement(BaseModel):
    """Definicao de conquista desbloqueavel."""

    class Tipo(models.TextChoices):
        BRONZE = "bronze", "Bronze"
        PRATA = "prata", "Prata"
        OURO = "ouro", "Ouro"
        DIAMANTE = "diamante", "Diamante"

    nome = models.CharField("nome", max_length=100)
    descricao = models.CharField("descricao", max_length=200)
    icone = models.CharField("icone", max_length=50, default="award")
    tipo = models.CharField("tipo", max_length=20, choices=Tipo.choices, default=Tipo.BRONZE)
    pontos_recompensa = models.IntegerField("pontos recompensa", default=0)
    criterio_campo = models.CharField(
        "campo criterio", max_length=50,
        help_text="Ex: checklists_concluidos, tarefas_concluidas, score_diagnostico"
    )
    criterio_valor = models.IntegerField("valor criterio", help_text="Valor minimo para desbloquear")
    publico = models.CharField(
        "publico", max_length=20,
        choices=[("consultor", "Consultor"), ("seller", "Seller"), ("ambos", "Ambos")],
        default="ambos",
    )

    class Meta:
        db_table = "gamificacao_achievements"
        verbose_name = "Conquista"
        verbose_name_plural = "Conquistas"
        ordering = ["tipo", "criterio_valor"]

    def __str__(self):
        return f"{self.nome} ({self.get_tipo_display()})"


class UserAchievement(BaseModel):
    """Conquista desbloqueada por um usuario."""

    usuario = models.ForeignKey(
        "accounts.User", on_delete=models.CASCADE, related_name="conquistas"
    )
    achievement = models.ForeignKey(
        Achievement, on_delete=models.CASCADE, related_name="desbloqueios"
    )
    desbloqueado_em = models.DateTimeField("desbloqueado em", auto_now_add=True)

    class Meta:
        db_table = "gamificacao_user_achievements"
        verbose_name = "Conquista do Usuario"
        verbose_name_plural = "Conquistas dos Usuarios"
        unique_together = ["usuario", "achievement"]

    def __str__(self):
        return f"{self.usuario} - {self.achievement.nome}"


class Streak(BaseModel):
    """Sequencia de atividade diaria."""

    usuario = models.OneToOneField(
        "accounts.User", on_delete=models.CASCADE, related_name="streak"
    )
    dias_consecutivos = models.IntegerField("dias consecutivos", default=0)
    maior_sequencia = models.IntegerField("maior sequencia", default=0)
    ultimo_dia = models.DateField("ultimo dia ativo", null=True, blank=True)

    class Meta:
        db_table = "gamificacao_streaks"
        verbose_name = "Streak"
        verbose_name_plural = "Streaks"

    def __str__(self):
        return f"{self.usuario} - {self.dias_consecutivos} dias"
