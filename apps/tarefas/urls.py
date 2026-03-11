from django.urls import path
from . import views

app_name = "tarefas"

urlpatterns = [
    path("", views.listar, name="listar"),
    path("kanban/", views.kanban, name="kanban"),
    path("kanban/mover/", views.kanban_mover, name="kanban_mover"),
    path("nova/", views.criar, name="criar"),
    path("<int:pk>/editar/", views.editar, name="editar"),
    path("<int:pk>/excluir/", views.excluir, name="excluir"),
    path("<int:pk>/status/", views.alterar_status, name="alterar_status"),
    # Tipo config
    path("tipos/", views.tipo_config, name="tipo_config"),
    path("tipos/<int:pk>/editar/", views.tipo_config_editar, name="tipo_config_editar"),
    path("tipos/<int:pk>/excluir/", views.tipo_config_excluir, name="tipo_config_excluir"),
]
