from django.contrib import admin
from .models import BenchmarkSegmento, DiagnosticTemplate, DiagnosticQuestion, Diagnostic, DiagnosticAnswer


class DiagnosticQuestionInline(admin.TabularInline):
    model = DiagnosticQuestion
    extra = 3


@admin.register(DiagnosticTemplate)
class DiagnosticTemplateAdmin(admin.ModelAdmin):
    list_display = ("nome", "total_perguntas", "created_at")
    inlines = [DiagnosticQuestionInline]


class DiagnosticAnswerInline(admin.TabularInline):
    model = DiagnosticAnswer
    extra = 0
    readonly_fields = ("score",)


@admin.register(Diagnostic)
class DiagnosticAdmin(admin.ModelAdmin):
    list_display = ("cliente", "template", "mes", "ano", "status", "score")
    list_filter = ("status", "ano", "template")
    search_fields = ("cliente__empresa",)
    inlines = [DiagnosticAnswerInline]


@admin.register(BenchmarkSegmento)
class BenchmarkSegmentoAdmin(admin.ModelAdmin):
    list_display = ("segmento", "score_medio", "total_diagnosticos", "atualizado_em")
    readonly_fields = ("scores_por_categoria", "total_diagnosticos", "atualizado_em")
    actions = ["recalcular_benchmarks"]

    @admin.action(description="Recalcular benchmarks selecionados")
    def recalcular_benchmarks(self, request, queryset):
        for bm in queryset:
            BenchmarkSegmento.recalcular(bm.segmento)
        self.message_user(request, f"{queryset.count()} benchmarks recalculados.")
