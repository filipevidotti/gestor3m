from django.contrib import admin
from django.utils.html import format_html

from .models import Configuracao, GrupoWhatsApp


@admin.register(Configuracao)
class ConfiguracaoAdmin(admin.ModelAdmin):
    list_display = ("chave", "categoria", "valor_display", "descricao")
    list_filter = ("categoria",)
    search_fields = ("chave", "descricao")
    list_editable = ("descricao",)

    fieldsets = (
        (None, {
            "fields": ("categoria", "chave", "valor", "descricao", "is_secret"),
        }),
    )

    def valor_display(self, obj):
        if obj.is_secret and obj.valor:
            return format_html(
                '<span style="color: #999;">{}...{}</span>',
                obj.valor[:4],
                obj.valor[-4:] if len(obj.valor) > 8 else "****",
            )
        return obj.valor[:80] + ("..." if len(obj.valor) > 80 else "")

    valor_display.short_description = "Valor"


@admin.register(GrupoWhatsApp)
class GrupoWhatsAppAdmin(admin.ModelAdmin):
    list_display = ("nome", "group_id", "cliente", "participantes_count", "is_active", "sincronizado_em")
    list_filter = ("is_active",)
    search_fields = ("nome", "group_id", "cliente__empresa")
    list_editable = ("is_active", "cliente")
    raw_id_fields = ("cliente",)
    readonly_fields = ("group_id", "sincronizado_em")
