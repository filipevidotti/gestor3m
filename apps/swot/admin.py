from django.contrib import admin

from .models import AnaliseSwot


@admin.register(AnaliseSwot)
class AnaliseSwotAdmin(admin.ModelAdmin):
    list_display = ("cliente", "consultor", "data_analise", "created_at")
    list_filter = ("data_analise",)
    search_fields = ("cliente__empresa",)
    raw_id_fields = ("cliente", "consultor", "reuniao")
