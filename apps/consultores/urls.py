from django.urls import path
from . import views

app_name = "consultores"

urlpatterns = [
    path("", views.listar, name="listar"),
    path("novo/", views.criar, name="criar"),
    path("<int:pk>/", views.detalhe, name="detalhe"),
    path("<int:pk>/editar/", views.editar, name="editar"),
    path("<int:pk>/excluir/", views.excluir, name="excluir"),
    # Vendedores
    path("vendedores/novo/", views.criar_vendedor, name="criar_vendedor"),
    path("vendedores/<int:pk>/editar/", views.editar_vendedor, name="editar_vendedor"),
    path("vendedores/<int:pk>/excluir/", views.excluir_vendedor, name="excluir_vendedor"),
]
