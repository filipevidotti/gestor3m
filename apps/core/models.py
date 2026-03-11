from django.db import models


class BaseModel(models.Model):
    created_at = models.DateTimeField("criado em", auto_now_add=True)
    updated_at = models.DateTimeField("atualizado em", auto_now=True)
    is_active = models.BooleanField("ativo", default=True)

    class Meta:
        abstract = True
        ordering = ["-created_at"]

    def soft_delete(self):
        self.is_active = False
        self.save(update_fields=["is_active", "updated_at"])

    def restore(self):
        self.is_active = True
        self.save(update_fields=["is_active", "updated_at"])


class ActiveManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(is_active=True)


class Configuracao(models.Model):
    """Configurações globais do sistema (singleton por chave)."""

    class Categoria(models.TextChoices):
        GOOGLE = "google", "Google (Calendar)"
        EVOLUTION = "evolution", "Evolution API (WhatsApp)"
        BREVO = "brevo", "Brevo (E-mail)"
        ASAAS = "asaas", "Asaas (Pagamentos)"
        AUTENTIQUE = "autentique", "Autentique (Assinatura Digital)"
        IA = "ia", "Inteligência Artificial"
        GERAL = "geral", "Geral"

    categoria = models.CharField(
        "categoria", max_length=30, choices=Categoria.choices, default=Categoria.GERAL
    )
    chave = models.CharField("chave", max_length=100, unique=True)
    valor = models.TextField("valor", blank=True)
    descricao = models.CharField("descrição", max_length=300, blank=True)
    is_secret = models.BooleanField(
        "é segredo?",
        default=False,
        help_text="Valores secretos são mascarados na listagem do admin.",
    )

    class Meta:
        db_table = "core_configuracao"
        verbose_name = "Configuração"
        verbose_name_plural = "Configurações"
        ordering = ["categoria", "chave"]

    def __str__(self):
        return f"[{self.get_categoria_display()}] {self.chave}"

    @classmethod
    def get(cls, chave, default=""):
        """Busca valor de configuração pelo slug da chave."""
        try:
            return cls.objects.get(chave=chave).valor
        except cls.DoesNotExist:
            return default
