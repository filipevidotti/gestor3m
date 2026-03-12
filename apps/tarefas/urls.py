from django.urls import path

from . import views

app_name = "tarefas"

urlpatterns = [
    # Lista e Kanban
    path("", views.listar, name="listar"),
    path("kanban/", views.kanban, name="kanban"),
    path("kanban/mover/", views.kanban_mover, name="kanban_mover"),
    # CRUD
    path("nova/", views.criar, name="criar"),
    path("<int:pk>/", views.detalhe, name="detalhe"),
    path("<int:pk>/editar/", views.editar, name="editar"),
    path("<int:pk>/excluir/", views.excluir, name="excluir"),
    path("<int:pk>/status/", views.alterar_status, name="alterar_status"),
    # Subtarefas
    path("<int:pk>/subtarefa/", views.adicionar_subtarefa, name="adicionar_subtarefa"),
    path("subtarefa/<int:pk>/toggle/", views.toggle_subtarefa, name="toggle_subtarefa"),
    path("subtarefa/<int:pk>/excluir/", views.excluir_subtarefa, name="excluir_subtarefa"),
    # Comentarios
    path("<int:pk>/comentario/", views.adicionar_comentario, name="adicionar_comentario"),
    # Config etapas
    path("etapas/", views.etapa_config, name="etapa_config"),
    path("etapas/<int:pk>/editar/", views.etapa_config_editar, name="etapa_config_editar"),
    path("etapas/<int:pk>/excluir/", views.etapa_config_excluir, name="etapa_config_excluir"),
    # Config etiquetas
    path("etiquetas/", views.etiqueta_config, name="etiqueta_config"),
    # Config tipos
    path("tipos/", views.tipo_config, name="tipo_config"),
    path("tipos/<int:pk>/editar/", views.tipo_config_editar, name="tipo_config_editar"),
    path("tipos/<int:pk>/excluir/", views.tipo_config_excluir, name="tipo_config_excluir"),
]
