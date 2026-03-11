from django.urls import path

from . import views

app_name = "conhecimento"

urlpatterns = [
    path("", views.listar, name="listar"),
    path("criar/", views.criar, name="criar"),
    path("<slug:slug>/", views.detalhe, name="detalhe"),
    path("<slug:slug>/editar/", views.editar, name="editar"),
]
