from django.db import models
from apps.core.models import BaseModel, ActiveManager


class UploadCurvaABC(BaseModel):
    """Upload semanal da planilha de Curva ABC."""

    class Periodo(models.TextChoices):
        SETE_DIAS = "7d", "Últimos 7 dias"
        TRINTA_DIAS = "30d", "Últimos 30 dias"

    cliente = models.ForeignKey(
        "clientes.Cliente", on_delete=models.CASCADE, related_name="uploads_curva_abc",
    )
    uploaded_by = models.ForeignKey(
        "accounts.User", on_delete=models.PROTECT, related_name="uploads_curva_abc",
        verbose_name="enviado por",
    )
    periodo = models.CharField("período", max_length=5, choices=Periodo.choices)
    data_referencia = models.DateField("data de referência")
    arquivo = models.FileField("arquivo", upload_to="anuncios/curva_abc/%Y/%m/")

    class Meta:
        db_table = "uploads_curva_abc"
        verbose_name = "Upload Curva ABC"
        verbose_name_plural = "Uploads Curva ABC"
        ordering = ["-data_referencia"]

    def __str__(self):
        return f"Curva ABC - {self.cliente} - {self.data_referencia}"


class ItemCurvaABC(BaseModel):
    """Linha individual de um upload de Curva ABC."""

    upload = models.ForeignKey(
        UploadCurvaABC, on_delete=models.CASCADE, related_name="itens",
    )
    classe = models.CharField("classe", max_length=5)
    mlb = models.CharField("MLB", max_length=30)
    sku = models.CharField("SKU", max_length=100, blank=True)
    titulo = models.CharField("título", max_length=500)
    marca = models.CharField("marca", max_length=200, blank=True)
    status = models.CharField("status", max_length=50, blank=True)
    tipo = models.CharField("tipo", max_length=50, blank=True)
    catalogo = models.CharField("catálogo", max_length=10, blank=True)
    logistica = models.CharField("logística", max_length=50, blank=True)
    estoque = models.IntegerField("estoque", default=0)
    preco_atual = models.DecimalField("preço atual", max_digits=12, decimal_places=2, default=0)
    quantidade = models.IntegerField("quantidade vendida", default=0)
    ticket_medio = models.DecimalField("ticket médio", max_digits=12, decimal_places=2, default=0)
    faturamento = models.DecimalField("faturamento", max_digits=14, decimal_places=2, default=0)
    margem = models.DecimalField("margem", max_digits=14, decimal_places=2, default=0)
    percentual_total = models.DecimalField("% do total", max_digits=7, decimal_places=2, default=0)
    percentual_acumulado = models.DecimalField("% acumulado", max_digits=7, decimal_places=2, default=0)

    class Meta:
        db_table = "itens_curva_abc"
        verbose_name = "Item Curva ABC"
        verbose_name_plural = "Itens Curva ABC"
        ordering = ["classe", "-faturamento"]

    def __str__(self):
        return f"{self.classe} - {self.mlb} - {self.titulo[:40]}"


class UploadMetricas(BaseModel):
    """Upload semanal da planilha de Métricas."""

    class Periodo(models.TextChoices):
        SETE_DIAS = "7d", "Últimos 7 dias"
        TRINTA_DIAS = "30d", "Últimos 30 dias"

    cliente = models.ForeignKey(
        "clientes.Cliente", on_delete=models.CASCADE, related_name="uploads_metricas",
    )
    uploaded_by = models.ForeignKey(
        "accounts.User", on_delete=models.PROTECT, related_name="uploads_metricas",
        verbose_name="enviado por",
    )
    periodo = models.CharField("período", max_length=5, choices=Periodo.choices)
    data_referencia = models.DateField("data de referência")
    arquivo = models.FileField("arquivo", upload_to="anuncios/metricas/%Y/%m/")

    class Meta:
        db_table = "uploads_metricas"
        verbose_name = "Upload Métricas"
        verbose_name_plural = "Uploads Métricas"
        ordering = ["-data_referencia"]

    def __str__(self):
        return f"Métricas - {self.cliente} - {self.data_referencia}"


class ItemMetrica(BaseModel):
    """Linha individual de um upload de Métricas."""

    upload = models.ForeignKey(
        UploadMetricas, on_delete=models.CASCADE, related_name="itens",
    )
    mlb = models.CharField("MLB", max_length=30)
    status = models.CharField("status", max_length=50, blank=True)
    geral = models.IntegerField("geral", default=0)
    vendas_30d = models.IntegerField("vendas 30d", default=0)
    visitas = models.IntegerField("visitas", default=0)
    conversao = models.DecimalField("conversão", max_digits=7, decimal_places=2, default=0)
    avaliacao = models.IntegerField("avaliação", default=0)
    preco = models.DecimalField("preço", max_digits=12, decimal_places=2, default=0)
    categoria = models.CharField("categoria", max_length=200, blank=True)
    video = models.CharField("vídeo", max_length=50, blank=True)
    foto = models.CharField("foto", max_length=50, blank=True)
    frete = models.CharField("frete", max_length=100, blank=True)
    ads = models.CharField("ADS", max_length=100, blank=True)
    promo = models.CharField("promo", max_length=100, blank=True)

    class Meta:
        db_table = "itens_metricas"
        verbose_name = "Item Métrica"
        verbose_name_plural = "Itens Métricas"
        ordering = ["-geral"]

    def __str__(self):
        return f"{self.mlb} - Geral: {self.geral}"


class AnuncioAtualizar(BaseModel):
    """Anúncio que precisa de atualização (foto/vídeo)."""

    cliente = models.ForeignKey(
        "clientes.Cliente", on_delete=models.CASCADE, related_name="anuncios_atualizar",
    )
    criado_por = models.ForeignKey(
        "accounts.User", on_delete=models.PROTECT, related_name="anuncios_criados",
        verbose_name="criado por",
    )
    mlb = models.CharField("MLB", max_length=30)
    titulo = models.CharField("título", max_length=500)
    precisa_foto = models.BooleanField("precisa foto", default=False)
    precisa_video = models.BooleanField("precisa vídeo", default=False)
    foto_feito = models.BooleanField("foto feito", default=False)
    video_feito = models.BooleanField("vídeo feito", default=False)
    concluido_em = models.DateTimeField("concluído em", null=True, blank=True)

    objects = ActiveManager()
    all_objects = models.Manager()

    class Meta:
        db_table = "anuncios_atualizar"
        verbose_name = "Anúncio para Atualizar"
        verbose_name_plural = "Anúncios para Atualizar"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.mlb} - {self.titulo[:40]}"

    @property
    def concluido(self):
        if self.precisa_foto and not self.foto_feito:
            return False
        if self.precisa_video and not self.video_feito:
            return False
        return True
