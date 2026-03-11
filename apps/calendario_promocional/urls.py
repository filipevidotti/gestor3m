from django.urls import path
from . import views

app_name = "calendario_promocional"

urlpatterns = [
    path("", views.calendario, name="calendario"),
    path("nova/", views.criar_data, name="criar"),
    path("<int:pk>/", views.detalhe_data, name="detalhe"),
    path("<int:pk>/editar/", views.editar_data, name="editar"),
    path("<int:pk>/excluir/", views.excluir_data, name="excluir"),
    path("<int:pk>/preparar/<int:cliente_pk>/", views.iniciar_preparacao, name="iniciar_preparacao"),
    path("preparacao/<int:pk>/editar/", views.editar_preparacao, name="editar_preparacao"),
]
