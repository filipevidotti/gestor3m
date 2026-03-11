from django.contrib import admin
from .models import Consultor


@admin.register(Consultor)
class ConsultorAdmin(admin.ModelAdmin):
    list_display = ("usuario", "especialidade", "max_clientes", "clientes_ativos")
    search_fields = ("usuario__first_name", "usuario__last_name")
