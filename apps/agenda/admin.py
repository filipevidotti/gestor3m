from django.contrib import admin

from .models import Agendamento, ConfiguracaoAgenda, HorarioTrabalho


class HorarioTrabalhoInline(admin.TabularInline):
    model = HorarioTrabalho
    extra = 0


@admin.register(ConfiguracaoAgenda)
class ConfiguracaoAgendaAdmin(admin.ModelAdmin):
    list_display = ("consultor", "slug", "duracao_padrao", "dias_visiveis")
    search_fields = ("consultor__first_name", "consultor__last_name", "slug")
    inlines = [HorarioTrabalhoInline]


@admin.register(Agendamento)
class AgendamentoAdmin(admin.ModelAdmin):
    list_display = ("nome_cliente", "consultor", "data_hora", "duracao", "status")
    list_filter = ("status", "consultor")
    search_fields = ("nome_cliente", "email_cliente")
    date_hierarchy = "data_hora"
