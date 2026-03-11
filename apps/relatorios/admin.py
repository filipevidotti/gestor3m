from django.contrib import admin

from .models import RelatorioMensal


@admin.register(RelatorioMensal)
class RelatorioMensalAdmin(admin.ModelAdmin):
    list_display = ("cliente", "mes", "ano", "enviado", "enviado_em", "created_at")
    list_filter = ("ano", "mes", "enviado")
    search_fields = ("cliente__empresa",)
    raw_id_fields = ("cliente",)
