from django.contrib import admin
from .models import Notificacao


@admin.register(Notificacao)
class NotificacaoAdmin(admin.ModelAdmin):
    list_display = ("titulo", "destinatario", "tipo", "lida", "created_at")
    list_filter = ("tipo", "lida")
    search_fields = ("titulo", "mensagem")
