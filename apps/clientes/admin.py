from django.contrib import admin
from .models import Cliente, Atividade, EtapaPipeline, Funcionario


@admin.register(EtapaPipeline)
class EtapaPipelineAdmin(admin.ModelAdmin):
    list_display = ("nome", "cor", "ordem")
    list_editable = ("ordem",)
    ordering = ("ordem",)


class FuncionarioInline(admin.TabularInline):
    model = Funcionario
    extra = 0
    raw_id_fields = ("usuario", "cadastrado_por")


@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ("empresa", "consultor", "tipo_consultoria", "status", "etapa", "ml_nickname", "data_inicio")
    list_filter = ("status", "tipo_consultoria", "consultor", "etapa")
    search_fields = ("empresa", "cnpj", "ml_nickname")
    date_hierarchy = "data_inicio"
    inlines = [FuncionarioInline]


@admin.register(Funcionario)
class FuncionarioAdmin(admin.ModelAdmin):
    list_display = ("usuario", "cliente", "cargo", "is_active")
    list_filter = ("cliente", "is_active")
    search_fields = ("usuario__first_name", "usuario__last_name", "cargo")
    raw_id_fields = ("usuario", "cadastrado_por")


@admin.register(Atividade)
class AtividadeAdmin(admin.ModelAdmin):
    list_display = ("cliente", "descricao", "autor", "created_at")
    list_filter = ("cliente",)
