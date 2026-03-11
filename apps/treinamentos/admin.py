from django.contrib import admin
from .models import Treinamento, TreinamentoRealizado


@admin.register(Treinamento)
class TreinamentoAdmin(admin.ModelAdmin):
    list_display = ("titulo", "categoria", "duracao_minutos")
    list_filter = ("categoria",)
    search_fields = ("titulo",)


@admin.register(TreinamentoRealizado)
class TreinamentoRealizadoAdmin(admin.ModelAdmin):
    list_display = ("treinamento", "cliente", "data")
    list_filter = ("treinamento",)
    date_hierarchy = "data"
