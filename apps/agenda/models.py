import uuid

from django.db import models
from django.utils.text import slugify

from apps.core.models import BaseModel


class ConfiguracaoAgenda(BaseModel):
    consultor = models.OneToOneField(
        "accounts.User",
        on_delete=models.CASCADE,
        related_name="agenda_config",
        limit_choices_to={"role__in": ["consultor", "gestor"]},
    )
    slug = models.SlugField("slug público", max_length=100, unique=True)
    titulo = models.CharField("título da agenda", max_length=200, blank=True)
    descricao = models.TextField("descrição", blank=True)
    duracao_padrao = models.PositiveIntegerField("duração padrão (min)", default=60)
    antecedencia_minima = models.PositiveIntegerField(
        "antecedência mínima (horas)", default=24
    )
    dias_visiveis = models.PositiveIntegerField("dias visíveis", default=14)

    # Google Calendar
    google_token = models.JSONField("token Google", null=True, blank=True)
    google_calendar_id = models.CharField(
        "ID do calendário Google", max_length=300, blank=True
    )

    class Meta:
        db_table = "agenda_configuracoes"
        verbose_name = "Configuração de Agenda"
        verbose_name_plural = "Configurações de Agenda"

    def __str__(self):
        return f"Agenda de {self.consultor.get_full_name()}"

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.consultor.get_full_name())
            slug = base
            n = 1
            while ConfiguracaoAgenda.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base}-{n}"
                n += 1
            self.slug = slug
        super().save(*args, **kwargs)


class HorarioTrabalho(models.Model):
    class DiaSemana(models.IntegerChoices):
        SEGUNDA = 0, "Segunda-feira"
        TERCA = 1, "Terça-feira"
        QUARTA = 2, "Quarta-feira"
        QUINTA = 3, "Quinta-feira"
        SEXTA = 4, "Sexta-feira"
        SABADO = 5, "Sábado"
        DOMINGO = 6, "Domingo"

    config = models.ForeignKey(
        ConfiguracaoAgenda,
        on_delete=models.CASCADE,
        related_name="horarios",
    )
    dia_semana = models.IntegerField("dia da semana", choices=DiaSemana.choices)
    hora_inicio = models.TimeField("hora início")
    hora_fim = models.TimeField("hora fim")
    ativo = models.BooleanField("ativo", default=True)

    class Meta:
        db_table = "agenda_horarios"
        verbose_name = "Horário de Trabalho"
        verbose_name_plural = "Horários de Trabalho"
        ordering = ["dia_semana", "hora_inicio"]
        unique_together = [("config", "dia_semana", "hora_inicio")]

    def __str__(self):
        return f"{self.get_dia_semana_display()} {self.hora_inicio:%H:%M}-{self.hora_fim:%H:%M}"


class Agendamento(BaseModel):
    class Status(models.TextChoices):
        CONFIRMADO = "confirmado", "Confirmado"
        CANCELADO = "cancelado", "Cancelado"
        REALIZADO = "realizado", "Realizado"
        NAO_COMPARECEU = "nao_compareceu", "Não Compareceu"

    consultor = models.ForeignKey(
        "accounts.User",
        on_delete=models.PROTECT,
        related_name="agendamentos",
        limit_choices_to={"role__in": ["consultor", "gestor"]},
    )
    data_hora = models.DateTimeField("data/hora")
    duracao = models.PositiveIntegerField("duração (min)", default=60)

    # Dados de quem agendou
    nome_cliente = models.CharField("nome", max_length=200)
    email_cliente = models.EmailField("e-mail")
    telefone_cliente = models.CharField("telefone", max_length=20, blank=True)
    observacao = models.TextField("observação", blank=True)

    # Vínculo opcional com cliente cadastrado
    cliente = models.ForeignKey(
        "clientes.Cliente",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="agendamentos",
    )

    # Google Calendar
    google_event_id = models.CharField(
        "ID evento Google", max_length=300, blank=True
    )

    status = models.CharField(
        "status", max_length=20, choices=Status.choices, default=Status.CONFIRMADO
    )
    token_cancelamento = models.UUIDField(
        "token cancelamento", default=uuid.uuid4, unique=True, editable=False
    )

    class Meta:
        db_table = "agenda_agendamentos"
        verbose_name = "Agendamento"
        verbose_name_plural = "Agendamentos"
        ordering = ["data_hora"]

    def __str__(self):
        return f"{self.nome_cliente} - {self.data_hora:%d/%m/%Y %H:%M}"
