from django.contrib import admin

from .models import PesquisaNPS, RespostaNPS


class RespostaNPSInline(admin.TabularInline):
    model = RespostaNPS
    extra = 0
    readonly_fields = ("nota", "comentario", "respondido_em", "token")


@admin.register(PesquisaNPS)
class PesquisaNPSAdmin(admin.ModelAdmin):
    list_display = ("titulo", "total_respostas", "nps_score", "created_at")
    inlines = [RespostaNPSInline]


@admin.register(RespostaNPS)
class RespostaNPSAdmin(admin.ModelAdmin):
    list_display = ("pesquisa", "cliente", "nota", "classificacao", "respondido_em")
    list_filter = ("pesquisa", "nota")
    search_fields = ("cliente__empresa",)
    readonly_fields = ("token",)
