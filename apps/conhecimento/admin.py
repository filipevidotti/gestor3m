from django.contrib import admin

from .models import Artigo, CategoriaConhecimento


@admin.register(CategoriaConhecimento)
class CategoriaConhecimentoAdmin(admin.ModelAdmin):
    list_display = ("nome", "ordem")
    list_editable = ("ordem",)


@admin.register(Artigo)
class ArtigoAdmin(admin.ModelAdmin):
    list_display = ("titulo", "categoria", "autor", "visibilidade", "destaque", "visualizacoes", "created_at")
    list_filter = ("categoria", "visibilidade", "destaque")
    search_fields = ("titulo", "conteudo")
    prepopulated_fields = {"slug": ("titulo",)}
    raw_id_fields = ("autor",)
