from django.contrib import admin

from .models import EtapaCRM, Lead, Oportunidade, AtividadeCRM, LembreteCRM


@admin.register(EtapaCRM)
class EtapaCRMAdmin(admin.ModelAdmin):
    list_display = ("nome", "ordem", "cor", "is_ganho", "is_perdido")
    list_editable = ("ordem",)


@admin.register(Lead)
class LeadAdmin(admin.ModelAdmin):
    list_display = ("nome", "empresa", "telefone", "email", "origem", "responsavel", "convertido", "created_at")
    list_filter = ("origem", "responsavel")
    search_fields = ("nome", "empresa", "email", "telefone")


@admin.register(Oportunidade)
class OportunidadeAdmin(admin.ModelAdmin):
    list_display = ("titulo", "lead", "etapa", "valor_estimado", "responsavel", "previsao_fechamento")
    list_filter = ("etapa", "responsavel")
    search_fields = ("titulo", "lead__nome", "lead__empresa")


@admin.register(AtividadeCRM)
class AtividadeCRMAdmin(admin.ModelAdmin):
    list_display = ("lead", "tipo", "autor", "created_at")
    list_filter = ("tipo",)


@admin.register(LembreteCRM)
class LembreteCRMAdmin(admin.ModelAdmin):
    list_display = ("lead", "descricao", "data_hora", "enviado", "responsavel")
    list_filter = ("enviado",)
