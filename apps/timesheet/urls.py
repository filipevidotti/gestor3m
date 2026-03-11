from django.urls import path

from . import views

app_name = "timesheet"

urlpatterns = [
    path("", views.listar, name="listar"),
    path("criar/", views.criar, name="criar"),
    path("<int:pk>/editar/", views.editar, name="editar"),
    path("<int:pk>/excluir/", views.excluir, name="excluir"),
    path("resumo/", views.resumo, name="resumo"),
]
