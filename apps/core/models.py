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
        UAZAPI = "uazapi", "UAZAPI (WhatsApp)"
        GOOGLE = "google", "Google (Calendar)"
        EVOLUTION = "evolution", "Evolution API (WhatsApp) — Legado"
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


class GrupoWhatsApp(BaseModel):
    """Grupo WhatsApp sincronizado via UAZAPI, vinculável a um cliente."""

    group_id = models.CharField(
        "ID do grupo", max_length=100, unique=True,
        help_text="ID retornado pela API (ex: 5511999999999-1234567890@g.us)",
    )
    nome = models.CharField("nome do grupo", max_length=300)
    descricao = models.TextField("descrição", blank=True)
    foto_url = models.URLField("foto URL", blank=True)
    participantes_count = models.PositiveIntegerField("nº participantes", default=0)

    cliente = models.ForeignKey(
        "clientes.Cliente",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="grupos_whatsapp",
        verbose_name="cliente vinculado",
    )

    sincronizado_em = models.DateTimeField("última sincronização", null=True, blank=True)
    ultima_mensagem_enviada = models.DateTimeField(
        "última mensagem enviada", null=True, blank=True,
    )
    ultima_interacao = models.DateTimeField(
        "última interação", null=True, blank=True,
    )

    objects = ActiveManager()
    all_objects = models.Manager()

    class Meta:
        db_table = "core_grupo_whatsapp"
        verbose_name = "Grupo WhatsApp"
        verbose_name_plural = "Grupos WhatsApp"
        ordering = ["nome"]

    def __str__(self):
        return self.nome

    @property
    def dias_sem_interacao(self):
        if not self.ultima_interacao:
            return None
        from django.utils import timezone as tz
        return (tz.now() - self.ultima_interacao).days


class MensagemGrupo(BaseModel):
    """Mensagem de grupo WhatsApp (enviada pelo sistema ou recebida via webhook)."""

    ORIGEM_CHOICES = [
        ("sistema", "Sistema"),
        ("webhook", "WhatsApp"),
    ]

    grupo = models.ForeignKey(
        GrupoWhatsApp,
        on_delete=models.CASCADE,
        related_name="mensagens",
        verbose_name="grupo",
    )
    texto = models.TextField("mensagem")
    enviado_por = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="enviado por (sistema)",
    )
    enviado_em = models.DateTimeField("enviado em", auto_now_add=True)
    sucesso = models.BooleanField("enviado com sucesso", default=True)
    erro = models.TextField("erro", blank=True)

    # Campos para mensagens recebidas via webhook
    remetente_nome = models.CharField(
        "nome do remetente", max_length=200, blank=True,
    )
    remetente_telefone = models.CharField(
        "telefone do remetente", max_length=50, blank=True,
    )
    origem = models.CharField(
        "origem", max_length=20, choices=ORIGEM_CHOICES, default="sistema",
    )

    class Meta:
        db_table = "core_mensagem_grupo"
        verbose_name = "Mensagem de Grupo"
        verbose_name_plural = "Mensagens de Grupo"
        ordering = ["-enviado_em"]

    def __str__(self):
        return f"{self.grupo.nome} - {self.enviado_em:%d/%m %H:%M}"
