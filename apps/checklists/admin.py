from django.contrib import admin
from .models import (
    ChecklistCategory, ChecklistTemplate, ChecklistTemplateItem,
    ChecklistExecution, ChecklistExecutionItem, Evidence,
)


@admin.register(ChecklistCategory)
class ChecklistCategoryAdmin(admin.ModelAdmin):
    list_display = ("nome", "ordem")
    ordering = ("ordem",)


class ChecklistTemplateItemInline(admin.TabularInline):
    model = ChecklistTemplateItem
    extra = 3


@admin.register(ChecklistTemplate)
class ChecklistTemplateAdmin(admin.ModelAdmin):
    list_display = ("nome", "target_audience", "tipo", "total_itens")
    list_filter = ("target_audience", "tipo")
    inlines = [ChecklistTemplateItemInline]


class ChecklistExecutionItemInline(admin.TabularInline):
    model = ChecklistExecutionItem
    extra = 0
    readonly_fields = ("completed_at", "completed_by")


@admin.register(ChecklistExecution)
class ChecklistExecutionAdmin(admin.ModelAdmin):
    list_display = ("template", "cliente", "executor", "status", "score")
    list_filter = ("status", "template")
    inlines = [ChecklistExecutionItemInline]
