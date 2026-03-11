from django.db import models

from apps.core.models import BaseModel, ActiveManager


class CategoriaConhecimento(BaseModel):
    """Categorias para organizar artigos."""
    nome = models.CharField("nome", max_length=100)
    descricao = models.CharField("descrição", max_length=300, blank=True)
    icone = models.CharField("ícone", max_length=50, blank=True, help_text="Nome do ícone SVG")
    ordem = models.PositiveIntegerField("ordem", default=0)

    class Meta:
        db_table = "conhecimento_categorias"
        verbose_name = "Categoria"
        verbose_name_plural = "Categorias"
        ordering = ["ordem"]

    def __str__(self):
        return self.nome


class Artigo(BaseModel):
    """Artigo/playbook da base de conhecimento."""

    class Visibilidade(models.TextChoices):
        TODOS = "todos", "Todos (consultor + seller)"
        CONSULTORES = "consultores", "Apenas Consultores"
        GESTORES = "gestores", "Apenas Gestores"

    titulo = models.CharField("título", max_length=300)
    slug = models.SlugField("slug", max_length=300, unique=True)
    categoria = models.ForeignKey(
        CategoriaConhecimento, on_delete=models.SET_NULL,
        null=True, blank=True, related_name="artigos",
    )
    conteudo = models.TextField("conteúdo", help_text="Suporta Markdown")
    resumo = models.CharField("resumo", max_length=500, blank=True)
    autor = models.ForeignKey(
        "accounts.User", on_delete=models.PROTECT,
        related_name="artigos", verbose_name="autor",
    )
    visibilidade = models.CharField(
        "visibilidade", max_length=20,
        choices=Visibilidade.choices, default=Visibilidade.TODOS,
    )
    destaque = models.BooleanField("destaque", default=False)
    visualizacoes = models.PositiveIntegerField("visualizações", default=0)

    objects = ActiveManager()
    all_objects = models.Manager()

    class Meta:
        db_table = "conhecimento_artigos"
        verbose_name = "Artigo"
        verbose_name_plural = "Artigos"
        ordering = ["-destaque", "-created_at"]

    def __str__(self):
        return self.titulo
