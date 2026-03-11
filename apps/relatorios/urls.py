from django.urls import path

from . import views

app_name = "relatorios"

urlpatterns = [
    path("", views.listar, name="listar"),
    path("cliente/<int:pk>/gerar/", views.gerar, name="gerar"),
    path("<int:pk>/download/", views.download, name="download"),
    path("<int:pk>/enviar/", views.enviar, name="enviar"),
]
