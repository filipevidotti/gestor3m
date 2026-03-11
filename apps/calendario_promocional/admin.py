from django.contrib import admin
from .models import DataPromocional, PreparacaoPromocional


@admin.register(DataPromocional)
class DataPromocionalAdmin(admin.ModelAdmin):
    list_display = ("nome", "tipo", "importancia", "data_inicio", "data_fim", "is_inscricao_aberta")
    list_filter = ("tipo", "importancia")
    search_fields = ("nome",)
    ordering = ("data_inicio",)


@admin.register(PreparacaoPromocional)
class PreparacaoPromocionalAdmin(admin.ModelAdmin):
    list_display = ("cliente", "data_promocional", "status", "desconto_medio", "budget_ads")
    list_filter = ("status", "data_promocional")
    search_fields = ("cliente__empresa",)
