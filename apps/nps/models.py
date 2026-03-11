import uuid

from django.db import models

from apps.core.models import BaseModel


class PesquisaNPS(BaseModel):
    """Pesquisa NPS enviada periodicamente aos clientes."""
    titulo = models.CharField("título", max_length=200)
    descricao = models.TextField("descrição", blank=True)
    criado_por = models.ForeignKey(
        "accounts.User", on_delete=models.PROTECT,
        related_name="pesquisas_nps", verbose_name="criado por",
    )

    class Meta:
        db_table = "nps_pesquisas"
        verbose_name = "Pesquisa NPS"
        verbose_name_plural = "Pesquisas NPS"

    def __str__(self):
        return self.titulo

    @property
    def total_respostas(self):
        return self.respostas.count()

    @property
    def nps_score(self):
        """Calcula NPS = %promotores - %detratores."""
        respostas = self.respostas.all()
        total = respostas.count()
        if total == 0:
            return None

        promotores = respostas.filter(nota__gte=9).count()
        detratores = respostas.filter(nota__lte=6).count()

        return round(((promotores - detratores) / total) * 100)

    @property
    def distribuicao(self):
        """Retorna contagem de promotores, neutros e detratores."""
        respostas = self.respostas.all()
        return {
            "promotores": respostas.filter(nota__gte=9).count(),
            "neutros": respostas.filter(nota__in=[7, 8]).count(),
            "detratores": respostas.filter(nota__lte=6).count(),
            "total": respostas.count(),
        }


class RespostaNPS(BaseModel):
    """Resposta individual de um cliente à pesquisa NPS."""
    pesquisa = models.ForeignKey(
        PesquisaNPS, on_delete=models.CASCADE, related_name="respostas",
    )
    cliente = models.ForeignKey(
        "clientes.Cliente", on_delete=models.CASCADE, related_name="respostas_nps",
    )
    nota = models.PositiveIntegerField(
        "nota (0-10)", help_text="0 = Não recomendaria, 10 = Recomendaria com certeza"
    )
    comentario = models.TextField("comentário", blank=True)
    token = models.UUIDField("token", default=uuid.uuid4, unique=True, editable=False)
    respondido_em = models.DateTimeField("respondido em", null=True, blank=True)

    class Meta:
        db_table = "nps_respostas"
        verbose_name = "Resposta NPS"
        verbose_name_plural = "Respostas NPS"
        unique_together = ["pesquisa", "cliente"]

    def __str__(self):
        return f"{self.cliente} — Nota: {self.nota}"

    @property
    def classificacao(self):
        if self.nota >= 9:
            return "promotor"
        elif self.nota >= 7:
            return "neutro"
        return "detrator"
