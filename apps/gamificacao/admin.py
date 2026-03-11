from django.contrib import admin
from .models import Achievement, Score, Streak, UserAchievement


@admin.register(Score)
class ScoreAdmin(admin.ModelAdmin):
    list_display = ["usuario", "pontos", "categoria", "descricao", "created_at"]
    list_filter = ["categoria"]
    search_fields = ["usuario__first_name", "descricao"]


@admin.register(Achievement)
class AchievementAdmin(admin.ModelAdmin):
    list_display = ["nome", "tipo", "criterio_campo", "criterio_valor", "pontos_recompensa", "publico"]
    list_filter = ["tipo", "publico"]


@admin.register(UserAchievement)
class UserAchievementAdmin(admin.ModelAdmin):
    list_display = ["usuario", "achievement", "desbloqueado_em"]
    list_filter = ["achievement"]


@admin.register(Streak)
class StreakAdmin(admin.ModelAdmin):
    list_display = ["usuario", "dias_consecutivos", "maior_sequencia", "ultimo_dia"]
