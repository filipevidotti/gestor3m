from django.urls import path
from . import views

app_name = "planos"

urlpatterns = [
    path("cliente/<int:cliente_pk>/", views.listar, name="listar"),
    path("cliente/<int:cliente_pk>/novo/", views.criar, name="criar"),
    path("<int:pk>/", views.detalhe, name="detalhe"),
    path("<int:pk>/item/", views.adicionar_item, name="adicionar_item"),
    path("<int:pk>/item/<int:item_pk>/toggle/", views.toggle_item, name="toggle_item"),
]
