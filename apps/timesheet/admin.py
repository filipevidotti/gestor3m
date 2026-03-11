from django.contrib import admin

from .models import RegistroHoras


@admin.register(RegistroHoras)
class RegistroHorasAdmin(admin.ModelAdmin):
    list_display = ("consultor", "cliente", "data", "hora_inicio", "hora_fim", "categoria", "duracao_formatada")
    list_filter = ("categoria", "data", "consultor")
    search_fields = ("cliente__empresa", "consultor__first_name", "descricao")
    date_hierarchy = "data"
    raw_id_fields = ("consultor", "cliente")
