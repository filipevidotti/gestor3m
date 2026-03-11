from django.db import models
from apps.core.models import BaseModel


class Treinamento(BaseModel):
    class Categoria(models.TextChoices):
        SEO = "seo", "SEO para Anúncios"
        ADS = "ads", "Mercado Ads"
        FULL = "full", "Logística FULL"
        REPUTACAO = "reputacao", "Reputação"
        CATALOGO = "catalogo", "Catálogo"
        VENDAS = "vendas", "Vendas"
        OUTRO = "outro", "Outro"

    titulo = models.CharField("título", max_length=200)
    categoria = models.CharField("categoria", max_length=20, choices=Categoria.choices)
    descricao = models.TextField("descrição", blank=True)
    conteudo_url = models.URLField("link do conteúdo", blank=True)
    material = models.FileField("material", upload_to="treinamentos/", blank=True)
    duracao_minutos = models.PositiveIntegerField("duração (min)", default=0)

    class Meta:
        db_table = "treinamentos"
        verbose_name = "Treinamento"
        verbose_name_plural = "Treinamentos"

    def __str__(self):
        return self.titulo


class TreinamentoRealizado(BaseModel):
    treinamento = models.ForeignKey(
        Treinamento, on_delete=models.CASCADE, related_name="realizacoes"
    )
    cliente = models.ForeignKey(
        "clientes.Cliente", on_delete=models.CASCADE, related_name="treinamentos_realizados"
    )
    data = models.DateField("data de realização")
    observacoes = models.TextField("observações", blank=True)
    material_especifico = models.FileField(
        "material específico", upload_to="treinamentos/clientes/", blank=True,
    )

    class Meta:
        db_table = "treinamentos_realizados"
        verbose_name = "Treinamento Realizado"
        verbose_name_plural = "Treinamentos Realizados"
        unique_together = ["treinamento", "cliente"]

    def __str__(self):
        return f"{self.treinamento} - {self.cliente}"
