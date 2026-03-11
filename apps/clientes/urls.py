from django.urls import path
from . import views

app_name = "clientes"

urlpatterns = [
    path("", views.listar, name="listar"),
    path("novo/", views.criar, name="criar"),
    path("<int:pk>/", views.detalhe, name="detalhe"),
    path("<int:pk>/editar/", views.editar, name="editar"),
    path("<int:pk>/excluir/", views.excluir, name="excluir"),
    # Pipeline
    path("pipeline/", views.pipeline, name="pipeline"),
    path("pipeline/mover/", views.pipeline_mover, name="pipeline_mover"),
    path("pipeline/config/", views.pipeline_config, name="pipeline_config"),
    path("pipeline/config/<int:pk>/editar/", views.pipeline_config_editar, name="pipeline_config_editar"),
    path("pipeline/config/<int:pk>/excluir/", views.pipeline_config_excluir, name="pipeline_config_excluir"),
]
