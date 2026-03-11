from django.db import models
from apps.core.models import BaseModel


class Reuniao(BaseModel):
    class Tipo(models.TextChoices):
        DIAGNOSTICO = "diagnostico", "Diagnóstico Inicial"
        TREINAMENTO_FULL = "treinamento_full", "Treinamento FULL"
        TREINAMENTO_REPUTACAO = "treinamento_reputacao", "Treinamento Reputação"
        TREINAMENTO_ADS = "treinamento_ads", "Treinamento ADS"
        REVISAO_MENSAL = "revisao_mensal", "Revisão Mensal"
        COMERCIAL = "comercial", "Reunião Comercial"
        OUTRO = "outro", "Outro"

    cliente = models.ForeignKey(
        "clientes.Cliente", on_delete=models.CASCADE, related_name="reunioes"
    )
    tipo = models.CharField("tipo", max_length=30, choices=Tipo.choices)
    data = models.DateTimeField("data/hora")
    duracao_minutos = models.PositiveIntegerField("duração (min)", default=60)
    consultor = models.ForeignKey(
        "accounts.User", on_delete=models.PROTECT, related_name="reunioes",
        limit_choices_to={"role__in": ["consultor", "gestor", "comercial"]},
    )
    participantes = models.TextField("participantes", blank=True)
    link_gravacao = models.URLField("link gravação", blank=True)
    resumo = models.TextField("resumo", blank=True)
    proximos_passos = models.TextField("próximos passos", blank=True)

    # Campos de IA
    audio_arquivo = models.FileField(
        "áudio da reunião", upload_to="reunioes/audios/%Y/%m/", blank=True,
    )
    transcricao_rascunho = models.TextField(
        "transcrição ao vivo", blank=True,
        help_text="Transcrição gerada em tempo real pelo navegador",
    )
    transcricao = models.TextField(
        "transcrição final", blank=True,
        help_text="Transcrição precisa gerada pelo Whisper",
    )

    class TranscricaoStatus(models.TextChoices):
        PENDENTE = "pendente", "Pendente"
        PROCESSANDO = "processando", "Processando"
        CONCLUIDA = "concluida", "Concluída"
        ERRO = "erro", "Erro"

    transcricao_status = models.CharField(
        "status transcrição", max_length=20,
        choices=TranscricaoStatus.choices, default=TranscricaoStatus.PENDENTE,
    )
    resumo_ia = models.TextField("resumo IA", blank=True)
    acoes_identificadas = models.JSONField(
        "ações identificadas", default=list, blank=True,
    )

    class SentimentoCliente(models.TextChoices):
        POSITIVO = "positivo", "Positivo"
        NEUTRO = "neutro", "Neutro"
        NEGATIVO = "negativo", "Negativo"
        MISTO = "misto", "Misto"

    sentimento_cliente = models.CharField(
        "sentimento do cliente", max_length=20,
        choices=SentimentoCliente.choices, blank=True,
    )
    insights_ia = models.JSONField(
        "insights IA", default=list, blank=True,
    )

    class Meta:
        db_table = "reunioes"
        verbose_name = "Reunião"
        verbose_name_plural = "Reuniões"

    def __str__(self):
        return f"{self.get_tipo_display()} - {self.cliente} ({self.data:%d/%m/%Y})"
