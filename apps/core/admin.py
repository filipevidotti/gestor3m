from django.contrib import admin
from django.utils.html import format_html

from .models import Configuracao


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
