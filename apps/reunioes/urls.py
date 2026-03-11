from django.urls import path
from . import views

app_name = "reunioes"

urlpatterns = [
    path("", views.listar, name="listar"),
    path("nova/", views.criar, name="criar"),
    path("<int:pk>/editar/", views.editar, name="editar"),
    path("<int:pk>/excluir/", views.excluir, name="excluir"),

    # IA: gravação + transcrição
    path("<int:pk>/gravar/", views.gravar_reuniao, name="gravar"),
    path("<int:pk>/salvar-gravacao/", views.salvar_gravacao, name="salvar_gravacao"),
    path("<int:pk>/status-transcricao/", views.status_transcricao, name="status_transcricao"),
    path("<int:pk>/detalhe/", views.detalhe, name="detalhe"),
]
