from django.urls import path
from . import views

app_name = "diagnosticos"

urlpatterns = [
    # Templates (gestor)
    path("templates/", views.template_listar, name="template_listar"),
    path("templates/novo/", views.template_criar, name="template_criar"),
    path("templates/<int:pk>/editar/", views.template_editar, name="template_editar"),

    # Diagnósticos
    path("cliente/<int:cliente_pk>/", views.listar, name="listar"),
    path("cliente/<int:cliente_pk>/novo/", views.criar, name="criar"),
    path("<int:pk>/", views.detalhe, name="detalhe"),
    path("<int:pk>/executar/", views.executar, name="executar"),
    path("<int:pk>/executar/salvar/", views.salvar_respostas, name="salvar_respostas"),
    path("<int:pk>/completar/", views.completar, name="completar"),
    path("<int:pk>/repetir/", views.repetir, name="repetir"),
]
