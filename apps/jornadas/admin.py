from django.contrib import admin

from .models import JornadaTemplate, EtapaTemplate, JornadaCliente, EtapaCliente


class EtapaTemplateInline(admin.TabularInline):
    model = EtapaTemplate
    extra = 1
    fields = [
        "nome", "tipo", "ordem", "dias_offset", "duracao_dias",
        "is_obrigatoria", "condicao",
        "checklist_template", "treinamento", "diagnostico_template",
    ]
    ordering = ["ordem"]


@admin.register(JornadaTemplate)
class JornadaTemplateAdmin(admin.ModelAdmin):
    list_display = ["nome", "descricao", "tipo_consultoria", "total_etapas", "is_active"]
    list_filter = ["tipo_consultoria", "is_active"]
    inlines = [EtapaTemplateInline]


class EtapaClienteInline(admin.TabularInline):
    model = EtapaCliente
    extra = 0
    fields = [
        "nome", "tipo", "ordem", "status",
        "data_prevista", "data_limite", "data_conclusao",
        "adicionada_por_ia",
    ]
    readonly_fields = ["adicionada_por_ia"]
    ordering = ["ordem"]


@admin.register(JornadaCliente)
class JornadaClienteAdmin(admin.ModelAdmin):
    list_display = ["nome", "cliente", "status", "progresso", "data_inicio", "recalibragens"]
    list_filter = ["status"]
    raw_id_fields = ["cliente"]
    inlines = [EtapaClienteInline]
    readonly_fields = ["justificativa_ia", "areas_foco", "progresso"]
