from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.checklists.models import ChecklistExecution
from apps.tarefas.models import Tarefa

from .services import registrar_pontos


@receiver(post_save, sender=ChecklistExecution)
def pontuar_checklist(sender, instance, **kwargs):
    if instance.status == "completed" and instance.executor:
        # Evita pontuar duas vezes
        from .models import Score
        ja_pontuou = Score.objects.filter(
            usuario=instance.executor,
            categoria="checklist",
            referencia_id=instance.pk,
        ).exists()
        if not ja_pontuou:
            pontos = 50
            if instance.score and instance.score >= 90:
                pontos = 100
            elif instance.score and instance.score >= 70:
                pontos = 75

            registrar_pontos(
                usuario=instance.executor,
                pontos=pontos,
                categoria="checklist",
                descricao=f"Checklist: {instance.template.nome}",
                referencia_id=instance.pk,
            )


@receiver(post_save, sender=Tarefa)
def pontuar_tarefa(sender, instance, **kwargs):
    if instance.status == "concluido" and instance.responsavel:
        from .models import Score
        ja_pontuou = Score.objects.filter(
            usuario=instance.responsavel,
            categoria="tarefa",
            referencia_id=instance.pk,
        ).exists()
        if not ja_pontuou:
            registrar_pontos(
                usuario=instance.responsavel,
                pontos=25,
                categoria="tarefa",
                descricao=f"Tarefa concluida",
                referencia_id=instance.pk,
            )
