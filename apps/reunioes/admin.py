from django.contrib import admin
from .models import Reuniao


@admin.register(Reuniao)
class ReuniaoAdmin(admin.ModelAdmin):
    list_display = ("tipo", "cliente", "consultor", "data", "duracao_minutos")
    list_filter = ("tipo", "consultor")
    search_fields = ("cliente__nome",)
    date_hierarchy = "data"
