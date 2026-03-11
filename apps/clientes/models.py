from django.db import models
from apps.core.models import BaseModel, ActiveManager


class EtapaPipeline(BaseModel):
    """Etapas configuraveis do pipeline de consultoria."""
    nome = models.CharField("nome", max_length=100)
    descricao = models.CharField("descricao", max_length=200, blank=True)
    cor = models.CharField("cor", max_length=7, default="#3b82f6")
    ordem = models.PositiveIntegerField("ordem", default=0)

    class Meta:
        db_table = "etapas_pipeline"
        verbose_name = "Etapa do Pipeline"
        verbose_name_plural = "Etapas do Pipeline"
        ordering = ["ordem"]

    def __str__(self):
        return self.nome


class Cliente(BaseModel):
    class Status(models.TextChoices):
        ONBOARDING = "onboarding", "Onboarding"
        ATIVO = "ativo", "Ativo"
        PAUSADO = "pausado", "Pausado"
        ENCERRADO = "encerrado", "Encerrado"

    class TipoConsultoria(models.TextChoices):
        ESTRATEGICA = "estrategica", "Estratégica"
        OPERACIONAL = "operacional", "Operacional"

    empresa = models.CharField("empresa", max_length=200)
    cnpj = models.CharField("CNPJ", max_length=18, blank=True)
    nicho = models.CharField("nicho", max_length=100, blank=True)
    telefone = models.CharField("telefone", max_length=20, blank=True)
    email = models.EmailField("e-mail", blank=True)
    logo = models.ImageField("logo", upload_to="clientes/logos/", blank=True, null=True)

    # Dados Mercado Livre
    ml_nickname = models.CharField("apelido ML", max_length=100, blank=True)
    ml_seller_id = models.CharField("seller ID ML", max_length=50, blank=True)
    ml_reputacao = models.CharField("reputação ML", max_length=50, blank=True)

    consultor = models.ForeignKey(
        "accounts.User",
        on_delete=models.PROTECT,
        related_name="clientes",
        verbose_name="consultor",
        limit_choices_to={"role": "consultor"},
    )
    tipo_consultoria = models.CharField(
        "tipo de consultoria", max_length=20, choices=TipoConsultoria.choices
    )
    data_inicio = models.DateField("data de início")
    status = models.CharField(
        "status", max_length=20, choices=Status.choices, default=Status.ONBOARDING
    )
    etapa = models.ForeignKey(
        EtapaPipeline,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="clientes",
        verbose_name="etapa pipeline",
    )
    observacoes = models.TextField("observações", blank=True)
    usuario = models.OneToOneField(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="cliente_perfil",
        verbose_name="acesso seller",
        limit_choices_to={"role": "seller"},
    )

    objects = ActiveManager()
    all_objects = models.Manager()

    class Meta:
        db_table = "clientes"
        verbose_name = "Cliente"
        verbose_name_plural = "Clientes"
        ordering = ["empresa"]

    def __str__(self):
        return self.empresa


class Funcionario(BaseModel):
    """Funcionário de um seller, com acesso restrito ao portal."""

    usuario = models.OneToOneField(
        "accounts.User",
        on_delete=models.CASCADE,
        related_name="funcionario_perfil",
        verbose_name="usuário",
    )
    cliente = models.ForeignKey(
        Cliente,
        on_delete=models.CASCADE,
        related_name="funcionarios",
        verbose_name="empresa",
    )
    cargo = models.CharField("cargo", max_length=100, blank=True)
    cadastrado_por = models.ForeignKey(
        "accounts.User",
        on_delete=models.PROTECT,
        related_name="+",
        verbose_name="cadastrado por",
    )

    class Meta:
        db_table = "funcionarios"
        verbose_name = "Funcionário"
        verbose_name_plural = "Funcionários"
        ordering = ["usuario__first_name"]

    def __str__(self):
        return f"{self.usuario.get_full_name()} — {self.cliente.empresa}"


class Atividade(BaseModel):
    cliente = models.ForeignKey(
        Cliente, on_delete=models.CASCADE, related_name="atividades"
    )
    descricao = models.TextField("descrição")
    autor = models.ForeignKey(
        "accounts.User", on_delete=models.PROTECT, verbose_name="autor"
    )

    class Meta:
        db_table = "atividades"
        verbose_name = "Atividade"
        verbose_name_plural = "Atividades"

    def __str__(self):
        return f"{self.cliente} - {self.descricao[:50]}"
