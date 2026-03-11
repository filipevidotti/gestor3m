from django.contrib import admin
from .models import PlanoAcao, ItemPlano


class ItemPlanoInline(admin.TabularInline):
    model = ItemPlano
    extra = 1


@admin.register(PlanoAcao)
class PlanoAcaoAdmin(admin.ModelAdmin):
    list_display = ("titulo", "cliente", "tipo", "created_at")
    list_filter = ("tipo",)
    search_fields = ("titulo", "cliente__nome")
    inlines = [ItemPlanoInline]
