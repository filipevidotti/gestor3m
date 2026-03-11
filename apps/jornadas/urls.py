from django.urls import path

from . import views

app_name = "jornadas"

urlpatterns = [
    # Config templates (gestor)
    path("templates/", views.config_templates, name="config_templates"),
    path("templates/novo/", views.criar_template, name="criar_template"),
    path("templates/<int:pk>/editar/", views.editar_template, name="editar_template"),
    path("templates/<int:pk>/excluir/", views.excluir_template, name="excluir_template"),
    path("templates/<int:pk>/etapas/", views.gerenciar_etapas, name="gerenciar_etapas"),

    # Jornada do cliente
    path("cliente/<int:cliente_pk>/", views.timeline_cliente, name="timeline_cliente"),
    path("cliente/<int:cliente_pk>/gerar/", views.gerar_jornada, name="gerar_jornada"),
    path("<int:pk>/recalibrar/", views.recalibrar, name="recalibrar"),
    path("etapa/<int:pk>/concluir/", views.concluir_etapa, name="concluir_etapa"),
    path("etapa/<int:pk>/status/", views.atualizar_status_etapa, name="atualizar_status"),
]
