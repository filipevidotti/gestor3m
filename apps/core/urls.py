from django.urls import path

from . import views

app_name = "core"

urlpatterns = [
    path("configuracoes/", views.configuracoes, name="configuracoes"),
    path("configuracoes/salvar/", views.configuracao_salvar, name="configuracao_salvar"),
    path("configuracoes/criar/", views.configuracao_criar, name="configuracao_criar"),
    path("configuracoes/<int:pk>/excluir/", views.configuracao_excluir, name="configuracao_excluir"),
    path("configuracoes/<int:pk>/testar/", views.configuracao_testar, name="configuracao_testar"),
]
