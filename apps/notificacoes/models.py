from django.db import models
from apps.core.models import BaseModel


class Notificacao(BaseModel):
    class Tipo(models.TextChoices):
        TAREFA_ATRASADA = "tarefa_atrasada", "Tarefa Atrasada"
        INADIMPLENCIA = "inadimplencia", "Inadimplência"
        REUNIAO_MARCADA = "reuniao_marcada", "Reunião Marcada"
        DIAGNOSTICO_PENDENTE = "diagnostico_pendente", "Diagnóstico Pendente"
        SEM_REUNIAO = "sem_reuniao", "Sem Reunião há 30 dias"
        GERAL = "geral", "Geral"

    destinatario = models.ForeignKey(
        "accounts.User", on_delete=models.CASCADE, related_name="notificacoes"
    )
    tipo = models.CharField("tipo", max_length=30, choices=Tipo.choices, default=Tipo.GERAL)
    titulo = models.CharField("título", max_length=200)
    mensagem = models.TextField("mensagem")
    lida = models.BooleanField("lida", default=False)
    link = models.CharField("link", max_length=500, blank=True)
    enviado_whatsapp = models.BooleanField("enviado WhatsApp", default=False)
    enviado_email = models.BooleanField("enviado e-mail", default=False)

    class Meta:
        db_table = "notificacoes"
        verbose_name = "Notificação"
        verbose_name_plural = "Notificações"

    def __str__(self):
        return f"{self.titulo} -> {self.destinatario}"

    def enviar_multicanal(self, telefone="", email=""):
        """Tenta enviar por WhatsApp e/ou e-mail se dados disponíveis."""
        from apps.core.services.evolution import enviar_mensagem
        from apps.core.services.brevo import enviar_email as brevo_email

        if telefone and not self.enviado_whatsapp:
            texto = f"*{self.titulo}*\n\n{self.mensagem}"
            if enviar_mensagem(telefone, texto):
                self.enviado_whatsapp = True

        if email and not self.enviado_email:
            html = (
                f"<h2>{self.titulo}</h2>"
                f"<p>{self.mensagem}</p>"
                f"<p><small>3M Consultoria</small></p>"
            )
            nome = self.destinatario.get_full_name()
            if brevo_email(email, nome, self.titulo, html):
                self.enviado_email = True

        if self.enviado_whatsapp or self.enviado_email:
            self.save(update_fields=["enviado_whatsapp", "enviado_email"])
