from django.urls import path

from . import views

app_name = "core"

urlpatterns = [
    # Configurações
    path("configuracoes/", views.configuracoes, name="configuracoes"),
    path("configuracoes/salvar/", views.configuracao_salvar, name="configuracao_salvar"),
    path("configuracoes/criar/", views.configuracao_criar, name="configuracao_criar"),
    path("configuracoes/<int:pk>/excluir/", views.configuracao_excluir, name="configuracao_excluir"),
    path("configuracoes/testar/<str:categoria>/", views.configuracao_testar_categoria, name="configuracao_testar_categoria"),
    # Grupos WhatsApp
    path("grupos/", views.grupos_whatsapp, name="grupos_whatsapp"),
    path("grupos/sincronizar/", views.grupos_sincronizar, name="grupos_sincronizar"),
    path("grupos/enviar-bulk/", views.grupos_enviar_bulk, name="grupos_enviar_bulk"),
    path("grupos/<int:pk>/", views.grupo_detalhe, name="grupo_detalhe"),
    path("grupos/<int:pk>/vincular/", views.grupo_vincular, name="grupo_vincular"),
    path("grupos/<int:pk>/toggle/", views.grupo_toggle_ativo, name="grupo_toggle_ativo"),
    path("grupos/<int:pk>/enviar/", views.grupo_enviar_mensagem, name="grupo_enviar_mensagem"),
]
