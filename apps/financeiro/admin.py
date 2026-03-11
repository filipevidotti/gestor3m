from django.contrib import admin
from .models import Contrato, ContratoTemplate, Pagamento


class PagamentoInline(admin.TabularInline):
    model = Pagamento
    extra = 0


@admin.register(ContratoTemplate)
class ContratoTemplateAdmin(admin.ModelAdmin):
    list_display = ("nome", "created_at", "is_active")


@admin.register(Contrato)
class ContratoAdmin(admin.ModelAdmin):
    list_display = ("cliente", "plano", "valor", "dia_vencimento", "data_inicio", "status_assinatura")
    search_fields = ("cliente__nome",)
    inlines = [PagamentoInline]


@admin.register(Pagamento)
class PagamentoAdmin(admin.ModelAdmin):
    list_display = ("contrato", "mes_referencia", "valor", "status", "data_pagamento")
    list_filter = ("status",)
    date_hierarchy = "mes_referencia"
