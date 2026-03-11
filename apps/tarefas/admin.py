from django.contrib import admin
from .models import Tarefa, TipoTarefa


@admin.register(TipoTarefa)
class TipoTarefaAdmin(admin.ModelAdmin):
    list_display = ("nome", "cor", "icone")
    search_fields = ("nome",)


@admin.register(Tarefa)
class TarefaAdmin(admin.ModelAdmin):
    list_display = ("descricao", "cliente", "responsavel", "tipo", "prioridade", "status", "prazo")
    list_filter = ("status", "prioridade", "tipo", "responsavel")
    search_fields = ("descricao", "cliente__empresa")
    date_hierarchy = "created_at"
