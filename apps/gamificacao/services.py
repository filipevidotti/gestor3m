from datetime import date, timedelta

from django.db.models import Sum

from .models import Achievement, Score, Streak, UserAchievement


def registrar_pontos(usuario, pontos, categoria, descricao, referencia_id=None):
    """Registra pontos e atualiza streak."""
    Score.objects.create(
        usuario=usuario,
        pontos=pontos,
        categoria=categoria,
        descricao=descricao,
        referencia_id=referencia_id,
    )
    atualizar_streak(usuario)
    verificar_conquistas(usuario)


def atualizar_streak(usuario):
    """Atualiza streak de atividade diaria."""
    streak, _ = Streak.objects.get_or_create(usuario=usuario)
    hoje = date.today()

    if streak.ultimo_dia == hoje:
        return

    if streak.ultimo_dia == hoje - timedelta(days=1):
        streak.dias_consecutivos += 1
    else:
        streak.dias_consecutivos = 1

    if streak.dias_consecutivos > streak.maior_sequencia:
        streak.maior_sequencia = streak.dias_consecutivos

    streak.ultimo_dia = hoje
    streak.save()


def get_total_pontos(usuario):
    """Retorna total de pontos do usuario."""
    return Score.objects.filter(usuario=usuario).aggregate(
        total=Sum("pontos")
    )["total"] or 0


def get_ranking(role=None, limit=10):
    """Retorna ranking de usuarios por pontos totais."""
    from django.contrib.auth import get_user_model
    User = get_user_model()

    qs = User.objects.annotate(
        total_pontos=Sum("scores__pontos")
    ).filter(total_pontos__gt=0)

    if role:
        qs = qs.filter(role=role)

    return qs.order_by("-total_pontos")[:limit]


def verificar_conquistas(usuario):
    """Verifica e desbloqueia conquistas atingidas."""
    from apps.checklists.models import ChecklistExecution
    from apps.tarefas.models import Tarefa

    role = usuario.role
    conquistas_existentes = set(
        UserAchievement.objects.filter(usuario=usuario).values_list(
            "achievement_id", flat=True
        )
    )

    if role in ("consultor", "gestor"):
        publicos = ["consultor", "ambos"]
    else:
        publicos = ["seller", "ambos"]

    achievements = Achievement.objects.filter(publico__in=publicos).exclude(
        pk__in=conquistas_existentes
    )

    # Metricas
    metricas = {
        "checklists_concluidos": ChecklistExecution.objects.filter(
            executor=usuario, status="completed"
        ).count(),
        "tarefas_concluidas": Tarefa.objects.filter(
            responsavel=usuario, status="concluido"
        ).count(),
        "total_pontos": get_total_pontos(usuario),
    }

    try:
        metricas["streak_dias"] = usuario.streak.dias_consecutivos
        metricas["maior_streak"] = usuario.streak.maior_sequencia
    except Streak.DoesNotExist:
        metricas["streak_dias"] = 0
        metricas["maior_streak"] = 0

    for achievement in achievements:
        valor_atual = metricas.get(achievement.criterio_campo, 0)
        if valor_atual >= achievement.criterio_valor:
            UserAchievement.objects.create(
                usuario=usuario, achievement=achievement
            )
            if achievement.pontos_recompensa > 0:
                Score.objects.create(
                    usuario=usuario,
                    pontos=achievement.pontos_recompensa,
                    categoria="bonus",
                    descricao=f"Conquista: {achievement.nome}",
                )
