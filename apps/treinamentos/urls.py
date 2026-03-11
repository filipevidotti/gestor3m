from django.urls import path
from . import views

app_name = "treinamentos"

urlpatterns = [
    path("", views.listar, name="listar"),
    path("novo/", views.criar, name="criar"),
    path("<int:pk>/editar/", views.editar, name="editar"),
    path("<int:pk>/excluir/", views.excluir, name="excluir"),
    path("cliente/<int:cliente_pk>/registrar/", views.registrar_realizado, name="registrar_realizado"),
    path("realizado/<int:pk>/remover/", views.remover_realizado, name="remover_realizado"),
]
