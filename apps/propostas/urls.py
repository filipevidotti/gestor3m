from django.urls import path

from . import views

app_name = "propostas"

urlpatterns = [
    # Serviços (gestor)
    path("servicos/", views.servicos_listar, name="servicos_listar"),
    path("servicos/criar/", views.servico_criar, name="servico_criar"),
    path("servicos/<int:pk>/editar/", views.servico_editar, name="servico_editar"),
    path("servicos/<int:pk>/excluir/", views.servico_excluir, name="servico_excluir"),

    # Propostas
    path("", views.listar, name="listar"),
    path("criar/", views.criar, name="criar"),
    path("<int:pk>/", views.detalhe, name="detalhe"),
    path("<int:pk>/editar/", views.editar, name="editar"),
    path("<int:pk>/excluir/", views.excluir, name="excluir"),

    # Wizard questionário
    path("<int:pk>/questionario/", views.questionario, name="questionario"),

    # Cálculo + IA
    path("<int:pk>/calcular/", views.calcular, name="calcular"),
    path("<int:pk>/gerar-ia/", views.gerar_ia, name="gerar_ia"),

    # Revisão
    path("<int:pk>/revisao/", views.revisao, name="revisao"),

    # Envio
    path("<int:pk>/enviar/", views.enviar, name="enviar"),

    # Exportar
    path("<int:pk>/exportar-pdf/", views.exportar_pdf, name="exportar_pdf"),

    # Link público (sem auth)
    path("p/<uuid:token>/", views.publico, name="publico"),
    path("p/<uuid:token>/responder/", views.publico_responder, name="publico_responder"),
]
