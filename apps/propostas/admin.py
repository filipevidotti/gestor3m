from django.contrib import admin

from .models import Proposta, PropostaServico, PropostaVisualizacao, Servico


@admin.register(Servico)
class ServicoAdmin(admin.ModelAdmin):
    list_display = ("nome", "preco_sugerido", "ordem", "is_active")
    list_editable = ("ordem",)
    search_fields = ("nome",)


class PropostaServicoInline(admin.TabularInline):
    model = PropostaServico
    extra = 0


@admin.register(Proposta)
class PropostaAdmin(admin.ModelAdmin):
    list_display = ("nome_display", "consultor", "tipo_seller", "status", "created_at")
    list_filter = ("status", "tipo_seller", "marketplace")
    search_fields = ("lead_nome", "lead_loja", "lead_email")
    readonly_fields = ("token", "visualizacoes")
    inlines = [PropostaServicoInline]


@admin.register(PropostaVisualizacao)
class PropostaVisualizacaoAdmin(admin.ModelAdmin):
    list_display = ("proposta", "ip", "data")
    list_filter = ("data",)
