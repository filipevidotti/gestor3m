from django.contrib import admin

from .models import InsightIA, HistoricoAnalise


@admin.register(InsightIA)
class InsightIAAdmin(admin.ModelAdmin):
    list_display = ["titulo", "tipo", "prioridade", "consultor", "cliente", "lido", "created_at"]
    list_filter = ["tipo", "prioridade", "lido"]
    search_fields = ["titulo", "descricao"]
    raw_id_fields = ["consultor", "cliente"]


@admin.register(HistoricoAnalise)
class HistoricoAnaliseAdmin(admin.ModelAdmin):
    list_display = ["tipo", "provider", "modelo", "cliente", "sucesso", "tokens_input", "tokens_output", "custo_estimado", "created_at"]
    list_filter = ["tipo", "provider", "sucesso"]
    readonly_fields = ["prompt_resumo", "resposta_resumo", "resposta_json"]
