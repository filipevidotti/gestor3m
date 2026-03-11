from django.contrib.auth.models import AbstractUser
from django.db import models


class Modulo(models.Model):
    """Módulo do sistema com permissão configurável por usuário."""

    slug = models.CharField("slug", max_length=50, unique=True)
    nome = models.CharField("nome", max_length=100)
    icone = models.CharField("ícone", max_length=50, blank=True)
    ordem = models.PositiveIntegerField("ordem", default=0)

    class Meta:
        db_table = "accounts_modulo"
        verbose_name = "Módulo"
        verbose_name_plural = "Módulos"
        ordering = ["ordem", "nome"]

    def __str__(self):
        return self.nome


class User(AbstractUser):
    class Role(models.TextChoices):
        GESTOR = "gestor", "Gestor"
        CONSULTOR = "consultor", "Consultor"
        SELLER = "seller", "Seller"
        FUNCIONARIO = "funcionario", "Funcionário"
        COMERCIAL = "comercial", "Comercial"

    role = models.CharField("papel", max_length=20, choices=Role.choices, default=Role.SELLER)
    telefone = models.CharField("telefone", max_length=20, blank=True)
    avatar = models.ImageField("avatar", upload_to="avatars/", blank=True, null=True)
    modulos = models.ManyToManyField(
        Modulo,
        blank=True,
        verbose_name="módulos permitidos",
        help_text="Módulos que este usuário pode acessar. Gestores têm acesso total.",
    )

    class Meta:
        db_table = "accounts_user"
        verbose_name = "Usuário"
        verbose_name_plural = "Usuários"

    def __str__(self):
        return f"{self.get_full_name()} ({self.get_role_display()})"

    @property
    def is_gestor(self):
        return self.role == self.Role.GESTOR

    @property
    def is_consultor(self):
        return self.role == self.Role.CONSULTOR

    @property
    def is_seller(self):
        return self.role == self.Role.SELLER

    @property
    def is_funcionario(self):
        return self.role == self.Role.FUNCIONARIO

    @property
    def is_comercial(self):
        return self.role == self.Role.COMERCIAL

    def tem_modulo(self, slug):
        """Verifica se o usuário tem acesso a um módulo."""
        if self.is_gestor:
            return True
        return self.modulos.filter(slug=slug).exists()

    def get_modulos_slugs(self):
        """Retorna set de slugs dos módulos permitidos."""
        if self.is_gestor:
            return set(Modulo.objects.values_list("slug", flat=True))
        return set(self.modulos.values_list("slug", flat=True))
