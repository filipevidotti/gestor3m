from django.db import models
from apps.core.models import BaseModel


class Consultor(BaseModel):
    usuario = models.OneToOneField(
        "accounts.User",
        on_delete=models.CASCADE,
        related_name="consultor_perfil",
        limit_choices_to={"role": "consultor"},
    )
    especialidade = models.CharField("especialidade", max_length=200, blank=True)
    bio = models.TextField("bio", blank=True)
    max_clientes = models.PositiveIntegerField("máx. clientes", default=10)

    class Meta:
        db_table = "consultores"
        verbose_name = "Consultor"
        verbose_name_plural = "Consultores"

    def __str__(self):
        return self.usuario.get_full_name()

    @property
    def clientes_ativos(self):
        return self.usuario.clientes.filter(status="ativo").count()
